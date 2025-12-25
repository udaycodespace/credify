// Main JavaScript file for Blockchain Verifiable Credentials System
// Handles client-side interactions and real-time updates

class CredentialSystem {
    constructor() {
        this.init();
        this.setupEventListeners();
        this.startStatusMonitoring();
    }

    init() {
        console.log('Blockchain Verifiable Credentials System initialized');
        this.loadSystemStatus();
        this.setupFormValidation();
        this.setupNotifications();
    }

    setupEventListeners() {
        // Copy buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('copy-btn') || 
                e.target.closest('.copy-btn')) {
                this.handleCopyClick(e);
            }
        });

        // Refresh buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('refresh-btn') || 
                e.target.closest('.refresh-btn')) {
                this.handleRefreshClick(e);
            }
        });

        // Form submissions
        document.addEventListener('submit', (e) => {
            this.handleFormSubmission(e);
        });

        // Real-time form validation
        document.addEventListener('input', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                this.validateField(e.target);
            }
        });
    }

    setupFormValidation() {
        // GPA validation
        const gpaInputs = document.querySelectorAll('input[type="number"][id*="gpa"]');
        gpaInputs.forEach(input => {
            input.addEventListener('input', (e) => {
                const value = parseFloat(e.target.value);
                if (value < 0 || value > 10) {
                    e.target.setCustomValidity('GPA must be between 0 and 10');
                } else {
                    e.target.setCustomValidity('');
                }
            });
        });

        // Student ID validation
        const studentIdInputs = document.querySelectorAll('input[id*="studentId"], input[id*="student_id"]');
        studentIdInputs.forEach(input => {
            input.addEventListener('input', (e) => {
                const value = e.target.value.trim();
                if (value && !/^[A-Za-z0-9]+$/.test(value)) {
                    e.target.setCustomValidity('Student ID should contain only letters and numbers');
                } else {
                    e.target.setCustomValidity('');
                }
            });
        });
    }

    setupNotifications() {
        // Check if notifications are supported
        if ('Notification' in window) {
            // Request permission if not already granted
            if (Notification.permission === 'default') {
                Notification.requestPermission();
            }
        }
    }

    // System status monitoring
    startStatusMonitoring() {
        this.updateBlockchainStatus();
        
        // Update every 30 seconds
        setInterval(() => {
            this.updateBlockchainStatus();
        }, 30000);
    }

    async updateBlockchainStatus() {
        try {
            const response = await fetch('/api/blockchain_status');
            const data = await response.json();
            
            this.updateStatusDisplay(data);
        } catch (error) {
            console.warn('Could not update blockchain status:', error);
            this.updateStatusDisplay({
                total_blocks: 'Error',
                total_credentials: 'Error',
                ipfs_status: false
            });
        }
    }

    updateStatusDisplay(data) {
        // Update navbar status
        const blockCountElement = document.getElementById('block-count');
        if (blockCountElement) {
            blockCountElement.textContent = `${data.total_blocks} blocks`;
        }

        // Update system status cards if present
        const totalBlocksElement = document.getElementById('total-blocks');
        if (totalBlocksElement) {
            totalBlocksElement.textContent = data.total_blocks;
        }

        const totalCredentialsElement = document.getElementById('total-credentials');
        if (totalCredentialsElement) {
            totalCredentialsElement.textContent = data.total_credentials;
        }

        const ipfsStatusElement = document.getElementById('ipfs-status');
        if (ipfsStatusElement) {
            if (data.ipfs_status) {
                ipfsStatusElement.textContent = 'Connected';
                ipfsStatusElement.className = 'badge bg-success';
            } else {
                ipfsStatusElement.textContent = 'Local Storage';
                ipfsStatusElement.className = 'badge bg-warning';
            }
        }

        const lastUpdateElement = document.getElementById('last-update');
        if (lastUpdateElement) {
            lastUpdateElement.textContent = new Date().toLocaleTimeString();
        }
    }

    async loadSystemStatus() {
        await this.updateBlockchainStatus();
    }

    // Form handling
    handleFormSubmission(e) {
        const form = e.target;
        const submitButton = form.querySelector('button[type="submit"]');
        
        if (submitButton) {
            // Add loading state
            const originalText = submitButton.innerHTML;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
            submitButton.disabled = true;
            
            // Restore button after a delay if form validation fails
            setTimeout(() => {
                if (submitButton.disabled) {
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                }
            }, 5000);
        }
    }

    // Field validation
    validateField(field) {
        const fieldType = field.type;
        const fieldValue = field.value.trim();
        
        // Remove any existing validation feedback
        const existingFeedback = field.parentNode.querySelector('.invalid-feedback, .valid-feedback');
        if (existingFeedback) {
            existingFeedback.remove();
        }
        
        field.classList.remove('is-valid', 'is-invalid');
        
        if (fieldValue === '' && field.required) {
            this.showFieldError(field, 'This field is required');
            return false;
        }
        
        // Specific validation based on field type
        switch (fieldType) {
            case 'email':
                if (fieldValue && !this.isValidEmail(fieldValue)) {
                    this.showFieldError(field, 'Please enter a valid email address');
                    return false;
                }
                break;
            case 'number':
                if (fieldValue && isNaN(fieldValue)) {
                    this.showFieldError(field, 'Please enter a valid number');
                    return false;
                }
                break;
        }
        
        if (fieldValue) {
            this.showFieldSuccess(field);
        }
        
        return true;
    }

    showFieldError(field, message) {
        field.classList.add('is-invalid');
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.textContent = message;
        field.parentNode.appendChild(feedback);
    }

    showFieldSuccess(field) {
        field.classList.add('is-valid');
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // Copy functionality
    handleCopyClick(e) {
        e.preventDefault();
        const button = e.target.closest('.copy-btn');
        const targetSelector = button.dataset.target;
        const targetElement = document.querySelector(targetSelector);
        
        if (targetElement) {
            const textToCopy = targetElement.value || targetElement.textContent;
            this.copyToClipboard(textToCopy);
            this.showCopySuccess(button);
        }
    }

    async copyToClipboard(text) {
        try {
            if (navigator.clipboard) {
                await navigator.clipboard.writeText(text);
            } else {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
            }
            return true;
        } catch (error) {
            console.error('Failed to copy text:', error);
            return false;
        }
    }

    showCopySuccess(button) {
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check me-1"></i>Copied!';
        button.classList.remove('btn-outline-primary');
        button.classList.add('btn-success');
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.classList.remove('btn-success');
            button.classList.add('btn-outline-primary');
        }, 2000);
    }

    // Refresh functionality
    handleRefreshClick(e) {
        e.preventDefault();
        const button = e.target.closest('.refresh-btn');
        const originalText = button.innerHTML;
        
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Refreshing...';
        button.disabled = true;
        
        // Simulate refresh action
        setTimeout(() => {
            location.reload();
        }, 1000);
    }

    // Notification system
    showNotification(title, message, type = 'info') {
        // Browser notification
        if (Notification.permission === 'granted') {
            new Notification(title, {
                body: message,
                icon: '/static/favicon.ico',
                tag: 'credential-system'
            });
        }
        
        // In-app notification
        this.showAlert(message, type);
    }

    showAlert(message, type = 'info', duration = 5000) {
        const alertContainer = document.querySelector('.container');
        if (!alertContainer) return;
        
        const alertElement = document.createElement('div');
        alertElement.className = `alert alert-${type} alert-dismissible fade show`;
        alertElement.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        alertContainer.insertBefore(alertElement, alertContainer.firstChild);
        
        // Auto-dismiss
        if (duration > 0) {
            setTimeout(() => {
                if (alertElement.parentNode) {
                    alertElement.remove();
                }
            }, duration);
        }
    }

    // Utility functions
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    formatTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    formatHash(hash, length = 20) {
        if (!hash) return 'N/A';
        return hash.length > length ? `${hash.substring(0, length)}...` : hash;
    }

    // Animation helpers
    animateElement(element, animation) {
        element.classList.add('animate__animated', `animate__${animation}`);
        
        element.addEventListener('animationend', () => {
            element.classList.remove('animate__animated', `animate__${animation}`);
        }, { once: true });
    }

    // Loading states
    showLoading(element) {
        if (element) {
            element.classList.add('loading');
        }
    }

    hideLoading(element) {
        if (element) {
            element.classList.remove('loading');
        }
    }

    // Modal helpers
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
            return bsModal;
        }
    }

    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        }
    }
}

