const fileInput = document.getElementById("qrFile");
const preview = document.getElementById("preview");
const fileLabel = document.getElementById("fileLabel");


// =========================
// IMAGE UPLOAD PREVIEW
// =========================

if (fileInput) {
    fileInput.addEventListener("change", function () {
        const file = this.files[0];

        if (!file) {
            preview.hidden = true;
            fileLabel.textContent =
                "Click or drag a PNG / JPG / JPEG image here";
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


// =========================
// CAMERA
// =========================

const startCam = document.getElementById("startCam");
const captureBtn = document.getElementById("captureBtn");
const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const cameraMsg = document.getElementById("cameraMsg");

let stream = null;


// START CAMERA
if (startCam) {
    startCam.addEventListener("click", async function () {

        try {

            if (!navigator.mediaDevices ||
                !navigator.mediaDevices.getUserMedia) {

                cameraMsg.textContent =
                    "Camera is not supported by this browser.";

                return;
            }

            cameraMsg.textContent = "Starting camera...";

            stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: {
                        ideal: "environment"
                    }
                },
                audio: false
            });

            video.srcObject = stream;

            video.hidden = false;
            captureBtn.hidden = false;

            await video.play();

            cameraMsg.textContent =
                "Camera ready. Place the QR code in front of the camera.";

        } catch (error) {

            console.error("Camera error:", error);

            cameraMsg.textContent =
                "Camera permission was denied or camera is unavailable.";
        }
    });
}


// CAPTURE QR
if (captureBtn) {

    captureBtn.addEventListener("click", function () {

        if (!stream) {
            cameraMsg.textContent =
                "Please start the camera first.";
            return;
        }

        if (!video.videoWidth || !video.videoHeight) {

            cameraMsg.textContent =
                "Camera is not ready yet. Please wait a moment.";

            return;
        }

        cameraMsg.textContent =
            "Capturing QR code...";

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const context = canvas.getContext("2d");

        context.drawImage(
            video,
            0,
            0,
            canvas.width,
            canvas.height
        );

        canvas.toBlob(async function (blob) {

            if (!blob) {

                cameraMsg.textContent =
                    "Could not capture the image.";

                return;
            }

            cameraMsg.textContent =
                "Analyzing QR code...";

            const formData = new FormData();

            formData.append(
                "qr_image",
                blob,
                "camera_qr.png"
            );

            try {

                const response = await fetch(
                    "/analyze",
                    {
                        method: "POST",
                        body: formData
                    }
                );

                if (!response.ok) {
                    throw new Error(
                        "Server returned " + response.status
                    );
                }

                const html = await response.text();

                // Stop camera
                if (stream) {
                    stream.getTracks().forEach(
                        track => track.stop()
                    );
                }

                document.open();
                document.write(html);
                document.close();

            } catch (error) {

                console.error("Capture error:", error);

                cameraMsg.textContent =
                    "Analysis failed. Please try again.";
            }

        }, "image/png");
    });
}
