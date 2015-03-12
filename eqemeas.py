import sys
from PyQt4 import QtGui, uic
import numpy as np


class Eqe(QtGui.QMainWindow):
    def __init__(self):
        super(Eqe, self).__init__()
        uic.loadUi('eqe_gui.ui', self)
        validator = QtGui.QDoubleValidator()

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

        self.start_button.clicked.connect(self.runMeasure)
        self.lines, = self.main_plot.axes.plot([],[], 'o-')
        self.main_plot.axes.set_xlabel('Wavelength [nm]')
        self.main_plot.axes.set_ylabel('EQE')
        #Autoscale on unknown axis and known lims on the other
        self.main_plot.axes.set_autoscale_on(True)
        self.show()

    def runMeasure(self):
        lstart = float(self.wavelength_start.text())
        lstep = float(self.wavelength_step.text())
        lstop = float(self.wavelength_end.text())
        self.lam = np.arange(lstart, lstop+lstep, lstep)
        self.updatePlot(np.arange(self.lam.size), self.lam)
        print(self.lam)
        filters, ok = FilterViewer.getFilters()
        print(filters)

    def updatePlot(self, newx, newy):
        #Update data (with the new _and_ the old points)
        self.lines.set_xdata(np.append(self.lines.get_xdata(), newx))
        self.lines.set_ydata(np.append(self.lines.get_ydata(), newy))
        #Need both of these in order to rescale
        self.main_plot.axes.relim()
        self.main_plot.axes.autoscale_view()
        #We need to draw *and* flush
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
            color = '#c4df9b' # green
        elif state == QtGui.QValidator.Intermediate:
            color = '#fff79a' # yellow
        else:
            color = '#f6989d' # red
        sender.setStyleSheet('QLineEdit { background-color: %s }' % color)


class FilterViewer(QtGui.QDialog):
    def __init__(self, parent=None):
        super(FilterViewer, self).__init__()
        uic.loadUi('filter_view.ui', self)
        self.btn_add.clicked.connect(self.addFilter)
        self.btn_rem.clicked.connect(self.remFilter)
        self.set_avalible_filters(['550', '695', '830'])

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
        return [x.text() for x in [self.usedFilters.item(y) for y in range(len(self.usedFilters))]]

    @staticmethod
    def getFilters(parent = None):
        dialog = FilterViewer(parent)
        result = dialog.exec_()
        filters = dialog.filters()
        return (filters, result == QtGui.QDialog.Accepted)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    win = Eqe()
    sys.exit(app.exec_())
