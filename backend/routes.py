from flask import Blueprint, request, jsonify
from services.image_processor import process_image

image_routes = Blueprint('image_routes', __name__)

@image_routes.route("/upload", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    print(f"Received file: {file.filename}")  # چک کن که فایل دریافت شده یا نه
    
    method = request.form.get("method", "pillow")  # متد پردازش
    processed_image = process_image(file, method)

    return jsonify({"message": "Image processed successfully", "image_url": processed_image})

