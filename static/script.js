
let uploadedFile = null; // نام فایل آپلود شده (از پوشه uploads)

let globalImage = null; // تصویر تغییر داده شده تجمعی (از processed)

let currentPalette = "all"; // پالت رنگ فعلی

let baseImages = {}; // دیکشنری نگهدارندهٔ تصویر پایه برای هر پالت (مانند: baseImages["green"]، baseImages["blue"]، ...)

let debounceTimer = null;

let finalProcessedImage = null; // مسیر تصویر نهایی پردازش شده
let debounceTimerLight = null;

// Handle file upload
document.getElementById("uploadForm").addEventListener("submit", function(event) {
    event.preventDefault();

    let file = document.getElementById("imageUpload").files[0];

    if (!file) {
        alert("No file selected!");
        return;
    }

    let formData = new FormData();
    formData.append("file", file);

    fetch("/upload", { method: "POST", body: formData })
        .then(response => response.json())
        .then(data => {
            uploadedFile = data.image_id;

            // بعد از آپلود، تصویر پایه اولیه از سرور (base_image) را ذخیره میکنیم
            globalImage = data.base_image;

            baseImages["all"] = data.base_image; // برای پالت "all"

            currentPalette = "all";

            document.getElementById("uploadedImage").src = "/static/uploads/" + uploadedFile;

            document.getElementById("uploadedImage").style.display = "block";
        })
        .catch(error => console.error("Upload error:", error));
});

// Color palette selection using separate buttons
let colorButtons = document.getElementsByClassName("colorBtn");

for (let btn of colorButtons) {
    btn.addEventListener("click", function() {
        // Remove active class from all buttons
        for (let b of colorButtons) {
            b.classList.remove("active");
        }

        // Add active class to clicked button
        btn.classList.add("active");

        let newPalette = btn.getAttribute("data-color");

        // اگر پالت جدید انتخاب شده متفاوت از پالت فعلی است:
        if (newPalette !== currentPalette) {
            // تنظیم پایه پالت جدید: اگر برای آن پالت قبلاً تصویری ثبت نشده باشد،
            // از تصویر تغییر یافته جاری (globalImage) استفاده میکنیم.
            if (!baseImages[newPalette]) {
                baseImages[newPalette] = globalImage;
            }

            currentPalette = newPalette;

            // ارسال درخواست تغییرات برای پالت انتخابی جدید
            sendHSLUpdate();
        }
    });
}

// Debounced function to send HSL update (for cumulative adjustments)
function sendHSLUpdate() {
    if (!uploadedFile) {
        console.warn("No uploaded file yet!");
        return;
    }

    let hue = document.getElementById("hue").value;
    let saturation = document.getElementById("saturation").value;
    let luminance = document.getElementById("luminance").value;
    let payload = {
        hue: parseInt(hue),
        saturation: parseInt(saturation),
        luminance: parseInt(luminance),
        color: currentPalette
    };

    // برای پالت فعلی، اگر تصویر پایه برای آن وجود دارد، ارسال شود؛ در غیر این صورت از تصویر آپلود شده استفاده میکنیم
    if (baseImages[currentPalette]) {
        payload.base_image = baseImages[currentPalette];
    } else {
        payload.image_id = uploadedFile;
    }

    fetch("/apply_hsl", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
        .then(response => response.json())
        .then(data => {
    if (data.image_url) {
        // به روزرسانی تصویر نمایش داده شده
        document.getElementById("uploadedImage").src = data.image_url + "?t=" + new Date().getTime();
        // به روزرسانی تصویر پایه برای پالت فعلی
        baseImages[currentPalette] = data.base_image;
        // به روزرسانی تصویر تغییر یافته تجمعی (global image)
        globalImage = data.base_image;
        // به روزرسانی دکمه دانلود
        let downloadBtn = document.getElementById("downloadBtn");
        downloadBtn.style.display = "inline-block";
        downloadBtn.onclick = function() {
        let a = document.createElement('a');
        a.href = data.image_url;
        a.download = getFileNameFromUrl(data.image_url);
        a.click();
        }
        function getFileNameFromUrl(url) {
        return url.substring(url.lastIndexOf('/') + 1);
                }
    } else {
        console.error("Invalid response", data);
    }
})
        .catch(error => console.error("Error applying HSL changes:", error));
}

// Listen to slider input events with debounce (300ms delay)
document.getElementById("hue").addEventListener("input", function() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(sendHSLUpdate, 300);
});

