// Update current time in navbar
function updateTime() {
    const now = new Date();
    document.getElementById('currentTime').textContent = now.toLocaleTimeString();
}
setInterval(updateTime, 1000);
updateTime();

// Run PDS script
function runScript(campaignName) {
    const btn = document.getElementById(`btn-${campaignName}`);
    const status = document.getElementById(`status-${campaignName}`);
    
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
    btn.disabled = true;
    status.style.backgroundColor = '#17a2b8';
    status.innerHTML = '<i class="fas fa-cog fa-spin"></i> PROCESSING';
    
    fetch(`/run/${campaignName}`)
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            btn.innerHTML = '<i class="fas fa-check"></i> Completed';
            btn.className = 'btn btn-success';
            status.style.backgroundColor = '#28a745';
            status.innerHTML = '<i class="fas fa-check-circle"></i> SUCCESS';
            
            // Show script output in a detailed toast/modal
            showScriptOutput(campaignName, data.output || data.message, 'success');
        } else {
            btn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Failed';
            btn.className = 'btn btn-danger';
            status.style.backgroundColor = '#dc3545';
            status.innerHTML = '<i class="fas fa-times-circle"></i> FAILED';
            
            // Show error output
            const errorMessage = data.error || data.message || 'Script execution failed';
            showScriptOutput(campaignName, errorMessage, 'error');
        }
        
        // Reset button after 3 seconds
        setTimeout(() => {
            btn.innerHTML = '<i class="fas fa-play"></i> Run Script';
            btn.className = 'btn btn-primary';
            btn.disabled = false;
            status.style.backgroundColor = '#6c757d';
            status.innerHTML = '<i class="fas fa-hourglass-start"></i> READY';
        }, 3000);
    })
    .catch(error => {
        console.error('Error:', error);
        btn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
        btn.className = 'btn btn-danger';
        status.style.backgroundColor = '#dc3545';
        status.innerHTML = '<i class="fas fa-times-circle"></i> ERROR';
        
        showScriptOutput(campaignName, 'Network error occurred', 'error');
        
        // Reset button after 3 seconds
        setTimeout(() => {
            btn.innerHTML = '<i class="fas fa-play"></i> Run Script';
            btn.className = 'btn btn-primary';
            btn.disabled = false;
            status.style.backgroundColor = '#6c757d';
            status.innerHTML = '<i class="fas fa-hourglass-start"></i> READY';
        }, 3000);
    });
}

// New function to show script output in a modal
function showScriptOutput(campaignName, output, type) {
    // Create modal HTML
    const modalHtml = `
        <div class="modal fade" id="scriptOutputModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header ${type === 'success' ? 'bg-success' : 'bg-danger'} text-white">
                        <h5 class="modal-title">
                            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-triangle'}"></i>
                            ${campaignName} Script Output
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert ${type === 'success' ? 'alert-success' : 'alert-danger'}">
                            <strong>${type === 'success' ? '✅ Success' : '❌ Error'}:</strong>
                            Script execution ${type === 'success' ? 'completed' : 'failed'}
                        </div>
                        <div class="script-output">
                            <h6>Script Output:</h6>
                            <pre class="bg-dark text-light p-3 rounded" style="white-space: pre-wrap; font-family: 'Courier New', monospace; font-size: 0.9em;">${output}</pre>
                        </div>
                        ${type === 'success' ? `
                        <div class="mt-3">
                            <button class="btn btn-primary" onclick="openOutputFolder()">
                                <i class="fas fa-folder-open"></i> Open Output Folder
                            </button>
                        </div>
                        ` : ''}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('scriptOutputModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to document
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('scriptOutputModal'));
    modal.show();
    
    // Auto-remove modal when hidden
    document.getElementById('scriptOutputModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// Navbar tool functions
function openOutputFolder() {
    fetch('/open_output_folder')
    .then(response => response.json())
    .then(data => {
        showToast('Output Folder', data.message);
    });
}

function createEndoFolder() {
    fetch('/create_endo_folder')
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast('ENDO Folder', `Created: ${data.message}`);
            setTimeout(() => location.reload(), 1000);
        }
    });
}

function showToast(title, message) {
    const toast = document.createElement('div');
    toast.className = 'position-fixed bottom-0 end-0 p-3';
    toast.style.zIndex = '11';
    toast.innerHTML = `
        <div class="toast show" role="alert">
            <div class="toast-header">
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">${message}</div>
        </div>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// Upload file for a specific campaign (called from onchange in template)
function uploadFile(campaignName) {
    const fileInput = document.getElementById(`file-input-${campaignName}`);
    const file = fileInput.files[0];
    
    if (!file) {
        showToast('Upload Error', 'Please select a file first');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    // Show loading state
    showToast('Upload Status', 'Uploading file...');
    
    fetch(`/upload/${campaignName}`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast('Upload Success', data.message);
            fileInput.value = ''; // Clear the input
        } else {
            showToast('Upload Error', data.message || 'Upload failed');
        }
    })
    .catch(error => {
        console.error('Upload error:', error);
        showToast('Upload Error', 'Upload error occurred');
    });
}