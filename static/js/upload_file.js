const output = document.getElementById('output');
  const progressBar = document.getElementById('progressBar');
  const fileInput = document.getElementById('file');
  const pathInput = document.getElementById('path');
  const submitBtn = document.getElementById('submitBtn');
  const serverResp = document.getElementById('server-resp');

  // --- Toast notification ---
  function showToast(message, isError = false) {
    const toast = document.createElement('div');
    toast.className = 'toast ' + (isError ? 'error' : 'success');
    toast.textContent = message;
    document.body.appendChild(toast);

    // trigger animation
    setTimeout(() => toast.classList.add('show'), 10);

    // auto-remove after 5s
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, 5000);
  }

  // Intercept form submit
  document.getElementById('uploadForm').addEventListener('submit', function(e) {
    e.preventDefault(); // prevent full page reload
    uploadWithXHR();
  });

  function uploadWithXHR(){
    const files = fileInput.files;
    if (!files || files.length === 0) {
      showToast('Please choose a file first.', true);
      return;
    }

    const file = files[0];
    const remotePath = pathInput.value;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('path', remotePath);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/upload', true);

    xhr.upload.onprogress = function(e) {
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded / e.total) * 100);
        progressBar.style.display = 'block';
        progressBar.value = percent;
      }
    };

    xhr.onloadstart = function() {
      output.textContent = 'Uploading...';
      submitBtn.disabled = true;
      progressBar.value = 0;
      progressBar.style.display = 'block';
    };

    xhr.onerror = function() {
      showToast('Upload failed (network error)', true);
      submitBtn.disabled = false;
      serverResp.style.display = 'none';
      progressBar.style.display = 'none';
    };

    xhr.onload = function() {
  submitBtn.disabled = false;
  progressBar.style.display = 'none';
  try {
    const json = JSON.parse(xhr.responseText);

    // handle nested "result"
    const success = json.success ?? json.result?.success;
    const message = json.message ?? json.result?.message;
    const error = json.error; // capture error if present

    if (success) {
      showToast('✅ File uploaded successfully!');
      fileInput.value = ""; // clear file selection
      serverResp.style.display = 'none';
      output.style.display = 'none';
      output.textContent = "No response yet."; // clear debug
    } else {
      const displayMsg = error || message || 'Unknown error';
      showToast('❌ Upload failed: ' + displayMsg, true);
      serverResp.style.display = 'block';
      output.style.display = 'block';
      output.textContent = displayMsg; // only show the message/error
    }
  } catch (err) {
    showToast('❌ Server returned non-JSON response', true);
    serverResp.style.display = 'block';
    output.style.display = 'block';
    output.textContent = 'Server returned:\n' + xhr.responseText;
  }
};


    xhr.send(formData);
  }

  function clearLog(){
    output.textContent = '';
    progressBar.style.display = 'none';
    progressBar.value = 0;
    fileInput.value = ""; // clear file selection
  }