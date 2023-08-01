import argparse

class ArgParsing():
    def __init__(self):
        self.ap = None
        self.set()

    def set(self):
        self.ap = argparse.ArgumentParser()
        self.ap.add_argument("-c", "--config", required=False, help="Sets config file name and path")
        self.ap.add_argument("-m", "--main", required=False, help="Sets images folder path")
        self.ap.add_argument("-i", "--images", required=False, help="Sets number of images per session")
        self.ap.add_argument("-s", "--save-filename", required=False, help="Sets filename of pdf save file")
        self.ap.add_argument("-x", "--res-x", required=False, help="Sets resoluition x parameter")
        self.ap.add_argument("-y", "--res-y", required=False, help="Sets resolution y parameter")

    def get(self):
        return vars(self.ap.parse_args())