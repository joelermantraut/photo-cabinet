import cv2
import os, sys
import argparse
import mediapipe as mp
import math, copy

from PIL import Image
from PyQt5.Qt import Qt
from datetime import datetime

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (
                                QWidget, QPushButton,
                                QLabel, QApplication,
                                QMessageBox, QLineEdit,
                                QGridLayout, QFileDialog,
                                QSizePolicy
                            )

IMAGES_PER_SESSION = 3
DIRECTORY = f"{os.path.expanduser('~')}/photo-cabinet"
MAIN_FOLDER = f"{DIRECTORY}/images"
CONFIG_FILENAME = ".config"
CONFIG_FILEPATH = f"{DIRECTORY}/{CONFIG_FILENAME}"

# TODO: Divide file in multiple files.

class ConfigManager():
    def __init__(self):
        self.config_dict = dict()

        if not os.path.exists(DIRECTORY):
            os.mkdir(DIRECTORY)
            self.create_config_file()
        else:
            try:
                self.parse_config_file()
            except:
                self.create_config_file()
                self.parse_config_file()

    def create_config_file(self):
        self.config_dict = {
            "face_detection_coeff": "0.8",
            "camera_index": "0",
            "images_session": "3",
            "config": CONFIG_FILEPATH,
            "main_folder": MAIN_FOLDER,
            "stamp_filepath": "",
            "filter_filepath": ""
        }

        self.save()

    def parse_config_file(self):
        with open(CONFIG_FILEPATH, "r") as file:
            file_content = file.read()
        
        lines = file_content.split("\n")
        for line in lines:
            param, value = line.split(",")
            self.config_dict[param] = value

    def set(self, param, value):
        self.config_dict[param] = value

    def get(self, param):
        if param in self.config_dict.keys():
            value = self.config_dict[param]
        else:
            value = 0
            # Its useful to set 0 to default values

        return value
    
    def get_all(self):
        return self.config_dict

    def save(self, config_dict=None):
        if not config_dict:
            config_dict = self.config_dict

        file_content = ""
        for key, value in config_dict.items():
            file_content += f"{key},{value}\n"

        file_content = file_content[:-1]
        # Deletes last \n to not generate other item on parsing

        with open(CONFIG_FILEPATH, "w") as file:
            file.write(file_content)

class ImageProcessor():
    def __init__(self):
        if not os.path.exists(MAIN_FOLDER):
            os.makedirs(MAIN_FOLDER)

        configActions = ConfigManager()
        stamp_filepath = configActions.get("stamp_filepath")
        filter_filepath = configActions.get("filter_filepath")

        self.border_size = 10
        self.stamp_filepath = stamp_filepath
        self.filter_filepath = filter_filepath

    def apply_filter(self, image):
        filter_image = Image.open(self.filter_filepath)
        filter_image = filter_image.resize(image.size)
        image.paste(filter_image, (0, 0), filter_image)

        return image

    def append_horizontally(self, images, width, total_width, max_height):
        new_im_x = Image.new('RGB', (total_width, max_height), (255, 255, 255))

        x_offset = 0
        for im in images:
            new_im_x.paste(im, (x_offset, self.border_size))
            x_offset += width + self.border_size

        return new_im_x

    def append_vertically(self, image, total_width, max_height, faces):
        total_height = max_height * faces + self.border_size * (faces - 1)
        new_im_y = Image.new('RGB', (total_width, total_height), (255, 255, 255))

        y_offset = 0
        for _ in range(faces):
            new_im_y.paste(image, (self.border_size, y_offset))
            y_offset += max_height + self.border_size

        return new_im_y

    def save(self, images_list, filename):
        images = list()
        faces = list()

        for item in images_list:
            image, face = item
            image = Image.fromarray(image)

            if len(self.filter_filepath) and os.path.exists(self.filter_filepath):
                image = self.apply_filter(image)
                # Applies filter
            else:
                # print("Filter filepath not exists or not assigned")
                print("Archivo de filtro no existo o no fue seleccionado")

            images.append(image)
            faces.append(face)

        faces = max(set(faces), key=faces.count) or 1
        # Gets most common case on faces list, minimum 1

        images_size = images[0].size
        width, height = images_size

        if len(self.stamp_filepath) and os.path.exists(self.stamp_filepath):
            stamp_image = Image.open(open(self.stamp_filepath, "rb"))
            stamp_image = stamp_image.resize((stamp_image.size[0], images_size[1]))
            images.insert(0, stamp_image)
        # Adds stamp resized to common images size

        total_width = width * len(images) + self.border_size * len(images)
        max_height = height + self.border_size * 2

        new_im_x = self.append_horizontally(images, width, total_width, max_height)

        new_im_y = self.append_vertically(new_im_x, total_width, max_height, faces)

        new_im_y.save(filename)
        os.system(f"start {filename}")
        # Open photo in file system

