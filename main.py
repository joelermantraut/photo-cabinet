from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication
import sys
import cv2
from PIL import Image
import math

class QtCapture(QtWidgets.QWidget):
    def __init__(self, *args):
        super(QtWidgets.QWidget, self).__init__()

        self.fps = 24
        self.cap = cv2.VideoCapture(*args)

        self.video_frame = QtWidgets.QLabel()
        lay = QtWidgets.QVBoxLayout()
        # lay.setMargin(0)
        lay.addWidget(self.video_frame)
        self.setLayout(lay)

    def setFPS(self, fps):
        self.fps = fps

    def nextFrameSlot(self):
        ret, frame = self.cap.read()
        # OpenCV yields frames in BGR format
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = QtGui.QImage(frame, frame.shape[1], frame.shape[0], QtGui.QImage.Format_RGB888)
        pix = QtGui.QPixmap.fromImage(img)
        self.video_frame.setPixmap(pix)

    def start(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.nextFrameSlot)
        self.timer.start(math.ceil(1000.0 / self.fps))

    def stop(self):
        self.timer.stop()

    def deleteLater(self):
        self.cap.release()
        super(QtWidgets.QWidget, self).deleteLater()

class ControlWindow(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.capture = None

        self.start_button = QtWidgets.QPushButton('Start')
        self.start_button.clicked.connect(self.startCapture)
        self.quit_button = QtWidgets.QPushButton('End')
        self.quit_button.clicked.connect(self.endCapture)
        self.end_button = QtWidgets.QPushButton('Stop')

        vbox = QtWidgets.QVBoxLayout(self)
        vbox.addWidget(self.start_button)
        vbox.addWidget(self.end_button)
        vbox.addWidget(self.quit_button)
        self.setLayout(vbox)
        self.setWindowTitle('Control Panel')
        self.setGeometry(100,100,200,200)
        self.show()

    def startCapture(self):
        if not self.capture:
            self.capture = QtCapture(0)
            self.end_button.clicked.connect(self.capture.stop)
            self.capture.setFPS(30)
            self.capture.setParent(self)
            self.capture.setWindowFlags(QtCore.Qt.Tool)
        self.capture.start()
        self.capture.show()

    def endCapture(self):
        self.capture.deleteLater()
        self.capture = None

def main():
    app = QApplication(sys.argv)
    control_window = ControlWindow()
    sys.exit(app.exec_())

main()