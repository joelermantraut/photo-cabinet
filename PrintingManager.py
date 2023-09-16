from fpdf import FPDF
from PIL import Image
import time

from globals import A4_SIZE, PT_MM_RELATION

class PrintingManager():
    def __init__(self):
        pass

    def prepare_to_print(self, pdf_path, files_to_print):
        pdf = FPDF("P", "pt")
        pdf.add_page()

        images_len = len(files_to_print)

        actual_height = 0
        for image_index, image in enumerate(files_to_print):
            PILImage = Image.open(image)
            width, height = PILImage.size
            real_height = height * (A4_SIZE["width"] / PT_MM_RELATION) / width
            if (actual_height + real_height) > A4_SIZE["height"] / PT_MM_RELATION:
                pdf.add_page()
                actual_height = 0

            pdf.image(image, 0, actual_height, A4_SIZE["width"] / PT_MM_RELATION)
            actual_height += real_height + 10

            # Update progress bar
            time.sleep(1)

        pdf.output(pdf_path, "F")

        # https://stackoverflow.com/questions/27327513/create-pdf-from-a-list-of-images
