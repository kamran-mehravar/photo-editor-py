from PIL import Image
import numpy as np
import os


def process_image(image_path, hue, saturation, luminance, hue_range=None):
    """اعمال تغییرات HSL روی تصویر و فقط روی توناژ انتخاب‌شده در صورت مشخص شدن hue_range"""

    image = Image.open(image_path).convert("RGB")
    np_image = np.array(image)

    # تبدیل تصویر به HSV
    hsv_image = np.array(image.convert("HSV"))

    # مقدار hue را به بازه 0 تا 255 نگه‌داریم
    hue = int((hue / 360) * 255)  # تبدیل از بازه [0,360] به [0,255]
    hue = np.clip(hue, 0, 255)  # جلوگیری از مقدار منفی یا بیشتر از 255

    # مقدارهای saturation و luminance را قبل از اعمال، در بازه‌ی [-255, 255] محدود می‌کنیم
    saturation = np.clip(saturation, -255, 255)
    luminance = np.clip(luminance, -255, 255)

    if hue_range:
        min_hue, max_hue = hue_range
        min_hue = int((min_hue / 360) * 255)
        max_hue = int((max_hue / 360) * 255)

        hue_channel = hsv_image[:, :, 0]
        mask = (hue_channel >= min_hue) & (hue_channel <= max_hue)

        # جلوگیری از مقدار منفی یا بیش از حد در Hue, Saturation, Luminance
        hsv_image[:, :, 0][mask] = np.clip((hsv_image[:, :, 0][mask] + hue) % 255, 0, 255)
        hsv_image[:, :, 1][mask] = np.clip(hsv_image[:, :, 1][mask] + saturation, 0, 255)
        hsv_image[:, :, 2][mask] = np.clip(hsv_image[:, :, 2][mask] + luminance, 0, 255)

        image = Image.fromarray(hsv_image, "HSV").convert("RGB")

    output_path = image_path.replace("uploads", "processed")
    image.save(output_path)
    return output_path
