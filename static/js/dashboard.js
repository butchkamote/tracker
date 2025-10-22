// Update current time in navbar
function updateTime() {
    const timeElement = document.getElementById('currentTime');
    if (timeElement) {
        const now = new Date();
        timeElement.textContent = now.toLocaleTimeString();
    }
}
setInterval(updateTime, 1000);
updateTime();

// Current filter state
let currentFilter = 'ALL';

// Filter categories
function filterCategory(category) {
    currentFilter = category;
    const sections = document.querySelectorAll('.category-section');
    const selectedText = document.getElementById('selectedCategory');
    
    // Update dropdown text
    const categoryNames = {
        'ALL': 'All Categories',
        'ENDORSEMENT_MAYA': 'ENDORSEMENT - MAYA',
        'ENDORSEMENT_OLA': 'ENDORSEMENT - OLA',
        'LOXON': 'LOXON',
        'DCA_MAYA': 'DCA - MAYA',
        'PAYMENTS_MAYA': 'PAYMENTS - MAYA',
        'PAYMENTS_OLA': 'PAYMENTS - OLA'
    };
    
    selectedText.textContent = categoryNames[category] || category;
    
    // Show/hide sections based on filter
    sections.forEach(section => {
        const sectionCategory = section.getAttribute('data-category');
        if (category === 'ALL' || sectionCategory === category) {
            section.style.display = 'block';
            section.classList.remove('hidden');
        } else {
            section.style.display = 'none';
            section.classList.add('hidden');
        }
    });
    
    // Update summary counters for filtered view
    updateFilteredSummary();
    
    // Close dropdown after selection
    const dropdown = bootstrap.Dropdown.getInstance(document.getElementById('categoryDropdown'));
    if (dropdown) {
        dropdown.hide();
    }
}

// Toggle category collapse
function toggleCategory(categoryId) {
    const content = document.getElementById(`category-${categoryId}`);
    const button = event.target.closest('.collapse-btn');
    const icon = button.querySelector('i');
    
    if (content.style.display === 'none' || content.classList.contains('collapsed')) {
        content.style.display = 'flex';
        content.classList.remove('collapsed');
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
        button.classList.remove('collapsed');
    } else {
        content.style.display = 'none';
        content.classList.add('collapsed');
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
        button.classList.add('collapsed');
    }
}

// Update filtered summary
function updateFilteredSummary() {
    const visibleSections = document.querySelectorAll('.category-section:not(.hidden)');
    const statusCounts = {
        'PENDING': 0,
        'DOWNLOADED': 0,
        'PROCESSED': 0,
        'UPLOADED': 0,
        'N/A': 0
    };
    
    visibleSections.forEach(section => {
        if (section.style.display !== 'none') {
            const allTasks = section.querySelectorAll('.task-item');
            allTasks.forEach(item => {
                const statusBadge = item.querySelector('.status-badge');
                if (statusBadge) {
                    const statusText = statusBadge.textContent.trim();
                    const status = statusText.split(' ').pop();
                    if (statusCounts.hasOwnProperty(status)) {
                        statusCounts[status]++;
                    }
                }
            });
        }
    });
    
    // Update summary cards
    const summaryCards = document.querySelectorAll('.summary-card h4');
    const statuses = ['PENDING', 'DOWNLOADED', 'PROCESSED', 'UPLOADED', 'N/A'];
    
    summaryCards.forEach((card, index) => {
        if (index < statuses.length) {
            card.textContent = statusCounts[statuses[index]];
        }
    });
}

// Update task status
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.update-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const taskKey = this.dataset.task;
            const status = this.dataset.status;
            const assignedTo = document.querySelector(`input[data-task="${taskKey}"]`).value;
            const notes = document.querySelector(`textarea[data-task="${taskKey}"]`).value;
            const cardElement = this.closest('.glass-card');
            
            // Add visual feedback
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
            this.disabled = true;
            
            fetch('/update_task', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    task_key: taskKey,
                    status: status,
                    assigned_to: assignedTo,
                    notes: notes
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateCardStatus(cardElement, taskKey, status);
                    updateFilteredSummary();
                } else {
                    // Restore button if failed
                    this.innerHTML = originalText;
                    this.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                this.innerHTML = originalText;
                this.disabled = false;
            });
        });
    });

    // Auto-save assigned to and notes
    document.querySelectorAll('.assigned-input, .notes-input').forEach(input => {
        input.addEventListener('blur', function() {
            const taskKey = this.dataset.task;
            const assignedTo = document.querySelector(`input[data-task="${taskKey}"]`).value;
            const notes = document.querySelector(`textarea[data-task="${taskKey}"]`).value;
            const currentStatus = document.querySelector(`.update-btn[data-task="${taskKey}"][disabled]`)?.dataset.status || 'PENDING';
            
            // Add visual feedback
            const originalBg = this.style.backgroundColor;
            this.style.backgroundColor = 'rgba(220, 252, 231, 0.5)';
            
            fetch('/update_task', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    task_key: taskKey,
                    status: currentStatus,
                    assigned_to: assignedTo,
                    notes: notes
                })
            })
            .then(() => {
                setTimeout(() => {
                    this.style.backgroundColor = originalBg;
                }, 500);
            })
            .catch(error => {
                console.error('Error:', error);
                this.style.backgroundColor = originalBg;
            });
        });
    });

    // Initialize filter
    filterCategory('ALL');
});

