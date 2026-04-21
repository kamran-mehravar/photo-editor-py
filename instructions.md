````markdown
# Flask Photo Editor Setup Guide

## Overview

This document explains how to set up and run a Flask-based photo editor project that integrates **GIMP** for image processing on Linux.

The stack includes:

- Python 3.10
- Flask
- Pillow
- NumPy
- GIMP installed via Flatpak

This version uses Flask as the backend and calls a custom GIMP Python plugin to process uploaded images.

---

## Step 1: Prepare the Development Environment

### Install prerequisites on Linux

```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev -y
sudo apt install flatpak -y
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install flathub org.gimp.GIMP -y
```

This installs:

- Python 3.10
- Python virtual environment support
- Python development headers
- Flatpak
- GIMP

---

## Step 2: Create the Project Structure

### Create the project directory

```bash
mkdir flask-photo-editor
cd flask-photo-editor
```

### Create and activate a virtual environment

```bash
python3.10 -m venv venv
source venv/bin/activate
```

### Install the required Python packages

```bash
pip install flask numpy pillow
```

---

## Step 3: Suggested Project Layout

```text
flask-photo-editor/
│── app/
│   │── static/            # CSS and JavaScript files
│   │── templates/         # HTML templates
│   │── routes.py          # Flask routes
│   │── image_processor.py # Image processing with GIMP
│   │── __init__.py        # Flask app initialization
│── venv/                  # Python virtual environment
│── requirements.txt       # Python dependencies
│── config.py              # Project configuration
│── run.py                 # Application entry point
│── README.md              # Project documentation
```

---

## Step 4: Create the Main Project Files

### `run.py`

```python
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
```

### `app/__init__.py`

```python
from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_object('config')

    from app.routes import main
    app.register_blueprint(main)

    return app
```

### `app/routes.py`

```python
from flask import Blueprint, render_template, request, jsonify
from app.image_processor import process_image

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/edit', methods=['POST'])
def edit_image():
    image = request.files['image']
    params = request.form.to_dict()
    output_path = process_image(image, params)
    return jsonify({'output': output_path})
```

At this point, the Flask backend is ready.

---

## Step 5: Create a GIMP Plugin

GIMP uses Python-Fu for plugins, so a custom plugin is needed for image editing operations.

### Create the plugin directory and file

```bash
mkdir -p ~/.config/GIMP/2.10/plug-ins/
nano ~/.config/GIMP/2.10/plug-ins/my_plugin.py
```

### `~/.config/GIMP/2.10/plug-ins/my_plugin.py`

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gimpfu import *

def my_custom_filter(image, drawable):
    """Increase image brightness"""
    pdb.gimp_brightness_contrast(drawable, 30, 10)
    pdb.gimp_displays_flush()

register(
    "python_fu_my_custom_filter",
    "Increase Brightness",
    "A simple filter to increase image brightness",
    "Kamran",
    "Open Source",
    "2025",
    "<Image>/Filters/My Custom Filter",
    "*",
    [],
    [],
    my_custom_filter
)

main()
```

### Make the plugin executable

```bash
chmod +x ~/.config/GIMP/2.10/plug-ins/my_plugin.py
```

---

## Step 6: Test the Plugin in GIMP

### Run GIMP

```bash
flatpak run org.gimp.GIMP
```

Then go to:

```text
Filters > My Custom Filter
```

If **My Custom Filter** appears, the plugin has been loaded correctly.

---

## Step 7: Test the Plugin in the GIMP Python Console

Open GIMP and go to:

```text
Filters > Python-Fu > Console
```

Then run:

```python
img = gimp.image_list()[0]
layer = img.active_layer
pdb.python_fu_my_custom_filter(img, layer)
```

If the image changes, the plugin works correctly.

---

## Step 8: Connect GIMP to Flask

Now Flask needs to call GIMP during image processing.

### `app/image_processor.py`

```python
import os
from PIL import Image
from subprocess import call

def process_image(image, params):
    input_path = "static/uploads/input.png"
    output_path = "static/uploads/output.png"

    image.save(input_path)

    # Run the GIMP plugin for image processing
    call([
        "flatpak", "run", "org.gimp.GIMP",
        "--batch-interpreter=python-fu-eval",
        "-b",
        "import gimpfu; img = pdb.file_png_load('{}', '{}'); layer = img.active_layer; pdb.python_fu_my_custom_filter(img, layer); pdb.file_png_save(img, layer, '{}', '{}', False, 9, True, False, False, False, False);".format(
            input_path, input_path, output_path, output_path
        )
    ])

    return output_path
```

At this stage, Flask can invoke GIMP to process uploaded images.

---

## Step 9: Run the Project

### Start the application

```bash
python run.py
```

Then open the browser at:

```text
http://127.0.0.1:5000/
```

---

## Alternative Run Command

You can also run the Flask app like this:

```bash
PYTHONPATH=$(pwd) flask --app backend/app.py run --host=127.0.0.1 --port=5000
```

---

## Notes

- This setup is intended for Linux.
- GIMP is installed through Flatpak.
- The image processing flow depends on a custom Python-Fu GIMP plugin.
- Flask handles the web interface and delegates image operations to GIMP.

## Future Improvements

Possible next improvements include:

- more image editing controls
- additional GIMP filters
- error handling for missing files or invalid uploads
- support for multiple output formats
- better frontend integration for real-time preview
````
