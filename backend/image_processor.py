import os
import numpy as np
from skimage import io, filters
from skimage.exposure import exposure, equalize_adapthist
from skimage.util import img_as_ubyte, img_as_float
from skimage.color import rgb2hsv, hsv2rgb, rgb2gray
import torch
from PIL import Image
from torchvision import transforms

def process_with_skimage_color_range(input_path, hue_adj, sat_adj, lum_adj, selected_color):
    """
    Apply HSL adjustments using skimage on the selected color range.
    If selected_color is "all" or invalid, adjustments are applied to the whole image.
    The modifications are applied cumulatively by overwriting the file at input_path.

    :param input_path: Path to the base image (current.jpg).
    :param hue_adj: Hue adjustment in degrees [-180,180].
    :param sat_adj: Saturation adjustment in percent [-100,100].
    :param lum_adj: Luminance adjustment in percent [-100,100].
    :param selected_color: A string representing the selected color (e.g., "red", "blue", "green", ...).
    :return: The path to the processed image (input_path).
    """
    # Define approximate hue ranges (in degrees) for various colors

    color_ranges = {
        "red": [(0, 15), (345, 360)],
        "orange": [(15, 30)],
        "yellow": [(30, 60)],
        "green": [(60, 150)],
        "blue": [(150, 240)],
        "purple": [(240, 300)],
        "brown": [(15, 25)],  # بسیار تقریبی؛ با orange تداخل دارد
    }

    # خواندن تصویر
    image = io.imread(input_path)
    if image.shape[2] == 4:
        image = image[:, :, :3]

    # تبدیل به float در بازه [0,1]
    image_float = image.astype(np.float32) / 255.0
    # تبدیل RGB به HSV
    hsv = rgb2hsv(image_float)

    # تابع کمکی برای بررسی اینکه hue در بازه‌ی رنگ انتخابی است یا نه
    def is_in_color_range(h_deg, ranges):
        # h_deg در بازه [0,360]
        for (low, high) in ranges:
            if low <= h_deg <= high:
                return True
        return False

    # Determine whether to apply adjustments to all pixels or only on selected color range
    apply_to_all = (selected_color is None) or (selected_color == "all") or (selected_color not in color_ranges)

    # تبدیل hue از [0,1] به [0,360]
    hue_array_deg = hsv[:, :, 0] * 360.0
    # offset مربوط به hue
    hue_offset = hue_adj

    # پیمایش پیکسل‌ها و اعمال تغییرات
    # روش برداری (vectorized) برای عملکرد بهتر
    # گام اول: اگر apply_to_all = True، همه پیکسل‌ها را انتخاب می‌کنیم
    # در غیر این صورت، فقط پیکسل‌های در محدوده‌ی hue انتخابی
    if not apply_to_all:
        # لیست بازه‌های رنگ مورد نظر
        color_intervals = color_ranges[selected_color]
        mask = np.zeros_like(hue_array_deg, dtype=bool)
        for (low, high) in color_intervals:
            # انتخاب پیکسل‌هایی که h_deg در [low, high] هستند
            mask |= ((hue_array_deg >= low) & (hue_array_deg <= high))
    else:
        # همه‌ی پیکسل‌ها
        mask = np.ones_like(hue_array_deg, dtype=bool)

    # فقط روی ماسک انتخابی تغییر اعمال می‌کنیم
    # ۱) تنظیم hue
    hue_array_deg[mask] = (hue_array_deg[mask] + hue_offset) % 360
    hsv[:, :, 0] = hue_array_deg / 360.0

    # ۲) تنظیم saturation
    hsv[mask, 1] = np.clip(hsv[mask, 1] * (1 + sat_adj / 100.0), 0, 1)

    # ۳) تنظیم value (یا روشنایی)
    hsv[mask, 2] = np.clip(hsv[mask, 2] * (1 + lum_adj / 100.0), 0, 1)

    # تبدیل مجدد به RGB
    rgb = hsv2rgb(hsv)
    output_image = img_as_ubyte(rgb)

    # ذخیره در پوشه‌ی static/processed
    output_filename = "skimage_" + os.path.basename(input_path)
    output_path = os.path.join("static/processed", output_filename)
    io.imsave(output_path, output_image)
    return output_path


