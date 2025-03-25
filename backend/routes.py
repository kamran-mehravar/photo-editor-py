from flask import Blueprint, request, jsonify, send_file
import os
import time
from backend.image_processor import process_with_skimage_color_range, process_with_style_transfer, \
    process_with_temperature_tint, process_with_light_adjustments

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
    return send_file(output_path, as_attachment=True, attachment_filename=image_id)


@image_routes.route("/apply_temperature_tint", methods=["POST"])
def apply_temperature_tint():
    data = request.json
    image_id = data.get("image_id")
    temperature_factor = float(data.get("temperature_factor", 1.0))
    red_factor = float(data.get("red_factor", 1.0))
    blue_factor = float(data.get("blue_factor", 1.0))
    vibrancy_factor = float(data.get("vibrancy_factor", 1.0))
    saturation_factor = float(data.get("saturation_factor", 1.0))

    input_path = os.path.join(UPLOAD_FOLDER, image_id)
    if not os.path.exists(input_path):
        return jsonify({"error": "Image not found"}), 404

    try:
        output_path = process_with_temperature_tint(input_path, temperature_factor, red_factor, blue_factor,
                                                    vibrancy_factor, saturation_factor)
    except Exception as e:
        print("Error during temperature and tint adjustment:", e)
        return jsonify({"error": f"Error during processing: {str(e)}"}), 500

    return jsonify({
        "temperature_image_url": f"/static/processed/{os.path.basename(output_path)}",
        "download_url": f"/download/{os.path.basename(output_path)}"
    })
@image_routes.route("/reset_color", methods=["POST"])
def reset_color():
    data = request.json
    image_id = data.get("image_id")

    input_path = os.path.join(UPLOAD_FOLDER, image_id)
    if not os.path.exists(input_path):
        return jsonify({"error": "Image not found"}), 404

    return jsonify({
        "image_url": f"/static/uploads/{image_id}",
        "download_url": f"/download/{image_id}"
    })


@image_routes.route("/apply_light", methods=["POST"])
def apply_light():
    data = request.json
    image_id = data.get("image_id")
    dehaze = float(data.get("dehaze", 1.0))
    exposure_val = float(data.get("exposure", 1.0))
    brightness = float(data.get("brightness", 1.0))
    contrast = float(data.get("contrast", 1.0))
    highlights = float(data.get("highlights", 1.0))
    shadows = float(data.get("shadows", 1.0))
    whites = float(data.get("whites", 98))
    blacks = float(data.get("blacks", 2))

    input_path = os.path.join(UPLOAD_FOLDER, image_id)
    if not os.path.exists(input_path):
        return jsonify({"error": "Image not found"}), 404

    try:
        output_path = process_with_light_adjustments(
            input_path, dehaze, exposure_val, brightness, contrast, highlights,
            shadows, whites, blacks
        )
    except Exception as e:
        print("Error during light adjustments:", e)
        return jsonify({"error": f"Error during processing: {str(e)}"}), 500

    return jsonify({
        "light_image_url": f"/static/processed/{os.path.basename(output_path)}",
        "download_url": f"/download/{os.path.basename(output_path)}"
    })