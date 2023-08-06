import sys

from PyQt5.QtWidgets import QApplication

from globals import *
from ConfigManager import ConfigManager
from ArgParsing import ArgParsing
from ControlWindow import ControlWindow

def main():
    global CONFIG_FILENAME, CONFIG_FILEPATH, MAIN_FOLDER, IMAGES_PER_SESSION, \
            FILE_SAVE_NAME, RESOLUTION_X, RESOLUTION_Y, REPOSITORY_URL

    argparsing = ArgParsing()
    args = argparsing.get()

    if args["config"]:
        CONFIG_FILENAME = args["config"]
        CONFIG_FILEPATH = f"{DIRECTORY}/{CONFIG_FILENAME}"
    if args["main"]:
        MAIN_FOLDER = args["main"]
    if args["images"]:
        IMAGES_PER_SESSION = args["images"]
    if args["save_filename"]:
        FILE_SAVE_NAME = args["save_filename"]
    if args["res_x"]:
        RESOLUTION_X = args["res_x"]
    if args["res_y"]:
        RESOLUTION_Y = args["res_y"]

    configActions = ConfigManager()
    configActions.save()
    # Saves changes, and create directories

    app = QApplication(sys.argv)
    control_window = ControlWindow()
    # Keep var to not destroy object

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()