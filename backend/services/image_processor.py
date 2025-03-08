import subprocess
import os

OUTPUT_STORAGE = "backend/static/processed"


def process_with_gimp(input_path, hue, saturation, luminance, color):
    output_filename = os.path.basename(input_path)  # گرفتن نام فایل بدون مسیر
    output_path = os.path.join("backend/static/processed", output_filename)

    # اجرای GIMP برای پردازش
    command = f"gimp -i -b '(batch-hsl \"{input_path}\" \"{output_path}\" {hue} {saturation} {luminance} {color})' -b '(gimp-quit 0)'"
    os.system(command)

    if not os.path.exists(output_path):
        raise FileNotFoundError(f"Error: Processed file not found at {output_path}")


    gimp_script = f"""
    (define (apply-hsl image)
        (let* ((drawable (car (gimp-image-get-active-layer image))))
            (gimp-hue-saturation drawable {color} {hue} {saturation} {luminance})
            (gimp-file-save RUN-NONINTERACTIVE image drawable "{output_path}" "{output_path}")
            (gimp-image-delete image)))
    (let ((image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}"))))
        (apply-hsl image))
    """

    subprocess.run(["gimp", "-i", "-b", gimp_script, "-b", "(gimp-quit 0)"], stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE)

    return output_path
