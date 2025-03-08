from flask import Blueprint, request, jsonify, send_file
import os
import time
from backend.services.image_processor import process_with_gimp
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')
image_routes = Blueprint('image_routes', __name__)

TEMP_STORAGE = "backend/static/uploads"
OUTPUT_STORAGE = "backend/static/processed"

# Ensure required directories exist
for folder in [TEMP_STORAGE, OUTPUT_STORAGE]:
    os.makedirs(folder, exist_ok=True)

@image_routes.route("/upload", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    image_id = f"{int(time.time())}_{file.filename}"
    file_path = os.path.join(TEMP_STORAGE, image_id)
    file.save(file_path)

    return jsonify({"message": "File uploaded successfully", "image_id": image_id})


@image_routes.route("/apply_hsl", methods=["POST"])
def apply_hsl():
    data = request.json
    print("📥 Received HSL Request:", data)

    image_id = data.get("image_id")
    hue = int(data.get("hue"))
    saturation = int(data.get("saturation"))
    luminance = int(data.get("luminance"))
    color_index = int(data.get("color_index"))

    input_path = os.path.join(TEMP_STORAGE, image_id)
    if not os.path.exists(input_path):
        return jsonify({"error": "Image not found"}), 404

    print("🚀 Processing with GIMP:", input_path, hue, saturation, luminance, color_index)

    output_path = process_with_gimp(input_path, hue, saturation, luminance, color_index)

    return jsonify({
        "image_url": f"/static/processed/{image_id}",
        "download_url": f"/download/{image_id}"
    })

@image_routes.route("/download/<image_id>")
def download_image(image_id):
    """Handles processed image downloads"""
    output_path = os.path.join(OUTPUT_STORAGE, image_id)
    if not os.path.exists(output_path):
        return jsonify({"error": "File not found"}), 404

    return send_file(output_path, as_attachment=True)

def cleanup_images():
    """Deletes images older than 60 days"""
    now = time.time()
    for folder in [TEMP_STORAGE, OUTPUT_STORAGE]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path) and now - os.path.getmtime(file_path) > 60 * 24 * 60 * 60:
                os.remove(file_path)
