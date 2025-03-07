from flask import Blueprint, request, jsonify, send_file
import os
import time
from services.image_processor import process_image  # اضافه کردن تابع پردازش تصویر

image_routes = Blueprint('image_routes', __name__)

TEMP_STORAGE = "backend/static/uploads"
OUTPUT_STORAGE = "backend/static/processed"

# اطمینان از وجود دایرکتوری‌های ضروری
for folder in [TEMP_STORAGE, OUTPUT_STORAGE]:
    os.makedirs(folder, exist_ok=True)


@image_routes.route("/upload", methods=["POST"])
def upload_image():
    """آپلود تصویر و ذخیره آن در سرور"""
    cleanup_images()  # حذف فایل‌های قدیمی

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    image_id = f"{int(time.time())}_{file.filename}"
    file_path = os.path.join(TEMP_STORAGE, image_id)
    file.save(file_path)

    print(f"✅ Image uploaded: {file_path}")  # نمایش مسیر ذخیره شده در لاگ سرور

    return jsonify({
        "message": "File uploaded successfully",
        "image_id": image_id
    })



@image_routes.route("/apply_hsl", methods=["POST"])
def apply_hsl():
    """اعمال تغییرات HSL روی تصویر"""
    data = request.get_json()
    image_id = data.get("image_id")
    hue = int(data.get("hue", 0))
    saturation = int(data.get("saturation", 0))
    luminance = int(data.get("luminance", 0))
    hue_range = data.get("hue_range", None)  # دریافت محدوده رنگ انتخاب‌شده

    input_path = os.path.join(TEMP_STORAGE, image_id)

    if not os.path.exists(input_path):
        print(f"❌ Image not found: {input_path}")
        return jsonify({"error": "Image not found"}), 404

    print(f"🎨 Processing image with HSL: Hue={hue}, Saturation={saturation}, Luminance={luminance}, Hue Range={hue_range}")

    output_path = process_image(input_path, hue, saturation, luminance, hue_range)
    output_filename = os.path.basename(output_path)

    return jsonify({
        "image_url": f"/static/processed/{output_filename}",
        "download_url": f"/download/{output_filename}"
    })

@image_routes.route("/download/<image_id>")
def download_image(image_id):
    """دانلود فایل پردازش‌شده"""

    # بررسی مسیر درست برای ذخیره‌شده تصویر پردازش‌شده
    output_path = os.path.join(os.getcwd(), OUTPUT_STORAGE, image_id)

    if not os.path.exists(output_path):
        print(f"❌ Download failed: {output_path} not found!")  # نمایش خطا در لاگ سرور
        return jsonify({"error": f"File not found: {output_path}"}), 404

    return send_file(output_path, as_attachment=True)


def cleanup_images():
    """حذف تصاویر قدیمی بعد از ۶۰ روز"""
    now = time.time()
    for folder in [TEMP_STORAGE, OUTPUT_STORAGE]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path) and now - os.path.getmtime(file_path) > 60 * 24 * 60 * 60:
                os.remove(file_path)