// Update a single card's status without page reload
function updateCardStatus(cardElement, taskKey, newStatus) {
    // Update status badge
    const statusBadge = cardElement.querySelector('.status-badge');
    statusBadge.style.backgroundColor = getStatusColor(newStatus);
    
    // Update badge icon and text
    let iconClass = 'fa-hourglass-start';
    if (newStatus === 'DOWNLOADED') iconClass = 'fa-download';
    else if (newStatus === 'PROCESSED') iconClass = 'fa-cog';
    else if (newStatus === 'UPLOADED') iconClass = 'fa-cloud-upload-alt';
    else if (newStatus === 'N/A') iconClass = 'fa-ban';
    
    statusBadge.innerHTML = `<i class="fas ${iconClass}"></i> ${newStatus}`;
    
    // Update all buttons (disable the selected one, enable others)
    const buttons = cardElement.querySelectorAll('.update-btn');
    buttons.forEach(button => {
        if (button.dataset.status === newStatus) {
            button.disabled = true;
            button.innerHTML = `<i class="fas ${iconClass}"></i> ${newStatus}`;
        } else {
            button.disabled = false;
            
            // Reset button text with proper icon
            let btnStatus = button.dataset.status;
            let btnIcon = 'fa-hourglass-start';
            if (btnStatus === 'DOWNLOADED') btnIcon = 'fa-download';
            else if (btnStatus === 'PROCESSED') btnIcon = 'fa-cog';
            else if (btnStatus === 'UPLOADED') btnIcon = 'fa-cloud-upload-alt';
            else if (btnStatus === 'N/A') btnIcon = 'fa-ban';
            
            button.innerHTML = `<i class="fas ${btnIcon}"></i> ${btnStatus}`;
        }
    });
    
    // Handle payment-alert class on card based on status
    const category = taskKey.split('_')[0];
    if (category.includes('PAYMENTS')) {
        if (newStatus === 'UPLOADED' || newStatus === 'N/A') {
            cardElement.classList.remove('payment-alert');
        } else {
            cardElement.classList.add('payment-alert');
        }
    }
    
    // Update the last updated time
    const timestamp = new Date().toLocaleString();
    const timeElement = cardElement.querySelector('.text-muted');
    if (timeElement) {
        timeElement.innerHTML = `<i class="fas fa-history"></i> Updated: ${timestamp}`;
    }
}

// Get color for status
function getStatusColor(status) {
    const colors = {
        'PENDING': '#ffc107',
        'DOWNLOADED': '#17a2b8',
        'PROCESSED': '#fd7e14',
        'UPLOADED': '#28a745',
        'N/A': '#6c757d'
    };
    return colors[status] || '#6c757d';
}

// Manual reminder trigger
function triggerReminder() {
    const btn = event.target.closest('.btn-warning');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    btn.disabled = true;
    
    fetch('/manual_reminder')
    .then(response => response.json())
    .then(data => {
        btn.innerHTML = '<i class="fas fa-check"></i> Sent!';
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }, 2000);
        
        showToast('Reminder Sent', 'Payment reminder has been sent successfully. Check the console for details.');
    })
    .catch(error => {
        console.error('Error:', error);
        btn.innerHTML = originalText;
        btn.disabled = false;
        showToast('Error', 'Failed to send reminder. Please try again.');
    });
}

// Show toast notification
function showToast(title, message) {
    const toast = document.createElement('div');
    toast.className = 'position-fixed bottom-0 end-0 p-3';
    toast.style.zIndex = '11';
    toast.innerHTML = `
        <div class="toast show" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <strong class="me-auto"><i class="fas fa-bell text-warning"></i> ${title}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    document.body.appendChild(toast);
    
    // Remove toast after 3 seconds
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Auto refresh every 30 seconds
setInterval(() => {
    updateFilteredSummary();
}, 30000);

// Show current time in title
setInterval(() => {
    const now = new Date();
    const timeStr = now.toLocaleTimeString();
    document.title = `📊 DA PROCESS - ${timeStr}`;
}, 1000);