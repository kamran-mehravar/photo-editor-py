from flask import Blueprint, request, jsonify, send_file
import os
import time
from backend.image_processor import process_with_skimage_color_range, process_with_style_transfer

image_routes = Blueprint('image_routes', __name__)

UPLOAD_FOLDER = "static/uploads"
PROCESSED_FOLDER = "static/processed"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@image_routes.route("/upload", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    image_id = f"{int(time.time())}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, image_id)
    file.save(file_path)

    return jsonify({"image_id": image_id, "image_url": f"/static/uploads/{image_id}"})

@image_routes.route("/apply_hsl", methods=["POST"])
def apply_hsl():
    data = request.json
    image_id = data.get("image_id")
    hue = int(data.get("hue", 0))
    saturation = int(data.get("saturation", 0))
    luminance = int(data.get("luminance", 0))
    selected_color = data.get("color", None)  # مثلاً 'red', 'blue', 'green', ...

    input_path = os.path.join(UPLOAD_FOLDER, image_id)
    if not os.path.exists(input_path):
        return jsonify({"error": "Image not found"}), 404

    try:
        # فراخوانی تابع جدید با استفاده از skimage و پالت رنگی انتخابی
        output_path = process_with_skimage_color_range(
            input_path, hue, saturation, luminance, selected_color
        )
    except Exception as e:
        print("Error during skimage processing:", e)
        return jsonify({"error": f"Error during processing: {str(e)}"}), 500

    return jsonify({
        "image_url": f"/static/processed/{os.path.basename(output_path)}",
        "download_url": f"/download/{os.path.basename(output_path)}"
    })

@image_routes.route("/apply_style", methods=["POST"])
def apply_style():
    data = request.json
    image_id = data.get("image_id")
    model_name = data.get("model_name", "candy")

    input_path = os.path.join(UPLOAD_FOLDER, image_id)
    if not os.path.exists(input_path):
        return jsonify({"error": "Image not found"}), 404

    try:
        output_path = process_with_style_transfer(input_path, model_name)
    except Exception as e:
        print("Error during style transfer:", e)
        return jsonify({"error": f"Error during style transfer: {str(e)}"}), 500

    return jsonify({
        "image_url": f"/static/processed/{os.path.basename(output_path)}",
        "download_url": f"/download/{os.path.basename(output_path)}"
    })

@image_routes.route("/download/<image_id>")
def download_image(image_id):
    output_path = os.path.join(PROCESSED_FOLDER, image_id)
    if not os.path.exists(output_path):
        return jsonify({"error": "File not found"}), 404
    return send_file(output_path, as_attachment=True)