def process_with_style_transfer(input_path, model_name='candy'):
    """
    تابع استایل ترنسفر نمونه. تغییری در آن نمی‌دهیم.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = torch.hub.load('pytorch/fast_neural_style', model_name).to(device)
    model.eval()

    image = Image.open(input_path).convert("RGB")
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.ToTensor(),
        transforms.Lambda(lambda x: x.mul(255))
    ])
    image_tensor = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        output = model(image_tensor)

    output = output.cpu().squeeze(0).div(255).clamp(0, 1)
    output_image = transforms.ToPILImage()(output)

    output_filename = "style_" + os.path.basename(input_path)
    output_path = os.path.join("static/processed", output_filename)
    output_image.save(output_path)

    return output_path


# ------------------ New Color Filters Functions ------------------

def adjust_temperature(image_path, factor):
    image = io.imread(image_path)
    if image.shape[2] == 4:
        image = image[:, :, :3]
    result = np.copy(image)
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            r, g, b = image[i, j]
            r = min(max(int(r * factor), 0), 255)
            b = min(max(int(b / factor), 0), 255)
            result[i, j] = [r, g, b]
    return result


def adjust_tint(image_path, red_factor, blue_factor):
    image = io.imread(image_path)
    if image.shape[2] == 4:
        image = image[:, :, :3]
    result = np.copy(image)
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            r, g, b = image[i, j]
            r = min(max(int(r * red_factor), 0), 255)
            b = min(max(int(b * blue_factor), 0), 255)
            result[i, j] = [r, g, b]
    return result


def save_image(image, output_path):
    output_image = img_as_ubyte(image)
    io.imsave(output_path, output_image)



def process_with_temperature_tint(input_path, temperature_factor, red_factor, blue_factor, vibrancy_factor=1.0, saturation_factor=1.0):
    image = io.imread(input_path)
    if image.shape[2] == 4:
        image = image[:, :, :3]

    # اعمال تغییرات رنگی
    image = image.astype(np.float32) / 255.0

    # Vibrancy
    image[:, :, 0] = np.clip(image[:, :, 0] * vibrancy_factor, 0, 1)
    image[:, :, 1] = np.clip(image[:, :, 1] * vibrancy_factor, 0, 1)
    image[:, :, 2] = np.clip(image[:, :, 2] * vibrancy_factor, 0, 1)

    # Color Saturation
    hsv = rgb2hsv(image)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation_factor, 0, 1)
    image = hsv2rgb(hsv)

    # Temperature
    image[:, :, 0] = np.clip(image[:, :, 0] * temperature_factor, 0, 1)
    image[:, :, 2] = np.clip(image[:, :, 2] / temperature_factor, 0, 1)

    # Tint
    image[:, :, 0] = np.clip(image[:, :, 0] * red_factor, 0, 1)
    image[:, :, 2] = np.clip(image[:, :, 2] * blue_factor, 0, 1)

    output_image = img_as_ubyte(image)

    # ذخیره تصویر
    output_filename = "temperature_" + os.path.basename(input_path)
    output_path = os.path.join("static/processed", output_filename)
    io.imsave(output_path, output_image)

    return output_path

# ------------------ New Light Filters Functions ------------------


def apply_dehaze(image, val):
    # val در بازه [-1, 1]؛ 0 یعنی بدون تغییر
    if abs(val) < 1e-3:
        return image
    # برای نواحی تاریک (کمتر از 0.5) تغییر ایجاد می‌کنیم
    mask = rgb2gray(image) < 0.5
    # اعمال تغییر به صورت additif؛ ضرایب را می‌توانید تغییر دهید
    result = image.copy()
    result[mask] = np.clip(result[mask] + val * 0.3, 0, 1)
    return result


def adjust_exposure(image, val):
    if abs(val) < 1e-3:
        return image
    gamma = 1 + val  # وقتی val مثبت شود تصویر تاریک‌تر، منفی شود روشن‌تر
    return exposure.adjust_gamma(image, gamma=gamma)


def adjust_brightness(image, val):
    if abs(val) < 1e-3:
        return image
    # تغییر additif
    return np.clip(image + val * 0.3, 0, 1)


def adjust_contrast(image, val):
    if abs(val) < 1e-3:
        return image
    # افزایش یا کاهش کنتراست بر اساس فاصله از میانگین
    mean = np.mean(image, axis=(0, 1), keepdims=True)
    return np.clip(mean + (image - mean) * (1 + val), 0, 1)


def adjust_highlights(image, val):
    if abs(val) < 1e-3:
        return image
    # فقط بر روی پیکسل‌های روشن (بالای 0.7) اعمال شود
    result = image.copy()
    mask = image > 0.7
    result[mask] = np.clip(result[mask] * (1 + val * 0.5), 0, 1)
    return result


def adjust_shadows(image, val):
    if abs(val) < 1e-3:
        return image
    # فقط بر روی پیکسل‌های تاریک (زیر 0.3)
    result = image.copy()
    mask = image < 0.3
    result[mask] = np.clip(result[mask] + val * 0.3, 0, 1)
    return result


def adjust_whites_blacks(image, white_val, black_val):
    # white_val و black_val در بازه [-1, 1]
    if abs(white_val) < 1e-3 and abs(black_val) < 1e-3:
        return image
    orig_min, orig_max = np.min(image), np.max(image)
    delta_black = black_val * 0.1
    delta_white = white_val * 0.1
    new_min = orig_min + delta_black
    new_max = orig_max - delta_white
    if new_max - new_min < 0.1:
        new_max = new_min + 0.1
    return exposure.rescale_intensity(image, in_range=(new_min, new_max))


def process_with_light_adjustments(input_path, dehaze_val, exposure_val, brightness_val, contrast_val,
                                   highlights_val, shadows_val, white_val, black_val):
    """
    در این نسخه، هر فیلتر به صورت زنجیره‌ای روی تصویر اصلی اعمال می‌شود.
    مقادیر اسلایدرها در بازه [-1, 1] هستند؛ 0 یعنی بدون تغییر.
    """
    image = img_as_float(io.imread(input_path))

    # اعمال فیلترها به ترتیب:
    image = apply_dehaze(image, dehaze_val)
    image = adjust_exposure(image, exposure_val)
    image = adjust_brightness(image, brightness_val)
    image = adjust_contrast(image, contrast_val)
    image = adjust_highlights(image, highlights_val)
    image = adjust_shadows(image, shadows_val)
    image = adjust_whites_blacks(image, white_val, black_val)

    image = np.clip(image, 0, 1)
    output_image = img_as_ubyte(image)
    output_filename = "light_" + os.path.basename(input_path)
    output_path = os.path.join("static/processed", output_filename)
    io.imsave(output_path, output_image)
    return output_path