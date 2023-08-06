import os

IMAGES_PER_SESSION = 3
DIRECTORY = f"{os.path.expanduser('~')}/photo-cabinet"
MAIN_FOLDER = f"{DIRECTORY}/images"
CONFIG_FILENAME = ".config"
CONFIG_FILEPATH = f"{DIRECTORY}/{CONFIG_FILENAME}"
RESOLUTION_X = 800
RESOLUTION_Y = 640
A4_SIZE = {"width": 210, "height": 297}
PT_MM_RELATION = 0.35
FILE_SAVE_NAME = "imprimir_fotos"
FONT_DEFAULT = ("Arial", 15)