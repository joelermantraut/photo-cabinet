import cv2
import os, sys
import argparse
import mediapipe as mp
import math, time, copy

from PIL import Image
from PyQt5.Qt import Qt
from datetime import datetime

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (
                                QWidget, QPushButton,
                                QLabel, QApplication,
                                QMessageBox, QLineEdit,
                                QSizePolicy, QVBoxLayout,
                                QGridLayout
                            )

CONFIG_FILENAME = ".config"
IMAGES_PER_SESSION = 3
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
MAIN_FOLDER = f"{DIRECTORY}/images"

class ConfigManager():
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

class ImageProcessor():
    def __init__(self, images_session):
        self.IMAGES_SESSION = images_session

        if not os.path.exists(MAIN_FOLDER):
            os.makedirs(MAIN_FOLDER)

    def save(self, images_list, filename):
        border_right = Image.open("data/images/right-border.jpg")
        border_bottom = Image.open("data/images/bottom-border.jpg")

        border_size = 10

        images = list()
        faces = list()

        for item in images_list:
            image, face = item
            image = Image.fromarray(image)
            images.append(image)
            faces.append(face)

        faces = max(faces)
        # Total faces in 1 image

        # TODO: Review if this is the best method to get all
        # faces in three images

        width, height = images[0].size

        total_width = width * IMAGES_PER_SESSION + border_size * (len(images) + 1)
        max_height = height + border_size * 2

        print("total_width", total_width)
        print("max_height", max_height)

        new_im_x = Image.new('RGB', (total_width, max_height), (255, 255, 255))

        x_offset = 0
        for im in images:
            new_im_x.paste(im, (x_offset, border_size))
            x_offset += width + border_size
        new_im_x.paste(border_right, (x_offset, border_size))

        new_im_y = Image.new('RGB', (total_width, max_height * faces), (255, 255, 255))

        y_offset = 0
        for im in images:
            new_im_y.paste(new_im_x, (border_size, y_offset))
            y_offset += max_height + border_size
        new_im_y.paste(border_bottom, (border_size, y_offset))

        new_im_y.show()
        new_im_y.save(filename)

class QtCapture(QWidget):
    def __init__(self, *args, fps=30, width=840, height=680):
        super(QWidget, self).__init__()

        self.fps = fps
        self.cap = cv2.VideoCapture(*args)

        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        self.frame = None
        self.close_callback = None

        self.face_detection_coeff = 0.8
        self.face_detection_fn = mp.solutions.face_detection.FaceDetection(self.face_detection_coeff)

        self.initUI()

    def initUI(self):
        self.lay = QGridLayout()
        self.setLayout(self.lay)

        self.video_frame = QLabel()
        self.lay.addWidget(self.video_frame, 1, 1)

    def setFPS(self, fps):
        self.fps = fps
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

    def getPeopleOnImage(self, frame):
        result = self.face_detection_fn.process(frame)

        if not result or (result and not result.detections):
            result = 0
        else:
            result = len(result.detections)

        return result

    def nextFrameSlot(self):
        ret, frame = self.cap.read()
        # OpenCV yields frames in BGR format
        try:
            self.frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        except cv2.error:
            self.frame = None
            return # cv2.cvtColor receive not initialized frame

        img = QtGui.QImage(
            self.frame,
            self.frame.shape[1],
            self.frame.shape[0],
            QtGui.QImage.Format_RGB888
        )
        pix = QtGui.QPixmap.fromImage(img)
        self.video_frame.setPixmap(pix)

    def start(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.nextFrameSlot)
        self.timer.start(math.ceil(1000.0 / self.fps))
        # Rounded to closest integer up calculated value

    def stop(self):
        self.timer.stop()

    def deleteLater(self):
        self.cap.release()
        super(QWidget, self).deleteLater()

    def setCloseCallback(self, callback):
        self.close_callback = callback

    def closeEvent(self, event):
        if self.close_callback:
            self.close_callback()
        event.accept()

class QtSaveContentCapture(QtCapture):
    def __init__(self, *args):
        self.phrases_list = [
            "Press SPACE to start...",
            "Another photo?",
            "Last one!!",
            "Ready!! Press SPACE again to restart..."
        ]
        # Needs to be before because initUI uses it
        # and it is called in QtCapture.__init__

        super().__init__(*args)

        self.IMAGES_SESSION = IMAGES_PER_SESSION
        self.TIME_LIMIT = 3
        # Seconds to wait for capture

        self.photos_taken = list()
        self.prev = 0
        self.cur_timer = 0
        self.timer_working = False

        self.imageProcessor = ImageProcessor(self.IMAGES_SESSION)

        self.setWindowTitle('Capture Window')

    def addLabel(self, text, fontSized):
        label = QLabel(text)
        label.setFont(QtGui.QFont('Arial', fontSized))

        return label

    def initUI(self):
        super().initUI()

        self.timer_label = self.addLabel("-", 40)
        self.bottom_label = self.addLabel(self.phrases_list[0], 10)

        self.lay.addWidget(self.timer_label, 1, 0, alignment=Qt.AlignTop)
        self.lay.addWidget(self.bottom_label, 2, 1)

    def update_timer(self):
        if self.cur_timer == 0:
            self.cur_timer = self.TIME_LIMIT
        else:
            self.cur_timer -= 1

        if self.cur_timer <= 0:
            if self.frame is not None:
                self.photos_taken.append(
                    (
                        copy.copy(self.frame),
                        self.getPeopleOnImage(self.frame)
                    )
                )
                # Tuple of image and number of faces detected on it

                self.bottom_label.setText(self.phrases_list[len(self.photos_taken)])
                # Changes bottom label text depending on number of photon taken

                if len(self.photos_taken) == self.IMAGES_SESSION:
                    datetime_string = datetime.now().strftime("%H-%M-%S")
                    img_name = f"{MAIN_FOLDER}/{datetime_string}.png"
                    self.imageProcessor.save(self.photos_taken, img_name)

                    self.photos_taken = list()
                    self.timer_timer.stop()

        self.timer_label.setText(str(self.cur_timer))

    def nextFrameSlot(self):
        super().nextFrameSlot()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            if not self.timer_working:
                self.timer_timer = QtCore.QTimer()
                self.timer_timer.timeout.connect(self.update_timer)
                self.timer_timer.start(1000)

                self.update_timer()

