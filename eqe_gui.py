# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'eqe_gui.ui'
#
# Created: Fri Mar  6 14:12:16 2015
#      by: PyQt4 UI code generator 4.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(800, 600)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.main_plot = MatplotlibWidget(self.centralwidget)
        self.main_plot.setGeometry(QtCore.QRect(189, 20, 601, 521))
        self.main_plot.setObjectName(_fromUtf8("main_plot"))
        self.widget = QtGui.QWidget(self.centralwidget)
        self.widget.setGeometry(QtCore.QRect(10, 322, 174, 123))
        self.widget.setObjectName(_fromUtf8("widget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.widget)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label = QtGui.QLabel(self.widget)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.wavelength_start = QtGui.QLineEdit(self.widget)
        self.wavelength_start.setObjectName(_fromUtf8("wavelength_start"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.wavelength_start)
        self.label_2 = QtGui.QLabel(self.widget)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_2)
        self.wavelength_end = QtGui.QLineEdit(self.widget)
        self.wavelength_end.setObjectName(_fromUtf8("wavelength_end"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.wavelength_end)
        self.label_3 = QtGui.QLabel(self.widget)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.label_3)
        self.wavelength_step = QtGui.QLineEdit(self.widget)
        self.wavelength_step.setObjectName(_fromUtf8("wavelength_step"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.wavelength_step)
        self.verticalLayout.addLayout(self.formLayout)
        self.start_button = QtGui.QCommandLinkButton(self.widget)
        self.start_button.setObjectName(_fromUtf8("start_button"))
        self.verticalLayout.addWidget(self.start_button)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.label.setText(_translate("MainWindow", "Start", None))
        self.label_2.setText(_translate("MainWindow", "Stop", None))
        self.label_3.setText(_translate("MainWindow", "Step", None))
        self.start_button.setText(_translate("MainWindow", "Run", None))

from matplotlibwidget import MatplotlibWidget