document.getElementById("saturation").addEventListener("input", function() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(sendHSLUpdate, 300);
});

document.getElementById("luminance").addEventListener("input", function() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(sendHSLUpdate, 300);
});

// Reset button: revert to original uploaded image and clear all cumulative adjustments
document.getElementById("resetBtn").addEventListener("click", function() {
    if (uploadedFile) {
        currentPalette = "all";
        globalImage = baseImages["all"]; // بازگشت به تصویر پایه برای پالت all

        // پاکسازی baseImages به جز مقدار اولیه برای "all"
        baseImages = { "all": globalImage };

        document.getElementById("uploadedImage").src = "/static/uploads/" + uploadedFile;

        document.getElementById("hue").value = 0;
        document.getElementById("saturation").value = 0;
        document.getElementById("luminance").value = 0;
    }
});

// Tab switching logic
document.getElementById("tabHSL").addEventListener("click", function() {
    document.getElementById("hslControls").style.display = "block";
    document.getElementById("colorControls").style.display = "none";
    this.classList.add("active");
    document.getElementById("tabColor").classList.remove("active");
});

document.getElementById("tabColor").addEventListener("click", function() {
    document.getElementById("hslControls").style.display = "none";
    document.getElementById("colorControls").style.display = "block";
    this.classList.add("active");
    document.getElementById("tabHSL").classList.remove("active");
});

// Real-time color filter adjustments
let debounceTimerColor = null;

document.getElementById("temp").addEventListener("input", applyColorFilters);
document.getElementById("tint_red").addEventListener("input", applyColorFilters);
document.getElementById("tint_blue").addEventListener("input", applyColorFilters);
document.getElementById("vibrancy").addEventListener("input", applyColorFilters);
document.getElementById("sat_color").addEventListener("input", applyColorFilters);

function applyColorFilters() {
    clearTimeout(debounceTimerColor);
    debounceTimerColor = setTimeout(function() {
        let temperature = document.getElementById("temp").value;
        let redTint = document.getElementById("tint_red").value;
        let blueTint = document.getElementById("tint_blue").value;
        let vibrancy = document.getElementById("vibrancy").value;
        let saturation = document.getElementById("sat_color").value;

        let payload = {
            image_id: uploadedFile,
            temperature_factor: parseFloat(temperature),
            red_factor: parseFloat(redTint),
            blue_factor: parseFloat(blueTint),
            vibrancy_factor: parseFloat(vibrancy),
            saturation_factor: parseFloat(saturation)
        };

        fetch("/apply_temperature_tint", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
            .then(response => response.json())
            .then(data => {
                if (data.temperature_image_url) {
                    document.getElementById("uploadedImage").src = data.temperature_image_url + "?t=" + new Date().getTime();

                    // به روزرسانی مسیر تصویر نهایی پردازش شده
                    finalProcessedImage = data.temperature_image_url;

                    // به روزرسانی دکمه دانلود

                    let downloadBtn = document.getElementById("downloadBtn");
                    downloadBtn.style.display = "inline-block";
                    downloadBtn.onclick = function() {
                    let a = document.createElement('a');
                    a.href = finalProcessedImage;
                    a.download = getFileNameFromUrl(finalProcessedImage);
                    a.click();
                    };

                    // تابع برای استخراج نام فایل از URL
                    function getFileNameFromUrl(url) {
                    return url.substring(url.lastIndexOf('/') + 1);
                    }


                } else {
                    console.error("Invalid response", data);
                }
            })
            .catch(error => console.error("Error applying color filters:", error));
    }, 300); // تاخیر 300 میلی‌ثانیه
}

document.getElementById("resetColorBtn").addEventListener("click", function() {
    document.getElementById("temp").value = 1;
    document.getElementById("tint_red").value = 1;
    document.getElementById("tint_blue").value = 1;
    document.getElementById("vibrancy").value = 1;
    document.getElementById("sat_color").value = 1;

    // ارسال درخواست برای بازگرداندن تصویر به حالت پیش‌فرض
    fetch("/upload", { method: "POST", body: new FormData(document.getElementById("uploadForm")) })
        .then(response => response.json())
        .then(data => {
            uploadedFile = data.image_id;
            document.getElementById("uploadedImage").src = "/static/uploads/" + uploadedFile;
        })
        .catch(error => console.error("Error resetting image:", error));

    // برای اعمال تغییرات پس از ریست، یک بار درخواست ارسال شود
    applyColorFilters();
});
document.getElementById("tabLight").addEventListener("click", function() {
    document.getElementById("hslControls").style.display = "none";
    document.getElementById("colorControls").style.display = "none";
    document.getElementById("lightControls").style.display = "block";
    this.classList.add("active");
    document.getElementById("tabHSL").classList.remove("active");
    document.getElementById("tabColor").classList.remove("active");
});

//------------------------------------applyLightFilters--------------------------
function applyLightFilters() {
    clearTimeout(debounceTimerLight);
    debounceTimerLight = setTimeout(function() {
        let payload = {
            image_id: uploadedFile,
            dehaze: parseFloat(document.getElementById("dehaze").value),
            exposure: parseFloat(document.getElementById("exposure").value),
            brightness: parseFloat(document.getElementById("brightness").value),
            contrast: parseFloat(document.getElementById("contrast").value),
            highlights: parseFloat(document.getElementById("highlights").value),
            shadows: parseFloat(document.getElementById("shadows").value),
            whites: parseFloat(document.getElementById("whites").value),
            blacks: parseFloat(document.getElementById("blacks").value)
        };

        fetch("/apply_light", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            if (data.light_image_url) {
                document.getElementById("uploadedImage").src = data.light_image_url + "?t=" + new Date().getTime();
                finalProcessedImage = data.light_image_url;
                updateDownloadButton();
            } else {
                console.error("Invalid response", data);
            }
        })
        .catch(error => console.error("Error applying light filters:", error));
    }, 300);
}

