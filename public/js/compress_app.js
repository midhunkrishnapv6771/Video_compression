/**
 * compress_app.js - AptiTalent Tutor Video Compressor Frontend Logic
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const browseBtn = document.getElementById("browseBtn");
  const selectedFileBar = document.getElementById("selectedFileBar");
  const fileName = document.getElementById("fileName");
  const fileSize = document.getElementById("fileSize");
  const removeFileBtn = document.getElementById("removeFileBtn");
  const compressBtn = document.getElementById("compressBtn");
  
  const uploadCard = document.getElementById("uploadCard");
  const progressCard = document.getElementById("progressCard");
  const progressFill = document.getElementById("progressFill");
  const progressStatus = document.getElementById("progressStatus");
  const progressPct = document.getElementById("progressPct");
  
  const successCard = document.getElementById("successCard");
  const resSavingsPct = document.getElementById("resSavingsPct");
  const resSavingsMb = document.getElementById("resSavingsMb");
  const resPreset = document.getElementById("resPreset");
  const resOrigSize = document.getElementById("resOrigSize");
  const resCompressedSize = document.getElementById("resCompressedSize");
  const resOutputPath = document.getElementById("resOutputPath");
  const openFolderBtn = document.getElementById("openFolderBtn");
  const resetBtn = document.getElementById("resetBtn");
  
  const errorCard = document.getElementById("errorCard");
  const errorMessage = document.getElementById("errorMessage");
  const errorResetBtn = document.getElementById("errorResetBtn");
  
  const presetCards = document.querySelectorAll(".preset-card");
  const customConfigToggle = document.getElementById("customConfigToggle");
  const customConfigPanel = document.getElementById("customConfigPanel");
  const customResolution = document.getElementById("customResolution");
  const customFps = document.getElementById("customFps");
  const customCrf = document.getElementById("customCrf");
  const customBitrate = document.getElementById("customBitrate");
  const codecDropdownBtn = document.getElementById("codecDropdownBtn");
  const codecDropdownMenu = document.getElementById("codecDropdownMenu");
  const selectedCodecText = document.getElementById("selectedCodecText");
  const codecRadios = document.querySelectorAll("input[name='codec']");
  
  let selectedFile = null;
  let selectedPreset = "balanced";
  let useCustomConfig = false;
  let selectedCodec = "h264";

  // Preset Selection
  presetCards.forEach(card => {
    card.addEventListener("click", () => {
      presetCards.forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      selectedPreset = card.getAttribute("data-preset");
    });
  });

  // Custom Config Toggle
  customConfigToggle.addEventListener("change", (e) => {
    useCustomConfig = e.target.checked;
    customConfigPanel.style.display = useCustomConfig ? "grid" : "none";
    
    // Disable preset cards when using custom config
    presetCards.forEach(card => {
      card.style.opacity = useCustomConfig ? "0.5" : "1";
      card.style.pointerEvents = useCustomConfig ? "none" : "auto";
    });
  });

  // Codec Selection
  if (codecDropdownBtn) {
    codecDropdownBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const isHidden = codecDropdownMenu.style.display === "none";
      codecDropdownMenu.style.display = isHidden ? "block" : "none";
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", (e) => {
      if (!codecDropdownBtn.contains(e.target) && !codecDropdownMenu.contains(e.target)) {
        codecDropdownMenu.style.display = "none";
      }
    });
  }

  codecRadios.forEach(radio => {
    radio.addEventListener("change", (e) => {
      selectedCodec = e.target.value;
      const codecLabels = {
        "auto": "Auto",
        "av1": "AV1", 
        "hevc": "HEVC",
        "h264": "H.264"
      };
      selectedCodecText.textContent = `Primary Codec: ${codecLabels[selectedCodec]}`;
      codecDropdownMenu.style.display = "none";
    });
  });

  // File Choice Handlers
  browseBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    fileInput.click();
  });
  
  dropzone.addEventListener("click", () => {
    fileInput.click();
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  });

  // Drag and Drop
  ["dragenter", "dragover"].forEach(evt => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add("drag-over");
    });
  });

  ["dragleave", "drop"].forEach(evt => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("drag-over");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
    if (files && files[0]) {
      handleFileSelected(files[0]);
    }
  });

  function handleFileSelected(file) {
    selectedFile = file;
    fileName.textContent = file.name;
    const mb = (file.size / (1024 * 1024)).toFixed(2);
    fileSize.textContent = `${mb} MB`;
    selectedFileBar.style.display = "flex";
    compressBtn.removeAttribute("disabled");
  }

  removeFileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    clearSelectedFile();
  });

  function clearSelectedFile() {
    selectedFile = null;
    fileInput.value = "";
    selectedFileBar.style.display = "none";
    compressBtn.setAttribute("disabled", "true");
  }

  // Compress Trigger
  compressBtn.addEventListener("click", async () => {
    if (!selectedFile) return;

    // Show Progress
    uploadCard.style.display = "none";
    progressCard.style.display = "block";
    successCard.style.display = "none";
    errorCard.style.display = "none";
    
    updateProgress(10, "Uploading video to local encoder server...");

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("codec", selectedCodec);
    
    if (useCustomConfig) {
      formData.append("quality", "balanced"); // Use balanced as base for custom
      formData.append("custom_resolution", customResolution.value || "");
      formData.append("custom_fps", customFps.value || "");
      formData.append("custom_crf", customCrf.value || "");
      formData.append("custom_bitrate", customBitrate.value || "");
    } else {
      formData.append("quality", selectedPreset);
    }

    try {
      updateProgress(25, "Encoding video with selected profile and codec...");
      const response = await fetch("/api/compress", {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({ detail: "Server error" }));
        throw new Error(errJson.detail || "Compression failed");
      }

      const data = await response.json();
      if (data.success && data.result) {
        updateProgress(100, "Done!");
        showSuccess(data.result);
      } else {
        throw new Error(data.detail || "Compression failed");
      }
    } catch (err) {
      showError(err.message);
    }
  });

  function updateProgress(pct, msg) {
    progressFill.style.width = `${pct}%`;
    progressPct.textContent = `${pct}%`;
    progressStatus.textContent = msg;
  }

  function showSuccess(res) {
    progressCard.style.display = "none";
    successCard.style.display = "block";

    resSavingsPct.textContent = `${res.reduction_pct}%`;
    const savedMb = (res.orig_mb - res.output_mb).toFixed(2);
    resSavingsMb.textContent = `Saved ${savedMb} MB of bandwidth`;

    resPreset.textContent = `${res.preset} (${res.primary_codec ? res.primary_codec.toUpperCase() : ""})`;
    resOrigSize.textContent = `${res.orig_mb} MB`;
    resCompressedSize.textContent = `${res.output_mb} MB`;
    resOutputPath.textContent = res.output_path;
  }

  function showError(msg) {
    progressCard.style.display = "none";
    errorCard.style.display = "block";
    errorMessage.textContent = msg;
  }

  // Folder Open & Reset Handlers
  openFolderBtn.addEventListener("click", async () => {
    try {
      await fetch("/api/open-folder");
    } catch (e) {
      console.error(e);
    }
  });

  resetBtn.addEventListener("click", resetAll);
  errorResetBtn.addEventListener("click", resetAll);

  function resetAll() {
    clearSelectedFile();
    uploadCard.style.display = "block";
    progressCard.style.display = "none";
    successCard.style.display = "none";
    errorCard.style.display = "none";
  }

  // Health Check
  fetch("/api/status")
    .then(r => r.json())
    .then(d => {
      const pill = document.getElementById("statusPill");
      const txt = document.getElementById("statusText");
      if (d.status === "online" && d.ffmpeg) {
        pill.className = "status-pill online";
        txt.textContent = "Server & FFmpeg Online";
      } else {
        pill.className = "status-pill offline";
        txt.textContent = "FFmpeg Missing";
      }
    })
    .catch(() => {
      const pill = document.getElementById("statusPill");
      const txt = document.getElementById("statusText");
      pill.className = "status-pill offline";
      txt.textContent = "Server Offline";
    });
});
