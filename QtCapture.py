import cv2
import math, copy
import mediapipe as mp
from datetime import datetime

from PyQt5.Qt import Qt
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (
                                QWidget, QPushButton,
                                QLabel, QLineEdit,
                                QGridLayout, QSizePolicy
                            )

from ConfigManager import ConfigManager
from ImageProcessor import ImageProcessor

from globals import RESOLUTION_X, RESOLUTION_Y, IMAGES_PER_SESSION, MAIN_FOLDER, FONT_DEFAULT

class QtCapture(QWidget):
    def __init__(self, *args, fps=30, width=RESOLUTION_X, height=RESOLUTION_Y):
        super(QWidget, self).__init__()

        if len(args) == 0:
            configActions = ConfigManager()
            capture_index = int(configActions.get("camera_index"))

            args = (capture_index, )

        self.cap = cv2.VideoCapture(*args, cv2.CAP_DSHOW)
        # https://stackoverflow.com/questions/19448078/python-opencv-access-webcam-maximum-resolution

        self.fps = fps
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

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

    def showFrame(self, frame):
        img = QtGui.QImage(
            self.frame,
            self.frame.shape[1],
            self.frame.shape[0],
            QtGui.QImage.Format_RGB888
        )
        pix = QtGui.QPixmap.fromImage(img)
        self.video_frame.setPixmap(pix)

    def nextFrameSlot(self):
        _, frame = self.cap.read()
        # OpenCV yields frames in BGR format
        try:
            self.frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        except cv2.error:
            self.frame = None
            return # cv2.cvtColor receive not initialized frame

        self.showFrame(self.frame)

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
            "Presiona ESPACIO para comenzar...",
            "Otra foto?",
            "Ultima!!!",
            "Listo!!! Presiona ESPACIO para comenzar nuevamente..."
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

        self.imageProcessor = ImageProcessor()

        self.setWindowTitle('Centro Ágape Cristiano')

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

        self.calibrating = False

    def addButton(self, text, callback=None):
        button = QPushButton(text)
        button.setFont(QtGui.QFont(*FONT_DEFAULT))
        button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        if callback:
            button.clicked.connect(callback)

        return button

    def initUI(self):
        super().initUI()

        self.bottom_label = QLabel()
        self.placeholder_label = QLabel("Numero de personas en la imagen:")

        self.peopleLineEdit = QLineEdit()
        self.peopleLineEdit.setAlignment(QtCore.Qt.AlignCenter)

        self.calibrate_button = self.addButton("Calibrar", self.startCalibration)

        self.lay.addWidget(self.placeholder_label, 2, 1)
        self.lay.addWidget(self.peopleLineEdit, 3, 1)
        self.lay.addWidget(self.calibrate_button, 4, 1)
        self.lay.addWidget(self.bottom_label, 5, 1)

    def startCalibration(self):
        self.people = int(self.peopleLineEdit.text())
        if self.people != 0:
            self.calibrating = True
            self.bottom_label.setText("Calibrando... Por favor, espera")

    def setCalibrateParam(self, people):
        self.people = people
        self.face_detection_comparisons = 0

    def getPeopleOnImage(self, frame):
        results = self.face_detection_fn.process(frame)
        mp_drawing = mp.solutions.drawing_utils

        if not results.detections:
          return None, 0

        for detection in results.detections:
            mp_drawing.draw_detection(frame, detection)
            # Draws rectangles for each detection

        return frame, len(results.detections)

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

        frame, people_on_image = self.getPeopleOnImage(frame)

        if frame is None or people_on_image == 0:
            return

        super().showFrame(frame)

        self.face_detection_coeff = self.tuneFaceDetectionParam(self.people, people_on_image)

        self.face_detection_fn = mp.solutions.face_detection.FaceDetection(self.face_detection_coeff)
        # Updates face detection coeffs

    def nextFrameSlot(self):
        super().nextFrameSlot()

        if self.calibrating and self.frame is not None:
            self.compareToCalibrate(self.frame)

class QtSelectCameraCapture(QtCapture):
    def __init__(self, *args):
        super().__init__(*args)

        self.current_camera = 0
        self.LIMIT_SEARCH = 10
        # Camera index to stop searching

    def addButton(self, text, callback=None):
        button = QPushButton(text)
        button.setFont(QtGui.QFont(*FONT_DEFAULT))
        button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        if callback:
            button.clicked.connect(callback)

        return button

    def initUI(self):
        super().initUI()

        self.change_camera_button = self.addButton("Siguiente cámara", self.next_camera)
        self.save_and_exit_button = self.addButton("Guardar y salir", self.save_and_exit)
        self.lay.addWidget(self.change_camera_button, 2, 1)
        self.lay.addWidget(self.save_and_exit_button, 3, 1)

    def next_camera(self):
        is_working = False
        while not is_working and self.current_camera <= 10:
            self.cap = cv2.VideoCapture(self.current_camera)
            if self.cap.isOpened():
                is_working = True
            self.current_camera += 1

        if self.current_camera >= 10:
            self.current_camera = 0

    def save_and_exit(self):
        configActions = ConfigManager()
        configActions.set("camera_index", str(self.current_camera))
        configActions.save()

        self.close()