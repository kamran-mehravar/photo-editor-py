import os
import time
from PIL import Image, ImageEnhance

UPLOAD_FOLDER = "backend/static/uploads"
OUTPUT_FOLDER = "backend/static"

# بررسی مسیرها و ایجاد آن‌ها در صورت عدم وجود
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def process_image(file, method="pillow"):
    """ پردازش تصویر با Pillow """
    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(input_path)  
    print(f"File saved at: {input_path}")  
    
    image = Image.open(input_path)

    # تبدیل RGBA به RGB اگر لازم باشد
    if image.mode == "RGBA":
        image = image.convert("RGB")

    # تنظیم روشنایی
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.2)

    # تغییر اشباع رنگ
    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(1.5)

    # تولید نام خروجی تصادفی بر اساس timestamp
    output_filename = f"output_{int(time.time())}.jpg"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)
    image.save(output_path, format="JPEG")

    print(f"Processed image saved at: {output_path}")

    return f"/static/{output_filename}"

