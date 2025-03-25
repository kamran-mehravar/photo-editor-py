import os
import numpy as np
from skimage import io, filters
from skimage.exposure import exposure
from skimage.util import img_as_ubyte, img_as_float
from skimage.color import rgb2hsv, hsv2rgb
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
def process_with_light_adjustments(input_path, dehaze, exposure_val, brightness, contrast, highlights, shadows, whites,
                                   blacks):
    image = img_as_float(io.imread(input_path))

    image = apply_dehaze(image, dehaze)
    image = adjust_exposure(image, 'gamma', exposure_val)
    image = adjust_brightness(image, 'multiply', brightness)
    image = adjust_contrast(image, contrast)
    image = adjust_highlights_shadows(image, highlights, shadows)
    image = adjust_whites_blacks(image, whites, blacks)

    image = np.clip(image, 0, 1)
    output_image = img_as_ubyte(image)
    output_filename = "light_" + os.path.basename(input_path)
    output_path = os.path.join("static/processed", output_filename)
    io.imsave(output_path, output_image)
    return output_path


def apply_dehaze(image, intensity):
    # استفاده از contrast stretching با استفاده از percentiles (مقدار intensity در اینجا به‌طور مستقیم اعمال نمی‌شود)
    p_low, p_high = np.percentile(image, (2, 98))
    return exposure.rescale_intensity(image, in_range=(p_low, p_high))


def adjust_exposure(image, method, intensity):
    if method == 'gamma':
        return exposure.adjust_gamma(image, intensity)
    elif method == 'log':
        return exposure.adjust_log(image)
    elif method == 'sigmoid':
        return exposure.adjust_sigmoid(image)
    else:
        return exposure.adjust_gamma(image, intensity)


def adjust_brightness(image, method, intensity):
    # تنظیم روشنایی به صورت ضرب در مقدار intensity
    return np.clip(image * intensity, 0, 1)


def adjust_contrast(image, intensity):
    # اعمال contrast stretching و ترکیب با تصویر اصلی بر اساس مقدار intensity
    p2, p98 = np.percentile(image, (2, 98))
    contrast_stretched = exposure.rescale_intensity(image, in_range=(p2, p98))
    return image * (1 - intensity) + contrast_stretched * intensity


def adjust_highlights_shadows(image, highlights, shadows):
    # تنظیم highlights با cutoff بالا و shadows با cutoff پایین
    highlight_adj = exposure.adjust_sigmoid(image, cutoff=0.8, gain=highlights)
    shadow_adj = exposure.adjust_sigmoid(image, cutoff=0.3, gain=shadows)
    return (highlight_adj + shadow_adj) / 2


def adjust_whites_blacks(image, whites, blacks):
    # استفاده از مقادیر درصدی برای تعیین نقاط سیاه و سفید
    low = np.percentile(image, blacks)
    high = np.percentile(image, whites)
    return exposure.rescale_intensity(image, in_range=(low, high))