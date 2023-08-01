import os

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
                                QWidget, QPushButton,
                                QLabel, QLineEdit,
                                QGridLayout, QFileDialog,
                                QSizePolicy
                            )

from globals import DIRECTORY, CONFIG_FILEPATH, MAIN_FOLDER, FONT_DEFAULT

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
            "open_on_save": False,
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
        button.setFont(QtGui.QFont(*FONT_DEFAULT))
        button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        if callback:
            button.clicked.connect(callback)

        return button

    def addLabel(self, text, fontSize):
        label = QLabel(text)
        label.setFont(QtGui.QFont('Arial', fontSize))

        return label
    
    def addCheckButton(self, text, callback, fontSize):
        check = QtWidgets.QCheckBox(self)
        check.setText(text)
        check.toggled.connect(callback)

        return check

    def initUI(self):
        images_per_session_label = self.addLabel("Imágenes por sesión", self.label_font_size)
        self.images_session_entry = self.addLineEdit(self.all_config["images_session"])

        self.config_dir_label = self.addLabel(self.all_config["config"], self.label_font_size)
        change_dir_button = self.addButton("Cambiar directorio", self.change_dir_config)

        self.main_folder_label = self.addLabel(self.all_config["main_folder"], self.label_font_size)
        main_folder_button = self.addButton("Cambiar directorio", self.change_dir_main_folder)

        open_files_on_save_label = self.addLabel("Abrir al guardar", self.label_font_size)
        self.open_files_on_save_checkbutton = self.addCheckButton("No abrir imagen", self.open_files_on_save, self.label_font_size)
        if self.all_config["open_on_save"] == "True":
            self.open_files_on_save_checkbutton.setChecked(True)
        else:
            self.open_files_on_save_checkbutton.setChecked(False)
        # Set current value to checkbox

        self.stamp_filepath_label = self.addLabel(self.all_config["stamp_filepath"] or "Directorio estampa", self.label_font_size)
        stamp_filepath_change_button = self.addButton("Cambiar directorio", self.change_dir_stamp)
        stamp_filepath_clear_button = self.addButton("Borrar estampa", self.clear_stamp)

        self.filter_filepath_label = self.addLabel(self.all_config["filter_filepath"] or "Directorio filtro", self.label_font_size)
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
        gbox.addWidget(open_files_on_save_label, 3, 0)
        gbox.addWidget(self.open_files_on_save_checkbutton, 3, 1),
        gbox.addWidget(self.stamp_filepath_label, 4, 0)
        gbox.addWidget(stamp_filepath_change_button, 4, 1)
        gbox.addWidget(stamp_filepath_clear_button, 4, 2)
        gbox.addWidget(self.filter_filepath_label, 5, 0)
        gbox.addWidget(filter_filepath_change_button, 5, 1)
        gbox.addWidget(filter_filepath_clear_button, 5, 2)
        gbox.addWidget(save_button, 6, 1)
        gbox.addWidget(cancel_button, 6, 2)

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

    def open_files_on_save(self):
        status = self.sender().isChecked()

        if status == True:
            self.open_files_on_save_checkbutton.setText("Abrir imagen")
        else:
            self.open_files_on_save_checkbutton.setText("No abrir imagen")

        self.all_config["open_on_save"] = status

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