const fileInput = document.getElementById("qrFile");
const preview = document.getElementById("preview");
const fileLabel = document.getElementById("fileLabel");

if (fileInput) {
    fileInput.addEventListener("change", function () {
        const file = this.files[0];

        if (!file) {
            preview.hidden = true;
            fileLabel.textContent = "Click or drag a PNG / JPG / JPEG image here";
            return;
        }

        if (!file.type.startsWith("image/")) {
            alert("Please select a PNG, JPG or JPEG image.");
            this.value = "";
            return;
        }

        const reader = new FileReader();

        reader.onload = function (e) {
            preview.src = e.target.result;
            preview.hidden = false;
            fileLabel.textContent = file.name;
        };

        reader.readAsDataURL(file);
    });
}


// Camera
const startCam = document.getElementById("startCam");
const captureBtn = document.getElementById("captureBtn");
const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const cameraMsg = document.getElementById("cameraMsg");

let stream = null;

if (startCam) {
    startCam.addEventListener("click", async function () {
        try {
            stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: "environment" },
                audio: false
            });

            video.srcObject = stream;
            video.hidden = false;
            captureBtn.hidden = false;
            cameraMsg.textContent = "Camera started. Hold the QR code in front of the camera.";
        } catch (error) {
            cameraMsg.textContent =
                "Camera permission was denied or camera is unavailable.";
        }
    });
}


if (captureBtn) {
    captureBtn.addEventListener("click", function () {
        if (!video.videoWidth || !video.videoHeight) {
            cameraMsg.textContent = "Camera is not ready yet.";
            return;
        }

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const context = canvas.getContext("2d");
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(function (blob) {
            const formData = new FormData();
            formData.append("qr_image", blob, "camera_qr.png");

            cameraMsg.textContent = "Analyzing QR code...";

            fetch("/analyze", {
                method: "POST",
                body: formData
            })
            .then(function (response) {
                return response.text();
            })
            .then(function (html) {
                document.open();
                document.write(html);
                document.close();
            })
            .catch(function () {
                cameraMsg.textContent = "Something went wrong. Please try again.";
            });
        }, "image/png");
    });
}
