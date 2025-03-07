let selectedColor = null;  // مقدار رنگ انتخاب‌شده از پالت
let selectedHueRange = null;  // محدوده رنگی انتخاب‌شده
let uploadedFile = null;  // شناسه تصویر آپلود شده

// تعریف محدوده HUE برای رنگ‌های مختلف (در بازه 360 درجه HSL)
const colorRanges = {
    "red": [0, 30],
    "orange": [30, 60],
    "yellow": [60, 90],
    "green": [90, 150],
    "cyan": [150, 210],
    "blue": [210, 270],
    "purple": [270, 330],
    "pink": [330, 360]
};

// افزودن رویداد کلیک برای انتخاب رنگ از پالت
document.querySelectorAll(".color-box").forEach(box => {
    box.addEventListener("click", function() {
        selectedColor = getComputedStyle(this).backgroundColor;
        selectedHueRange = getColorRange(selectedColor);
        console.log("🎨 Selected Color:", selectedColor, "Hue Range:", selectedHueRange);

        // فعال کردن اسلایدرهای HSL برای رنگ انتخابی
        document.getElementById("hue").disabled = false;
        document.getElementById("saturation").disabled = false;
        document.getElementById("luminance").disabled = false;

        applyHSL();  // بعد از انتخاب رنگ، اعمال تغییرات HSL
    });
});

// تابع تشخیص محدوده رنگی بر اساس RGB
function getColorRange(rgb) {
    let rgbValues = rgb.match(/\d+/g);
    if (!rgbValues) return null;

    let [hue] = rgbToHsl(parseInt(rgbValues[0]), parseInt(rgbValues[1]), parseInt(rgbValues[2]));

    for (const [color, range] of Object.entries(colorRanges)) {
        if (hue >= range[0] && hue <= range[1]) {
            return range;  // بازه HUE متناظر با رنگ را برگردان
        }
    }
    return null;  // اگر رنگ یافت نشد، مقدار `null` برگردان
}

// تابع تبدیل RGB به HSL
function rgbToHsl(r, g, b) {
    r /= 255, g /= 255, b /= 255;
    let max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h, s, l = (max + min) / 2;

    if (max == min) {
        h = s = 0;
    } else {
        let d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        switch (max) {
            case r: h = (g - b) / d + (g < b ? 6 : 0); break;
            case g: h = (b - r) / d + 2; break;
            case b: h = (r - g) / d + 4; break;
        }
        h = Math.round(h * 60);
    }
    return [h, Math.round(s * 100), Math.round(l * 100)];
}

// تابع `applyHSL()` برای اعمال تغییرات HSL
function applyHSL() {
    if (!uploadedFile) {
        console.log("❌ No image uploaded, skipping applyHSL.");
        return;
    }

    let hueChange = parseInt(document.getElementById("hue").value);
    let saturationChange = parseInt(document.getElementById("saturation").value);
    let luminanceChange = parseInt(document.getElementById("luminance").value);

    if (!selectedHueRange) {
        console.log("⚠ No color selected, applying changes globally.");
    }

    // ارسال درخواست به سرور
    $.ajax({
        url: "/apply_hsl",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({
            image_id: uploadedFile,
            hue: hueChange,
            saturation: saturationChange,
            luminance: luminanceChange,
            hue_range: selectedHueRange  // ارسال بازه رنگ انتخاب‌شده به سرور
        }),
        success: function(response) {
            let timestamp = new Date().getTime();
            $("#resultImage").attr("src", response.image_url + "?t=" + timestamp);
            $("#downloadBtn").show().off("click").on("click", function() {
                window.location.href = response.download_url;
            });

            console.log("✅ HSL applied to selected color range:", selectedHueRange);
        },
        error: function(xhr) {
            alert("Error applying HSL: " + xhr.responseText);
        }
    });
}

// افزودن رویداد به اسلایدرهای HSL برای اجرای بلادرنگ تغییرات
document.getElementById("hue").addEventListener("input", applyHSL);
document.getElementById("saturation").addEventListener("input", applyHSL);
document.getElementById("luminance").addEventListener("input", applyHSL);

// تابع آپلود فایل
function uploadFile() {
    let file = document.getElementById("fileInput").files[0];
    if (!file) {
        alert("No file selected!");
        return;
    }

    let formData = new FormData();
    formData.append("file", file);

    $.ajax({
        url: "/upload",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            if (response.image_id) {
                uploadedFile = response.image_id;
                let imageUrl = `/static/uploads/${uploadedFile}`;

                // نمایش تصویر آپلود شده
                $("#resultImage").attr("src", imageUrl);
                $("#resultImage").show();

                console.log("✅ Image uploaded successfully:", uploadedFile);

                // اعمال تغییرات HSL پس از آپلود اولیه
                applyHSL();
            } else {
                alert("Error: No image ID received from server.");
            }
        },
        error: function(xhr) {
            alert("Error uploading file: " + xhr.responseText);
        }
    });
}