class QtCalibrationCapture(QtCapture):
    def __init__(self, *args):
        super().__init__(*args)

        self.face_detection_comparisons = 0
        self.FACE_DETECTION_COMPARISONS_LIMIT = self.fps * 10
        # 10 frames to calibrate

        self.bottom_label = QLabel()
        self.bottom_label.setText("Calibrating... Please wait")
        self.lay.addWidget(self.bottom_label, 2, 1)

    def setCalibrateParam(self, people):
        self.people = people
        self.face_detection_comparisons = 0

    def tuneFaceDetectionParam(self, people, people_on_image):
        if self.people > people_on_image:
            self.face_detection_coeff *= 0.9
        elif self.people < people_on_image:
            self.face_detection_coeff *= 1.1

        return self.face_detection_coeff

    def compareToCalibrate(self, frame):
        self.face_detection_comparisons += 1

        if self.face_detection_comparisons > self.FACE_DETECTION_COMPARISONS_LIMIT:
            configActions = ConfigManager()
            configActions.set("face_detection_coeff", str(self.face_detection_coeff))
            configActions.save()

            self.close()

        people_on_image = self.getPeopleOnImage(frame)

        self.face_detection_coeff = self.tuneFaceDetectionParam(self.people, people_on_image)

        self.face_detection_fn = mp.solutions.face_detection.FaceDetection(self.face_detection_coeff)
        # Updates face detection coeffs

    def nextFrameSlot(self):
        super().nextFrameSlot()

        if self.frame is not None:
            self.compareToCalibrate(self.frame)

class CalibrateWindow(QWidget):
    def __init__(self, *args):
        super(QWidget, self).__init__()

        self.people = 0

        self.calibrate_button = QPushButton('Calibrate')
        self.calibrate_button.clicked.connect(self.startCalibration)

        self.peopleLineEdit = QLineEdit()
        lay = QVBoxLayout()
        lay.addWidget(self.peopleLineEdit)
        lay.addWidget(self.calibrate_button)
        self.setLayout(lay)
        self.setGeometry(200, 200, 200, 200)
        self.setWindowTitle('Calibrate Window')
        self.show()

    def startCalibration(self):
        self.people = int(self.peopleLineEdit.text())
        if self.people != 0:
            self.capture = QtCalibrationCapture(0)
            self.capture.setCloseCallback(self.close)
            # When capture closes, close this window
            self.capture.setFPS(30)
            self.capture.setParent(self)
            self.capture.setWindowFlags(QtCore.Qt.Tool)
            self.capture.setCalibrateParam(self.people)

            self.capture.start()
            self.capture.show()

class ControlWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.capture = None
        self.pause = False
        self.calibrateWindow = None

        self.initUI()

        self.setWindowTitle('Control Panel')
        # self.showFullScreen()
        self.showMaximized()

    def addButton(self, text, callback=None):
        button = QPushButton(text)
        button.setFont(QtGui.QFont('Arial', 15))
        button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        if callback:
            button.clicked.connect(callback)

        return button

    def addLabel(self, text, fontSize):
        label = QLabel(text)
        label.setFont(QtGui.QFont('Arial', fontSize))

        return label

    def initUI(self):
        self.title = self.addLabel("Photo Cabinet", 25)

        self.start_button = self.addButton("Start", self.startCapture)
        self.end_button = self.addButton("Pause/Continue")
        self.quit_button = self.addButton("End", self.endCapture)
        self.calibrate_button = self.addButton("Calibrate", self.calibrate)

        gbox = QGridLayout(self)

        gbox.addWidget(self.title, 0, 0)
        gbox.addWidget(self.start_button, 1, 0)
        gbox.addWidget(self.calibrate_button, 1, 1)
        gbox.addWidget(self.end_button, 2, 0)
        gbox.addWidget(self.quit_button, 2, 1)

        self.setLayout(gbox)

    def calibrate(self):
        self.calibrateWindow = CalibrateWindow()
        self.calibrateWindow.show()

    def startCapture(self):
        if not self.capture:
            self.capture = QtSaveContentCapture(0)
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

class ArgParsing():
    def __init__(self):
        self.ap = None
        self.set()

    def set(self):
        self.ap = argparse.ArgumentParser()
        self.ap.add_argument("-c", "--config", required=False, help="Sets config file name and path")
        self.ap.add_argument("-m", "--main", required=False, help="Sets images folder path")
        self.ap.add_argument("-i", "--images", required=False, help="Sets number of images per session")

    def get(self):
        return vars(self.ap.parse_args())

def main():
    global CONFIG_FILENAME, MAIN_FOLDER, IMAGES_PER_SESSION

    argparsing = ArgParsing()
    args = argparsing.get()

    if args["config"]:
        CONFIG_FILENAME = args["config"]
    if args["main"]:
        MAIN_FOLDER = args["main"]
    if args["images"]:
        IMAGES_PER_SESSION = args["images"]

    app = QApplication(sys.argv)
    control_window = ControlWindow()

    sys.exit(app.exec_())

main()