// Enhanced credential verification
class CredentialVerifier {
    constructor() {
        this.verificationHistory = [];
    }

    async verifyCredential(credentialId) {
        try {
            const response = await fetch('/api/verify_credential', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ credential_id: credentialId })
            });

            const result = await response.json();
            
            // Add to verification history
            this.verificationHistory.push({
                credentialId,
                result,
                timestamp: new Date().toISOString()
            });
            
            return result;
        } catch (error) {
            console.error('Verification error:', error);
            throw error;
        }
    }

    getVerificationHistory() {
        return this.verificationHistory;
    }

    clearVerificationHistory() {
        this.verificationHistory = [];
    }
}

// Enhanced selective disclosure
class SelectiveDisclosure {
    constructor() {
        this.disclosureHistory = [];
    }

    async createDisclosure(credentialId, selectedFields) {
        try {
            const response = await fetch('/api/selective_disclosure', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    credential_id: credentialId,
                    fields: selectedFields
                })
            });

            const result = await response.json();
            
            // Add to disclosure history
            this.disclosureHistory.push({
                credentialId,
                selectedFields,
                result,
                timestamp: new Date().toISOString()
            });
            
            return result;
        } catch (error) {
            console.error('Disclosure error:', error);
            throw error;
        }
    }

    getDisclosureHistory() {
        return this.disclosureHistory;
    }
}

// Initialize the system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize main system
    window.credentialSystem = new CredentialSystem();
    window.credentialVerifier = new CredentialVerifier();
    window.selectiveDisclosure = new SelectiveDisclosure();
    
    console.log('Blockchain Verifiable Credentials System loaded successfully');
});

// Export for use in other scripts
window.CredentialSystem = CredentialSystem;
window.CredentialVerifier = CredentialVerifier;
window.SelectiveDisclosure = SelectiveDisclosure;

// Error handling
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
    
    // Show user-friendly error message
    if (window.credentialSystem) {
        window.credentialSystem.showAlert(
            'An unexpected error occurred. Please refresh the page and try again.',
            'danger'
        );
    }
});

// Handle offline/online status
window.addEventListener('online', function() {
    if (window.credentialSystem) {
        window.credentialSystem.showAlert('Connection restored', 'success', 3000);
        window.credentialSystem.updateBlockchainStatus();
    }
});

window.addEventListener('offline', function() {
    if (window.credentialSystem) {
        window.credentialSystem.showAlert(
            'Connection lost. Some features may not work properly.',
            'warning'
        );
    }
});
