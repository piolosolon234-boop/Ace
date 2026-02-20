// Connection Status Management
function updateConnectionStatus() {
    fetch('/check_connection')
        .then(response => response.json())
        .then(data => {
            const statusElement = document.getElementById('connectionStatus');
            if (data.online) {
                statusElement.innerHTML = '<i class="fas fa-wifi"></i> Online';
                statusElement.className = 'connection-status online';
                
                // Show sync button if there are pending offline operations
                const syncBtn = document.getElementById('syncData');
                if (syncBtn) {
                    syncBtn.disabled = false;
                    syncBtn.innerHTML = '<i class="fas fa-sync"></i> Sync Offline Data';
                    syncBtn.onclick = function() {
                        syncOfflineData();
                    };
                }
            } else {
                statusElement.innerHTML = '<i class="fas fa-wifi-slash"></i> Offline';
                statusElement.className = 'connection-status offline';
                
                // Disable sync button
                const syncBtn = document.getElementById('syncData');
                if (syncBtn) {
                    syncBtn.disabled = true;
                    syncBtn.innerHTML = '<i class="fas fa-sync"></i> Sync Data (Requires Connection)';
                }
            }
        })
        .catch(() => {
            // If fetch fails, we're offline
            const statusElement = document.getElementById('connectionStatus');
            if (statusElement) {
                statusElement.innerHTML = '<i class="fas fa-wifi-slash"></i> Offline';
                statusElement.className = 'connection-status offline';
            }
        });
}

// Sync offline data
function syncOfflineData() {
    const syncBtn = document.getElementById('syncData');
    if (syncBtn) {
        syncBtn.disabled = true;
        syncBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Syncing...';
    }
    
    fetch('/sync_offline_data')
        .then(response => response.json())
        .then(data => {
            if (data.success !== false) {
                showAlert(`Synced ${data.users_synced} users and ${data.bookings_synced} bookings successfully!`, 'success');
                
                // Update sync button
                if (syncBtn) {
                    syncBtn.innerHTML = '<i class="fas fa-check"></i> Synced';
                    setTimeout(() => {
                        syncBtn.innerHTML = '<i class="fas fa-sync"></i> Sync Offline Data';
                        syncBtn.disabled = false;
                    }, 2000);
                }
                
                // Reload page to show updated data
                setTimeout(() => location.reload(), 1500);
            } else {
                showAlert('Sync failed: ' + data.message, 'error');
                if (syncBtn) {
                    syncBtn.disabled = false;
                    syncBtn.innerHTML = '<i class="fas fa-sync"></i> Sync Offline Data';
                }
            }
        })
        .catch(error => {
            showAlert('Sync failed: ' + error, 'error');
            if (syncBtn) {
                syncBtn.disabled = false;
                syncBtn.innerHTML = '<i class="fas fa-sync"></i> Sync Offline Data';
            }
        });
}

// Show alert message
function showAlert(message, type) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.flash-messages');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        ${message}
        <button class="close-alert">&times;</button>
    `;
    
    // Add to page
    const mainContainer = document.querySelector('.main-container');
    if (mainContainer) {
        const firstChild = mainContainer.firstChild;
        mainContainer.insertBefore(alertDiv, firstChild);
    }
    
    // Add close functionality
    const closeBtn = alertDiv.querySelector('.close-alert');
    closeBtn.addEventListener('click', () => {
        alertDiv.remove();
    });
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Close alert buttons
document.addEventListener('DOMContentLoaded', function() {
    // Close alert buttons
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('close-alert')) {
            e.target.closest('.alert').remove();
        }
    });
    
    // Check connection status every 30 seconds
    updateConnectionStatus();
    setInterval(updateConnectionStatus, 30000);
    
    // Manual connection check button
    const checkBtn = document.getElementById('checkConnection');
    if (checkBtn) {
        checkBtn.addEventListener('click', function(e) {
            e.preventDefault();
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking...';
            updateConnectionStatus();
            setTimeout(() => {
                this.innerHTML = 'Check Connection';
            }, 1000);
        });
    }
    
    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = this.querySelectorAll('[required]');
            let valid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    valid = false;
                    field.style.borderColor = '#ef4444';
                    
                    // Add error message
                    if (!field.nextElementSibling || !field.nextElementSibling.classList.contains('error-message')) {
                        const errorMsg = document.createElement('small');
                        errorMsg.className = 'error-message';
                        errorMsg.style.color = '#ef4444';
                        errorMsg.textContent = 'This field is required';
                        field.parentNode.appendChild(errorMsg);
                    }
                } else {
                    field.style.borderColor = '';
                    
                    // Remove error message
                    const errorMsg = field.parentNode.querySelector('.error-message');
                    if (errorMsg) {
                        errorMsg.remove();
                    }
                }
            });
            
            if (!valid) {
                e.preventDefault();
                showAlert('Please fill in all required fields', 'error');
            }
        });
    });
});

// Seat selection functionality
function setupSeatSelection() {
    const seatBtns = document.querySelectorAll('.seat-btn');
    seatBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.parentNode.querySelector('.seat-count');
            const change = parseInt(this.dataset.change || (this.textContent === '+' ? 1 : -1));
            const min = parseInt(input.min) || 1;
            const max = parseInt(input.max) || 10;
            const current = parseInt(input.value) || 1;
            const newValue = current + change;
            
            if (newValue >= min && newValue <= max) {
                input.value = newValue;
                
                // Update fare calculation
                if (window.updateFare) {
                    window.updateFare();
                }
            }
        });
    });
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', setupSeatSelection);