import os
from PIL import Image

from globals import MAIN_FOLDER
from ConfigManager import ConfigManager

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
        filter_image = Image.open(self.filter_filepath).convert("RGBA")
        filter_image = filter_image.resize(image.size)
        image.paste(filter_image, (0, 0), filter_image)

        return image
    
    def apply_stamp(self, images, images_size):
        if len(self.stamp_filepath) and os.path.exists(self.stamp_filepath):
            stamp_image = Image.open(open(self.stamp_filepath, "rb"))
            stamp_image = stamp_image.resize((stamp_image.size[0], images_size[1]))
            images.insert(0, stamp_image)

        return images

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
        faces = 6 if faces > 6 else faces
        # Gets most common case on faces list, minimum 1
        # maximum 6

        images_size = images[0].size
        width, height = images_size

        images = self.apply_stamp(images, images_size)
        # Adds stamp resized to common images size

        total_width = width * len(images) + self.border_size * len(images)
        max_height = height + self.border_size * 2

        new_im_x = self.append_horizontally(images, width, total_width, max_height)

        new_im_y = self.append_vertically(new_im_x, total_width, max_height, faces)

        new_im_y.save(filename)
        os.system(f"start {filename}")
        # Open photo in file system