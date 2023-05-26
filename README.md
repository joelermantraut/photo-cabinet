# photo-cabinet
Esta en una aplicación de fotografia para cabinas, escrita en Python. Incluye una función para calibrar el coeficiente que utiliza para capturar rostros del numero de personas en fotos.

## Configuración

1. Primero, clone este repositorio.
2. Ejecute:
```
cd photo-cabinet
python -m virtualenv .
pip install -r requirements.txt
```
3. Si quiero compilar en un ejectuable, puede utilizar pyinstaller con cualquier parámetros que prefiera, pero debe seguir [esta](https://stackoverflow.com/questions/67887088/issues-compiling-mediapipe-with-pyinstaller-on-macos) respuesta en Stack Overflow para incluir la dependencia mediapipe.
