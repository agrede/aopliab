import sys
from PyQt4 import QtGui, uic
import numpy as np
import eqe
import visa
from aopliab_common import json_write


class EqeUi(QtGui.QMainWindow):
    def __init__(self):
        super(EqeUi, self).__init__()
        uic.loadUi('eqe_gui.ui', self)
        validator = QtGui.QDoubleValidator()
        self.rm = visa.ResourceManager()

        # TransImp Amplifier
        self.tia = None
        self.tia_enable.stateChanged.connect(self.enableTia)
        self.sens_value.editingFinished.connect(self.setTiaSens)
        self.sens_value.setValidator(validator)
        self.sens_value.textChanged.connect(self.check_state)
        self.sens_value.textChanged.emit(self.sens_value.text())
        self.cur_value.editingFinished.connect(self.setTiaCur)
        self.cur_value.setValidator(validator)
        self.cur_value.textChanged.connect(self.check_state)
        self.cur_value.textChanged.emit(self.cur_value.text())
        self.volt_value.editingFinished.connect(self.setTiaVolt)
        self.volt_value.setValidator(validator)
        self.volt_value.textChanged.connect(self.check_state)
        self.volt_value.textChanged.emit(self.volt_value.text())
        self.cur_enable.stateChanged.connect(self.enableTiaCur)
        self.volt_enable.stateChanged.connect(self.enableTiaVolt)

        # Lock-in Amp
        self.lia = eqe.get_lia(self.rm)

        # Wavelengths
        self.mon = eqe.get_mono(self.rm)
        self.wavelength_start.setValidator(validator)
        self.wavelength_start.textChanged.connect(self.check_state)
        self.wavelength_start.textChanged.emit(
            self.wavelength_start.text())

        self.wavelength_step.setValidator(validator)
        self.wavelength_step.textChanged.connect(self.check_state)
        self.wavelength_step.textChanged.emit(
            self.wavelength_step.text())

        self.wavelength_end.setValidator(validator)
        self.wavelength_end.textChanged.connect(self.check_state)
        self.wavelength_end.textChanged.emit(
            self.wavelength_end.text())

        # Filter Init
        self.filters_aval = eqe.get_filters()
        self.filters_curr = []
        self.filter_button.clicked.connect(self.setFilters)

        self.start_button.clicked.connect(self.runMeasure)
        self.lines, = self.main_plot.axes.plot([], [], 'o-')
        self.main_plot.axes.set_xlabel('Wavelength [nm]')
        self.main_plot.axes.set_ylabel('EQE')
        # Autoscale on unknown axis and known lims on the other
        self.main_plot.axes.set_autoscale_on(True)
        self.show()

    def runMeasure(self):
        lstart = float(self.wavelength_start.text())
        lstep = float(self.wavelength_step.text())
        lstop = float(self.wavelength_end.text())
        lam = eqe.brk_wavelength(lstart, lstop, lstep, self.filters_curr)

        meas = {}
        meas['settings'] = {}
        meas['settings']['dwell'] = np.zeros(len(lam))
        meas['settings']['lia_tc'] = np.zeros(len(lam))
        meas['settings']['lia_sens'] = np.zeros(len(lam))
        meas['settings']['wavelength'] = lam
        N = 1
        meas['cur'] = np.array([np.zeros((x.size, N)) for x in lam])
        meas['phas'] = np.array([np.zeros((x.size, N)) for x in lam])
        if (self.tia is not None):
            meas['volt'] = np.array([np.zeros((x.size, N)) for x in lam])
            meas['settings']['tia_sens'] = np.zeros(len(lam))
            meas['settings']['tia_volt'] = np.zeros(len(lam))
            meas['settings']['tia_cur'] = np.zeros(len(lam))
        for k, l in enumerate(lam):
            dwell = 8*self.lia.filter_time_constant
            if (self.tia is not None):
                if (self.tia.curr_output):
                    meas['settings']['tia_cur'][k] = self.tia.bias_curr
                if (self.tia.volt_output):
                    meas['settings']['tia_volt'][k] = self.tia.bias_volt
                meas['settings']['tia_sens'][k] = self.tia.sensitivity
            meas['settings']['lia_sens'][k] = self.lia.sensitivity
            meas['settings']['lia_tc'][k] = self.lia.filter_time_constant
            meas['settings']['dwell'][k] = dwell
            res = eqe.measureResponse(l, self.mon, self.lia, dwell, N=1,
                                      tia=self.tia, plot=self.updatePlot)
            meas = eqe.merge_meas(meas, res, k)
        fileName = QtGui.QFileDialog.getSaveFileName(
            self, 'Save Measurement', '')
        json_write(meas, fileName)
        self.meas = meas

    def updatePlot(self, newx, newy):
        # Update data (with the new _and_ the old points)
        self.lines.set_xdata(np.append(self.lines.get_xdata(), newx))
        self.lines.set_ydata(np.append(self.lines.get_ydata(), newy))
        # Need both of these in order to rescale
        self.main_plot.axes.relim()
        self.main_plot.axes.autoscale_view()
        # We need to draw *and* flush
        self.main_plot.figure.canvas.draw()
        self.main_plot.figure.canvas.flush_events()

    def clearPlot(self):
        self.lines.set_xdata([])
        self.lines.set_ydata([])
        self.main_plot.axes.relim()
        self.main_plot.axes.autoscale_view()
        self.main_plot.figure.canvas.draw()
        self.main_plot.figure.canvas.flush_events()

    def check_state(self, *args, **kwargs):
        sender = self.sender()
        validator = sender.validator()
        state = validator.validate(sender.text(), 0)[0]
        if state == QtGui.QValidator.Acceptable:
            color = '#c4df9b'  # green
        elif state == QtGui.QValidator.Intermediate:
            color = '#fff79a'  # yellow
        else:
            color = '#f6989d'  # red
        sender.setStyleSheet('QLineEdit { background-color: %s }' % color)

    def setFilters(self):
        tafilt = ["%d" % x for x in self.filters_aval]
        tcfilt = ["%d" % x for x in self.filters_curr]
        afilt, cfilt, ok = FilterViewer.getFilters(tafilt, tcfilt)
        if (ok):
            self.filters_aval = [int(x) for x in afilt]
            self.filters_curr = [int(x) for x in cfilt]

    def enableTia(self):
        if (self.tia_enable.isChecked()):
            self.tia = eqe.get_tia(self.rm)
            self.tia_lsens.setEnabled(True)
            self.sens_value.setEnabled(True)
            self.sens_value.setText("%0.e" % self.tia.sensitivity)
            self.cur_value.setEnabled(True)
            self.volt_value.setEnabled(True)
            self.cur_enable.setEnabled(True)
            self.volt_enable.setEnabled(True)
            self.cur_enable.setChecked(False)
            self.volt_enable.setChecked(False)
            self.cur_value.setText("%0.e" % self.tia.bias_curr)
            self.volt_value.setText("%0.e" % self.tia.bias_volt)
        else:
            self.tia.inst.close()
            self.tia = None

    def setTiaSens(self):
        if (self.tia is not None):
            if (self.sens_value.hasAcceptableInput()):
                self.tia.sensitivity = float(self.sens_value.text())
            self.sens_value.setText("%0.e" % self.tia.sensitivity)

    def setTiaVolt(self):
        if (self.tia is not None):
            if (self.volt_value.hasAcceptableInput()):
                self.tia.bias_volt = float(self.volt_value.text())
            self.volt_value.setText("%0.e" % self.tia.bias_volt)

    def setTiaCur(self):
        if (self.tia is not None):
            if (self.cur_value.hasAcceptableInput()):
                self.tia.bias_curr = float(self.cur_value.text())
            self.cur_value.setText("%0.e" % self.tia.bias_curr)

    def enableTiaVolt(self):
        if (self.tia is not None):
            self.tia.volt_output = self.volt_enable.isChecked()

    def enableTiaCur(self):
        if (self.tia is not None):
            self.tia.cur_output = self.cur_enable.isChecked()


