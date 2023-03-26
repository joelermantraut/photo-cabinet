from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QMessageBox, QLineEdit
import sys
import cv2
from PIL import Image
import math
import mediapipe as mp

CONFIG_FILENAME = ".config"

class configManager():
    def __init__(self):
        self.config_dict = dict()

    def parse_config_file(self):
        with open(CONFIG_FILENAME, "r") as file:
            file_content = self.config_file.read()
        
        lines = file_content.split("\n")
        for line in lines:
            param, value = line.split(",")
            self.config_dict[param] = value

    def set(self, param, value):
        self.config_dict[param] = value

    def get(self, param):
        return self.config_dict[param]

    def save(self):
        file_content = ""
        for key, value in self.config_dict.items():
            file_content += f"{key},{value}\n"

        file_content = file_content[:-1]
        # Deletes last \n to not generate other item on parsing

        with open(CONFIG_FILENAME, "w") as file:
            file.write(file_content)

class QtCapture(QtWidgets.QWidget):
    def __init__(self, *args):
        super(QtWidgets.QWidget, self).__init__()

        self.fps = 24
        self.cap = cv2.VideoCapture(*args)
        self.calibrate = 0
        # 0: Normal capture mode
        # 1: Calibrate mode
        self.face_detection_coeff = 0.8
        self.close_callback = None
        self.face_detection_comparisons = 0
        self.FACE_DETECTION_COMPARISONS_LIMIT = 100

        self.face_detection_fn = mp.solutions.face_detection.FaceDetection(self.face_detection_coeff)

        self.video_frame = QtWidgets.QLabel()
        lay = QtWidgets.QVBoxLayout()
        lay.addWidget(self.video_frame)
        self.setLayout(lay)
        self.setWindowTitle('Capture Window')

    def setFPS(self, fps):
        self.fps = fps

    # CALIBRATION METHODS

    def setCalibrateParam(self, people):
        self.people = people
        self.calibrate = True
        self.face_detection_comparisons = 0

    def compareToCalibrate(self, frame):
        self.face_detection_comparisons += 1

        if self.face_detection_comparisons > self.FACE_DETECTION_COMPARISONS_LIMIT:
            self.calibrate = False

            configActions = configManager()
            configActions.set("face_detection_coeff", str(self.face_detection_coeff))
            configActions.save()

            self.close()

        people_on_image = self.getPeopleOnImage(frame)

        if self.people > people_on_image:
            self.face_detection_coeff *= 0.9
        elif self.people < people_on_image:
            self.face_detection_coeff *= 1.1
        else:
            return
            # coeff is ok, not modify it

        self.face_detection_fn = mp.solutions.face_detection.FaceDetection(self.face_detection_coeff)
        # Updates face detection coeffs

    def getPeopleOnImage(self, frame):
        imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.face_detection_fn.process(imgRGB)

        if not result or (result and not result.detections):
            result = 0
        else:
            result = len(result.detections)

        return result

    # CALIBRATION METHODS

    def nextFrameSlot(self):
        ret, frame = self.cap.read()
        # OpenCV yields frames in BGR format
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = QtGui.QImage(frame, frame.shape[1], frame.shape[0], QtGui.QImage.Format_RGB888)
        pix = QtGui.QPixmap.fromImage(img)
        self.video_frame.setPixmap(pix)

        if self.calibrate:
            self.compareToCalibrate(frame)

    def start(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.nextFrameSlot)
        self.timer.start(math.ceil(1000.0 / self.fps))
        # Rounded to closest integer up calculated value

    def stop(self):
        self.timer.stop()

    def deleteLater(self):
        self.cap.release()
        super(QtWidgets.QWidget, self).deleteLater()

    def setCloseCallback(self, callback):
        self.close_callback = callback

    def closeEvent(self, event):
        if self.close_callback:
            self.close_callback()
        event.accept()

class CalibrateWindow(QtWidgets.QWidget):
    def __init__(self, *args):
        super(QtWidgets.QWidget, self).__init__()

        self.people = 0

        self.calibrate_button = QtWidgets.QPushButton('Calibrate')
        self.calibrate_button.clicked.connect(self.startCalibration)

        self.peopleLineEdit = QtWidgets.QLineEdit()
        lay = QtWidgets.QVBoxLayout()
        lay.addWidget(self.peopleLineEdit)
        lay.addWidget(self.calibrate_button)
        self.setLayout(lay)
        # self.setGeometry(200, 200, 200, 200)
        self.setWindowTitle('Calibrate Window')
        self.show()

    def startCalibration(self):
        self.people = int(self.peopleLineEdit.text())
        if self.people != 0:
            self.capture = QtCapture(0)
            self.capture.setCloseCallback(self.close)
            # When capture closes, close this window
            self.capture.setFPS(30)
            self.capture.setParent(self)
            self.capture.setWindowFlags(QtCore.Qt.Tool)
            self.capture.setCalibrateParam(self.people)

            self.capture.start()
            self.capture.show()

class ControlWindow(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.capture = None
        self.pause = False
        self.calibrateWindow = None

        self.start_button = QtWidgets.QPushButton('Start')
        self.start_button.clicked.connect(self.startCapture)

        self.end_button = QtWidgets.QPushButton('Pause/Continue')

        self.quit_button = QtWidgets.QPushButton('End')
        self.quit_button.clicked.connect(self.endCapture)

        self.calibrate_button = QtWidgets.QPushButton("Calibrate")
        self.calibrate_button.clicked.connect(self.calibrate)

        vbox = QtWidgets.QVBoxLayout(self)
        vbox.addWidget(self.start_button)
        vbox.addWidget(self.calibrate_button)
        vbox.addWidget(self.end_button)
        vbox.addWidget(self.quit_button)
        self.setLayout(vbox)
        self.setWindowTitle('Control Panel')
        # self.showFullScreen()
        self.showMaximized()

    def calibrate(self):
        self.calibrateWindow = CalibrateWindow()
        self.calibrateWindow.show()

    def startCapture(self):
        if not self.capture:
            self.capture = QtCapture(0)
            self.capture.setCloseCallback(self.captureQuitHandler)
            self.end_button.clicked.connect(self.pause_continue)
            self.capture.setFPS(30)
            self.capture.setParent(self)
            self.capture.setWindowFlags(QtCore.Qt.Tool)
        self.capture.start()
        self.capture.show()

    def pause_continue(self):
        if self.capture and self.pause:
            self.capture.start()
        elif self.capture and not self.pause:
            self.capture.stop()
        else:
            return
            # Capture not created

        self.pause = not self.pause

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
        # reply = QMessageBox.question(self, 'Window Close', 'Are you sure you want to close the window?',
        #         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        # if reply == QMessageBox.Yes:
        #     event.accept()
        # else:
        #     event.ignore()
        event.accept()

def main():
    global globalCapture

    app = QApplication(sys.argv)
    control_window = ControlWindow()

    sys.exit(app.exec_())

main()