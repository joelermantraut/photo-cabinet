# photo-cabinet
Photo Cabinet app developed with Python. It includes a calibration function to calibrate coefficent to catch faces and count number of people in photo.

## Setup

1. First, clone this repository.
2. Run:
```
cd photo-cabinet
python -m virtualenv .
pip install -r requirements.txt
```
3. If you want to compile in an executable, you can use pyinstaller with any parameters you want, but must follow [this](https://stackoverflow.com/questions/67887088/issues-compiling-mediapipe-with-pyinstaller-on-macos) response in Stack Overflow to include mediapipe dependency.