class FilterViewer(QtGui.QDialog):
    def __init__(self, afilt, cfilt, parent=None):
        super(FilterViewer, self).__init__()
        uic.loadUi('filter_view.ui', self)
        self.btn_add.clicked.connect(self.addFilter)
        self.btn_rem.clicked.connect(self.remFilter)
        self.set_avalible_filters(afilt)
        self.set_current_filters(cfilt)

    def set_avalible_filters(self, filters):
        self.avalibleFilters.clear()
        self.avalibleFilters.addItems(filters)
        self.avalibleFilters.sortItems()

    def set_current_filters(self, filters):
        self.usedFilters.clear()
        self.usedFilters.addItems(filters)
        self.usedFilters.sortItems()

    def addFilter(self):
        for itm in self.avalibleFilters.selectedItems():
            self.usedFilters.addItem(itm.text())
            self.avalibleFilters.takeItem(self.avalibleFilters.row(itm))
        self.usedFilters.sortItems()
        self.avalibleFilters.sortItems()

    def remFilter(self):
        for itm in self.usedFilters.selectedItems():
            self.avalibleFilters.addItem(itm.text())
            self.usedFilters.takeItem(self.usedFilters.row(itm))
        self.usedFilters.sortItems()
        self.avalibleFilters.sortItems()

    def filters(self):
        return (
            [x.text() for x in [
                self.avalibleFilters.item(y) for y in range(
                    len(self.avalibleFilters))]],
            [x.text() for x in [
                self.usedFilters.item(y) for y in range(
                    len(self.usedFilters))]])

    @staticmethod
    def getFilters(afilt, cfilt, parent=None):
        dialog = FilterViewer(afilt, cfilt, parent=parent)
        result = dialog.exec_()
        (afilt, cfilt) = dialog.filters()
        return (afilt, cfilt, result == QtGui.QDialog.Accepted)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    win = EqeUi()
    sys.exit(app.exec_())
