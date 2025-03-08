let selectedColor = null;
let uploadedFile = null;

// تعریف رنگ‌ها
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

// انتخاب رنگ از پالت
document.querySelectorAll(".color-box").forEach(box => {
    box.addEventListener("click", function() {
        selectedColor = this.getAttribute("data-color");
        console.log("🎨 Selected Color:", selectedColor);
        applyHSL();
    });
});

// آپلود فایل
document.getElementById('uploadForm').addEventListener('submit', function(event) {
    event.preventDefault();

    let formData = new FormData();
    let fileInput = document.getElementById('imageUpload').files[0];

    if (!fileInput) {
        alert("❌ Please chose a file");
        return;
    }

    formData.append("file", fileInput);

    fetch("/upload", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert("❌ Error: " + data.error);
        } else {
            console.log("✅ Image uploaded:", data);
            uploadedFile = data.image_id;
            document.getElementById("uploadedImage").src = "/static/uploads/" + uploadedFile;
            document.getElementById("uploadedImage").style.display = "block";
        }
    })
    .catch(error => console.error("❌ Upload error:", error));
});

// اعمال HSL
function applyHSL() {
    if (!uploadedFile || !selectedColor) return;

    let hue = parseInt($("#hue").val());
    let saturation = parseInt($("#saturation").val());
    let luminance = parseInt($("#luminance").val());

    $.ajax({
        url: "/apply_hsl",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({
            image_id: uploadedFile,
            hue: hue,
            saturation: saturation,
            luminance: luminance,
            color: selectedColor
        }),
        success: function(response) {
            console.log("✅ Processed Image:", response.image_url);
            $("#uploadedImage").attr("src", response.image_url + "?t=" + new Date().getTime()).fadeIn();
        },
        error: function(xhr) {
            console.error("❌ Processing error:", xhr.responseText);
            alert("There is a Problem during the process!");
        }
    });
}


// افزودن رویداد به اسلایدرهای HSL
document.getElementById("hue").addEventListener("input", applyHSL);
document.getElementById("saturation").addEventListener("input", applyHSL);
document.getElementById("luminance").addEventListener("input", applyHSL);
