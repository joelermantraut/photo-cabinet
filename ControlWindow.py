import os
from fpdf import FPDF
from PIL import Image

from PyQt5.Qt import Qt
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (
                                QWidget, QPushButton,
                                QMessageBox, QFileDialog,
                                QSizePolicy, QVBoxLayout,
                                QLabel
                            )
from PyQt5.QtGui import QPixmap

from globals import *
from QtCapture import QtSaveContentCapture, QtCalibrationCapture, QtSelectCameraCapture
from ConfigManager import ConfigWindow
from update import Update

class ControlWindow(QWidget):
    def __init__(self, WINDOW_WIDTH, WINDOW_HEIGHT):
        QWidget.__init__(self)
        self.capture = None
        self.calibrateWindow = None

        self.initUI()

        self.setWindowTitle('Panel de Control')
        self.setGeometry(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.show()

    def addButton(self, text, callback=None):
        button = QPushButton(text)
        button.setFont(QtGui.QFont(*FONT_DEFAULT))
        button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        if callback:
            button.clicked.connect(callback)

        return button

    def addLabel(self, text, fontSize):
        label = QLabel(text)
        label.setFont(QtGui.QFont('Arial', fontSize))
        label.setAlignment(Qt.AlignCenter)

        return label
    
    def showMessage(self, title, text, options=None):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setWindowTitle(title)
        msgBox.setText(text)

        if options is None:
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        else:
            msgBox.setStandardButtons(options[0] | options[1])

        return msgBox.exec()

    def initUI(self):
        self.icon = self.addLabel("", 25)
        pixmap = QPixmap('data/images/icono.png')
        self.icon.setPixmap(pixmap)

        self.title = self.addLabel("Centro Ágape Cristiano", 25)

        self.start_button = self.addButton("Capturar", self.startCapture)
        self.calibrate_button = self.addButton("Calibrar", self.calibrate)
        self.select_camera_button = self.addButton("Seleccionar cámara", self.select_camera)
        self.open_config_button = self.addButton("Abrir configuración", self.open_config)
        self.open_explorer_button = self.addButton("Abrir carpeta de imágenes", self.open_explorer)
        self.prepare_to_print_button = self.addButton("Preparar para imprimir", self.prepare_to_print)
        self.update_button = self.addButton("Actualizar", self.update)
        self.quit_button = self.addButton("Salir", self.endCapture)

        vbox = QVBoxLayout(self)
        self.setLayout(vbox)

        vbox.addWidget(self.icon)
        vbox.addWidget(self.title)
        vbox.addWidget(self.start_button)
        vbox.addWidget(self.calibrate_button)
        vbox.addWidget(self.select_camera_button)
        vbox.addWidget(self.open_config_button)
        vbox.addWidget(self.open_explorer_button)
        vbox.addWidget(self.prepare_to_print_button)
        vbox.addWidget(self.update_button)
        vbox.addWidget(self.quit_button)

    def calibrate(self):
        if not self.capture:
            self.capture = QtCalibrationCapture()
            self.capture.setCloseCallback(self.captureQuitHandler)
            self.capture.setParent(self)
            self.capture.setWindowFlags(QtCore.Qt.Tool)

        self.capture.start()
        self.capture.show()

    def open_explorer(self):
        os.system(f"start {MAIN_FOLDER}")

    def prepare_to_print(self):
        fnames = QFileDialog.getOpenFileNames(self, 'Seleccionar archivos', 
           MAIN_FOLDER, "Image files (*.jpg *.png *.jpeg)")

        folder_name = QFileDialog.getExistingDirectory(self, 'Seleccionar directorio')
        # Files to print and folder to save PDF

        if len(fnames[0]) == 2 or len(folder_name) == 0:
            return
        # Case of cancelled selection

        files_to_print = fnames[0]

        pdf_path = f"{folder_name}/{FILE_SAVE_NAME}.pdf"

        pdf = FPDF("P", "pt")
        pdf.add_page()

        actual_height = 0
        for image in files_to_print:
            PILImage = Image.open(image)
            width, height = PILImage.size
            real_height = height * (A4_SIZE["width"] / PT_MM_RELATION) / width
            if (actual_height + real_height) > A4_SIZE["height"] / PT_MM_RELATION:
                pdf.add_page()
                actual_height = 0

            pdf.image(image, 0, actual_height, A4_SIZE["width"] / PT_MM_RELATION)
            actual_height += real_height + 10

        pdf.output(pdf_path, "F")

        # https://stackoverflow.com/questions/27327513/create-pdf-from-a-list-of-images
        
    def open_config(self):
        self.configWindow = ConfigWindow()
        self.configWindow.show()

    def update(self):
        local_directory = "."
        # Current directory

        response = self.showMessage("Actualizacion", "Actualizacion. Por favor, no cierre el programa.")

        if response == QMessageBox.Cancel:
            return

        updater = Update()
        result = updater.update_software(REPOSITORY_URL, local_directory)

        if result == 0:
            _ = self.showMessage("Actualizacion", "El programa ya esta actualizado.")
        elif result == 1:
            _ = self.showMessage("Actualizacion", "El programa fue actualizado correctamente.")
        elif result == -1:
            _ = self.showMessage("Actualizacion", "No se ha podido actualizar. Consulte al servicio técnico.")
        else:
            raise Exception("Something went wrong")

    def select_camera(self):
        if not self.capture:
            self.capture = QtSelectCameraCapture()
            self.capture.setCloseCallback(self.captureQuitHandler)
            self.capture.setParent(self)
            self.capture.setWindowFlags(QtCore.Qt.Tool)

        self.capture.start()
        self.capture.show()

    def startCapture(self):
        if not self.capture:
            self.capture = QtSaveContentCapture()
            self.capture.setCloseCallback(self.captureQuitHandler)
            self.capture.setParent(self)
            self.capture.setWindowFlags(QtCore.Qt.Tool)

        self.capture.start()
        self.capture.showMaximized()

    def endCapture(self):
        if self.capture:
            self.capture.deleteLater()
            self.capture = None
        self.close_window()

    def captureQuitHandler(self):
        self.capture = None

    def close_window(self):
        self.close()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Cerrar programa', 'Está seguro que quiere salir?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()