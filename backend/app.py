from flask import Flask, render_template, request, jsonify, send_file, Blueprint
import os
import time
from backend.services.image_processor import process_with_gimp

# تنظیم مسیرهای ذخیره‌سازی

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/uploads")
PROCESSED_FOLDER = os.path.join(BASE_DIR, "static/processed")
TEMPLATE_FOLDER = os.path.join(BASE_DIR, "templates")

# ایجاد پوشه‌ها در صورت عدم وجود
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# مقداردهی اولیه Flask
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "static"),
                       template_folder=TEMPLATE_FOLDER)



# ایجاد Blueprint
image_routes = Blueprint('image_routes', __name__)

@app.route('/')
def home():
    """نمایش صفحه اصلی"""
    print("✅ Loading index.html...")
    return render_template('index.html')

@image_routes.route("/upload", methods=["POST"])
def upload_image():
    """آپلود تصویر و ذخیره آن"""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    image_id = f"{int(time.time())}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, image_id)
    file.save(file_path)

    return jsonify({
        "message": "File uploaded successfully",
        "image_id": image_id
    })

@app.route("/apply_hsl", methods=["POST"])
def apply_hsl():
    """اعمال تغییرات HSL با استفاده از GIMP"""
    data = request.json
    image_id = data.get("image_id")
    hue = int(data.get("hue"))
    saturation = int(data.get("saturation"))
    luminance = int(data.get("luminance"))
    color = data.get("color")

    input_path = os.path.join(UPLOAD_FOLDER, image_id)
    output_path = os.path.join(PROCESSED_FOLDER, image_id)

    if not os.path.exists(input_path):
        return jsonify({"error": "Image not found"}), 404

    # اجرای GIMP با مسیرهای کامل
    cmd = f'gimp -i -b \'(batch-hsl "{os.path.abspath(input_path)}" "{os.path.abspath(output_path)}" {hue} {saturation} {luminance})\' -b \'(gimp-quit 0)\''
    os.system(cmd)

    if not os.path.exists(output_path):
        return jsonify({"error": "Processing failed"}), 500

    return jsonify({
        "image_url": f"/static/processed/{image_id}",
        "download_url": f"/download/{image_id}"
    })


@app.route("/download/<image_id>")
def download_image(image_id):
    """دانلود تصویر پردازش‌شده"""
    output_path = os.path.join(PROCESSED_FOLDER, image_id)
    if not os.path.exists(output_path):
        return jsonify({"error": "File not found"}), 404
    return send_file(output_path, as_attachment=True)

# ثبت Blueprint
app.register_blueprint(image_routes)

if __name__ == '__main__':
    app.run(debug=True)