function updateDownloadButton() {
    let downloadBtn = document.getElementById("downloadLightBtn");
    downloadBtn.style.display = "inline-block";
    downloadBtn.onclick = function() {
        if (finalProcessedImage) {
            window.open(finalProcessedImage, "_blank");
        }
    };
}

document.getElementById("dehaze").addEventListener("input", applyLightFilters);
document.getElementById("exposure").addEventListener("input", applyLightFilters);
document.getElementById("brightness").addEventListener("input", applyLightFilters);
document.getElementById("contrast").addEventListener("input", applyLightFilters);
document.getElementById("highlights").addEventListener("input", applyLightFilters);
document.getElementById("shadows").addEventListener("input", applyLightFilters);
document.getElementById("whites").addEventListener("input", applyLightFilters);
document.getElementById("blacks").addEventListener("input", applyLightFilters);

// Reset Color Filters button
document.getElementById("resetColorBtn").addEventListener("click", function() {
    document.getElementById("temp").value = 1;
    document.getElementById("tint_red").value = 1;
    document.getElementById("tint_blue").value = 1;
    document.getElementById("vibrancy").value = 1;
    document.getElementById("sat_color").value = 1;

    document.getElementById("resetLightBtn").addEventListener("click", function() {
    // بازگردانی مقادیر پیش‌فرض برای اسلایدرهای Light
    document.getElementById("dehaze").value = 1;
    document.getElementById("exposure").value = 1;
    document.getElementById("brightness").value = 1;
    document.getElementById("contrast").value = 1;
    document.getElementById("highlights").value = 1;
    document.getElementById("shadows").value = 1;
    document.getElementById("whites").value = 98;
    document.getElementById("blacks").value = 2;

    // فراخوانی تابع برای اعمال تغییرات جدید
    applyLightFilters();
});

    fetch("/upload", { method: "POST", body: new FormData(document.getElementById("uploadForm")) })
        .then(response => response.json())
        .then(data => {
            uploadedFile = data.image_id;
            document.getElementById("uploadedImage").src = "/static/uploads/" + uploadedFile;
        })
        .catch(error => console.error("Error resetting image:", error));

    applyLightFilters();
});