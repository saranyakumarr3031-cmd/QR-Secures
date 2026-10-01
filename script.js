// QR-Secure front-end helpers (no libraries needed)

// ---- Animate the risk-score bars on the result page ----
document.querySelectorAll(".meter-fill").forEach(function (bar) {
  var score = Math.min(100, Number(bar.dataset.score) || 0);
  setTimeout(function () { bar.style.width = Math.max(score, 3) + "%"; }, 150);
});

// ---- Upload box: file name, preview and drag & drop ----
var fileInput = document.getElementById("qrFile");
var dropzone = document.getElementById("dropzone");
var fileLabel = document.getElementById("fileLabel");
var preview = document.getElementById("preview");
var uploadForm = document.getElementById("uploadForm");

function showFile() {
  if (!fileInput.files.length) { return; }
  var file = fileInput.files[0];
  fileLabel.textContent = "Selected: " + file.name;
  preview.src = URL.createObjectURL(file);
  preview.hidden = false;
}

if (fileInput) {
  fileInput.addEventListener("change", showFile);

  ["dragenter", "dragover"].forEach(function (name) {
    dropzone.addEventListener(name, function (e) { e.preventDefault(); dropzone.classList.add("drag"); });
  });
  ["dragleave", "drop"].forEach(function (name) {
    dropzone.addEventListener(name, function (e) { e.preventDefault(); dropzone.classList.remove("drag"); });
  });
  dropzone.addEventListener("drop", function (e) {
    if (e.dataTransfer.files.length) { fileInput.files = e.dataTransfer.files; showFile(); }
  });

  uploadForm.addEventListener("submit", function (e) {
    if (!fileInput.files.length) {
      e.preventDefault();
      fileLabel.textContent = "Please choose a QR image first!";
    }
  });
}

// ---- Webcam scan: capture one frame and send it to the server like an upload ----
var startBtn = document.getElementById("startCam");
var captureBtn = document.getElementById("captureBtn");
var video = document.getElementById("video");
var canvas = document.getElementById("canvas");
var cameraMsg = document.getElementById("cameraMsg");
var stream = null;

if (startBtn) {
  startBtn.addEventListener("click", function () {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      cameraMsg.textContent = "Camera is not supported in this browser. Please use Upload.";
      return;
    }
    navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
      .then(function (s) {
        stream = s;
        video.srcObject = s;
        video.hidden = false;
        captureBtn.hidden = false;
        startBtn.hidden = true;
        cameraMsg.textContent = "";
      })
      .catch(function () {
        cameraMsg.textContent = "Could not access the camera (permission denied or no camera). Please use Upload.";
      });
  });

  captureBtn.addEventListener("click", function () {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    canvas.toBlob(function (blob) {
      var file = new File([blob], "scan.png", { type: "image/png" });
      var data = new DataTransfer();
      data.items.add(file);
      fileInput.files = data.files;
      if (stream) { stream.getTracks().forEach(function (t) { t.stop(); }); }
      uploadForm.submit();
    }, "image/png");
  });
}