class QtCapture(QWidget):
    def __init__(self, *args, fps=30, width=840, height=680):
        super(QWidget, self).__init__()

        if len(args) == 0:
            configActions = ConfigManager()
            capture_index = int(configActions.get("camera_index"))

            args = (capture_index,)

        self.cap = cv2.VideoCapture(*args)

        self.fps = fps
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

        self.setWindowTitle('Ventana de Captura')

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
        button.setFont(QtGui.QFont('Arial', 15))
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
        button.setFont(QtGui.QFont('Arial', 15))
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

class ConfigWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        configActions = ConfigManager()
        self.all_config = configActions.get_all()

        self.label_font_size = 11

        self.setWindowTitle('Configuración')
        self.initUI()

    def addLineEdit(self, text=None):
        lineEdit = QLineEdit()
        lineEdit.setAlignment(QtCore.Qt.AlignCenter)

        if text:
            lineEdit.setText(text)

        return lineEdit
        
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
        images_per_session_label = self.addLabel("Imágenes por sesión", self.label_font_size)
        self.images_session_entry = self.addLineEdit(self.all_config["images_session"])

        self.config_dir_label = self.addLabel(self.all_config["config"], self.label_font_size)
        change_dir_button = self.addButton("Cambiar directorio", self.change_dir_config)

        self.main_folder_label = self.addLabel(self.all_config["main_folder"], self.label_font_size)
        main_folder_button = self.addButton("Cambiar directorio", self.change_dir_main_folder)

        self.stamp_filepath_label = self.addLabel(self.all_config["stamp_filepath"] or "Stamp file path", self.label_font_size)
        stamp_filepath_change_button = self.addButton("Cambiar directorio", self.change_dir_stamp)
        stamp_filepath_clear_button = self.addButton("Borrar etiqueta", self.clear_stamp)

        self.filter_filepath_label = self.addLabel(self.all_config["filter_filepath"] or "Filter file path", self.label_font_size)
        filter_filepath_change_button = self.addButton("Cambiar directorio", self.change_dir_filter)
        filter_filepath_clear_button = self.addButton("Borrar filtro", self.clear_filter)

        save_button = self.addButton("Guardar todo", self.save_all)
        cancel_button = self.addButton("Cancelar", self.close)

        gbox = QGridLayout(self)
        self.setLayout(gbox)

        gbox.addWidget(images_per_session_label, 0, 0)
        gbox.addWidget(self.images_session_entry, 0, 1)
        gbox.addWidget(self.config_dir_label, 1, 0)
        gbox.addWidget(change_dir_button, 1, 1)
        gbox.addWidget(self.main_folder_label, 2, 0)
        gbox.addWidget(main_folder_button, 2, 1)
        gbox.addWidget(self.stamp_filepath_label, 3, 0)
        gbox.addWidget(stamp_filepath_change_button, 3, 1)
        gbox.addWidget(stamp_filepath_clear_button, 3, 2)
        gbox.addWidget(self.filter_filepath_label, 4, 0)
        gbox.addWidget(filter_filepath_change_button, 4, 1)
        gbox.addWidget(filter_filepath_clear_button, 4, 2)
        gbox.addWidget(save_button, 5, 1)
        gbox.addWidget(cancel_button, 5, 2)

    def change_dir_config(self):
        fname = QFileDialog.getOpenFileName(self, 'Seleccionar archivo', 
           DIRECTORY)

        selected_filepath = fname[0]

        if len(selected_filepath) == 0:
            return
        
        self.all_config["config"] = selected_filepath
        self.config_dir_label.setText(selected_filepath)

    def change_dir_main_folder(self):
        directory = str(QFileDialog.getExistingDirectory(self, "Seleccionar directorio"))

        if len(directory) == 0:
            return
        
        self.all_config["main_folder"] = directory

    def change_dir_stamp(self):
        fname = QFileDialog.getOpenFileName(self, 'Seleccionar archivo', 
           DIRECTORY, "Image files (*.jpg *.png *.jpeg)")

        selected_filepath = fname[0]

        if len(selected_filepath) == 0:
            return
        
        self.all_config["stamp_filepath"] = selected_filepath
        self.stamp_filepath_label.setText(selected_filepath)

    def change_dir_filter(self):
        fname = QFileDialog.getOpenFileName(self, 'Seleccionar archivo', 
           DIRECTORY, "Image files (*.jpg *.png *.jpeg)")

        selected_filepath = fname[0]

        if len(selected_filepath) == 0:
            return
        
        self.all_config["filter_filepath"] = selected_filepath
        self.filter_filepath_label.setText(selected_filepath)

    def clear_stamp(self):
        self.all_config["stamp_filepath"] = ""

        self.stamp_filepath_label.setText("Directorio de etiqueta")

    def clear_filter(self):
        self.all_config["filter_filepath"] = ""
        self.filter_filepath_label.setText("Directorio de filtro")

    def save_all(self):
        images_per_session = self.images_session_entry.text()
        if images_per_session != "":
            self.all_config["images_session"] = images_per_session

        configActions = ConfigManager()
        configActions.save(self.all_config)

        self.close()

class ControlWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.capture = None
        self.calibrateWindow = None

        self.initUI()

        self.setWindowTitle('Panel de Control')
        self.showFullScreen()
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
        self.title = self.addLabel("Cabina de fotos", 25)

        self.start_button = self.addButton("Comenzar", self.startCapture)
        self.calibrate_button = self.addButton("Calibrar", self.calibrate)
        self.select_camera_button = self.addButton("Seleccionar cámara", self.select_camera)
        self.open_config_button = self.addButton("Abrir configuración", self.open_config)
        self.open_explorer_button = self.addButton("Abrir carpeta de imágenes", self.open_explorer)
        self.quit_button = self.addButton("Salir", self.endCapture)

        gbox = QGridLayout(self)
        self.setLayout(gbox)

        gbox.addWidget(self.title, 0, 0)
        gbox.addWidget(self.start_button, 1, 0)
        gbox.addWidget(self.calibrate_button, 1, 1)
        gbox.addWidget(self.select_camera_button, 2, 0)
        gbox.addWidget(self.open_config_button, 2, 1)
        gbox.addWidget(self.open_explorer_button, 3, 0)
        gbox.addWidget(self.quit_button, 3, 1)

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

    def select_camera(self):
        if not self.capture:
            self.capture = QtSelectCameraCapture()
            self.capture.setCloseCallback(self.captureQuitHandler)
            self.capture.setParent(self)
            self.capture.setWindowFlags(QtCore.Qt.Tool)

        self.capture.start()
        self.capture.show()

    def open_config(self):
        self.configWindow = ConfigWindow()
        self.configWindow.show()

    def startCapture(self):
        if not self.capture:
            self.capture = QtSaveContentCapture()
            self.capture.setCloseCallback(self.captureQuitHandler)
            self.capture.setParent(self)
            self.capture.setWindowFlags(QtCore.Qt.Tool)

        self.capture.start()
        self.capture.show()

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
    global CONFIG_FILENAME, CONFIG_FILEPATH, MAIN_FOLDER, IMAGES_PER_SESSION

    argparsing = ArgParsing()
    args = argparsing.get()

    if args["config"]:
        CONFIG_FILENAME = args["config"]
        CONFIG_FILEPATH = f"{DIRECTORY}/{CONFIG_FILENAME}"
    if args["main"]:
        MAIN_FOLDER = args["main"]
    if args["images"]:
        IMAGES_PER_SESSION = args["images"]

    configActions = ConfigManager()
    configActions.save()
    # Saves changes

    app = QApplication(sys.argv)
    control_window = ControlWindow()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()