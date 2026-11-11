(() => {
  const apiBase = (window.CONVERTER_API_URL || "").replace(/\/$/, "");
  const input = document.getElementById("worldFile");
  const dropzone = document.getElementById("dropzone");
  const fileRow = document.getElementById("fileRow");
  const fileName = document.getElementById("fileName");
  const fileSize = document.getElementById("fileSize");
  const convertButton = document.getElementById("convertButton");
  const status = document.getElementById("status");
  const progressWrap = document.getElementById("progressWrap");
  const progressText = document.getElementById("progressText");
  const progressPercent = document.getElementById("progressPercent");
  const progressFill = document.getElementById("progressFill");
  let selectedFile = null;

  const formatBytes = (bytes) => bytes < 1024 * 1024
    ? (bytes / 1024).toFixed(0) + " KB"
    : (bytes / 1024 / 1024).toFixed(1) + " MB";

  function setStatus(message, kind = "") {
    status.textContent = message;
    status.className = "status " + kind;
  }
  function chooseFile(file) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".zip")) {
      setStatus("Please choose a .zip containing your Java world.", "error");
      return;
    }
    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = formatBytes(file.size);
    fileRow.hidden = false;
    dropzone.hidden = true;
    convertButton.disabled = !apiBase;
    setStatus(apiBase ? "Ready to convert. Your original ZIP will not be changed." : "The website is ready, but its conversion server has not been connected yet.");
  }
  function clearFile() {
    selectedFile = null;
    input.value = "";
    fileRow.hidden = true;
    dropzone.hidden = false;
    convertButton.disabled = true;
    progressWrap.hidden = true;
  }
  input.addEventListener("change", () => chooseFile(input.files[0]));
  document.getElementById("removeFile").addEventListener("click", clearFile);
  ["dragenter", "dragover"].forEach(name => dropzone.addEventListener(name, e => {
    e.preventDefault(); dropzone.classList.add("dragover");
  }));
  ["dragleave", "drop"].forEach(name => dropzone.addEventListener(name, e => {
    e.preventDefault(); dropzone.classList.remove("dragover");
  }));
  dropzone.addEventListener("drop", e => chooseFile(e.dataTransfer.files[0]));

  async function checkServer() {
    if (!apiBase) {
      setStatus("Website interface loaded. Backend connection is not configured yet.");
      return;
    }
    try {
      const response = await fetch(apiBase + "/health");
      if (!response.ok) throw new Error("Server returned " + response.status);
      const data = await response.json();
      setStatus(data.converter_ready ? "Converter online · Ready for a Java world." : "API online, but the conversion engine is not installed.", data.converter_ready ? "success" : "error");
    } catch (error) {
      setStatus("Could not reach the conversion server. Check the API URL and server status.", "error");
    }
  }

  convertButton.addEventListener("click", () => {
    if (!selectedFile || !apiBase) return;
    convertButton.disabled = true;
    progressWrap.hidden = false;
    progressText.textContent = "Uploading world…";
    progressPercent.textContent = "0%";
    progressFill.style.width = "0%";
    const form = new FormData();
    form.append("world", selectedFile);
    const request = new XMLHttpRequest();
    request.open("POST", apiBase + "/convert/java-to-bedrock");
    request.responseType = "blob";
    request.upload.onprogress = event => {
      if (!event.lengthComputable) return;
      const percent = Math.round(event.loaded / event.total * 100);
      progressPercent.textContent = percent + "%";
      progressFill.style.width = percent + "%";
      if (percent >= 100) progressText.textContent = "Converting world on server…";
    };
    request.onload = () => {
      if (request.status >= 200 && request.status < 300) {
        const blob = request.response;
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = selectedFile.name.replace(/\.zip$/i, "") + "-Bedrock.mcworld";
        document.body.appendChild(link); link.click(); link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 30000);
        progressPercent.textContent = "100%";
        progressFill.style.width = "100%";
        progressText.textContent = "Conversion complete";
        setStatus("Your Bedrock world download is ready. Import the .mcworld file into Minecraft.", "success");
      } else {
        request.response.text().then(text => {
          let message = "Conversion failed. Please check that this ZIP contains a valid Java world.";
          try { message = JSON.parse(text).detail || message; } catch {}
          setStatus(message, "error");
        });
      }
      convertButton.disabled = false;
    };
    request.onerror = () => {
      setStatus("Network error while contacting the conversion server.", "error");
      convertButton.disabled = false;
    };
    request.onabort = () => {
      setStatus("Upload cancelled.", "error");
      convertButton.disabled = false;
    };
    request.send(form);
  });
  checkServer();
})();