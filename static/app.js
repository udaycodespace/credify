// ============================================================
// CREDIFY 2026 - BRUTALIST CYBER JAVASCRIPT
// Built for: G. Pulla Reddy Engineering College
// Team: SHASHI, UDAY, TEJA VARSHITH
// Description: Enhanced credential system with Easter eggs
// ============================================================

// Console Art Banner
console.log('%c' + `
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ██████╗██████╗ ███████╗██████╗ ██╗███████╗██╗   ██╗   ║
║  ██╔════╝██╔══██╗██╔════╝██╔══██╗██║██╔════╝╚██╗ ██╔╝   ║
║  ██║     ██████╔╝█████╗  ██║  ██║██║█████╗   ╚████╔╝    ║
║  ██║     ██╔══██╗██╔══╝  ██║  ██║██║██╔══╝    ╚██╔╝     ║
║  ╚██████╗██║  ██║███████╗██████╔╝██║██║        ██║      ║
║   ╚═════╝╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝        ╚═╝      ║
║                                                           ║
║              BLOCKCHAIN CREDENTIALS SYSTEM 2026           ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
`, 'color: #06b6d4; font-weight: bold;');

console.log('%c🔐 System Status: ONLINE', 'color: #10b981; font-weight: bold; font-size: 14px;');
console.log('%c🎯 Build: Production v1.0', 'color: #fbbf24; font-weight: bold;');
console.log('%c💡 Easter Eggs: 🥚🥚🥚🥚🥚 (Try finding them!)', 'color: #22d3ee;');
console.log('%c', 'color: #94a3b8;');

// ============================================================
// MAIN CREDENTIAL SYSTEM CLASS
// ============================================================
class CredentialSystem {
    constructor() {
        this.easterEggs = {
            konamiCode: [],
            clickCount: 0,
            secretCommands: [],
            matrixActive: false
        };
        this.konamiSequence = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];
        
        this.init();
        this.setupEventListeners();
        this.startStatusMonitoring();
        this.initEasterEggs();
    }

    init() {
        console.log('%c⚡ Credential System Initialized', 'color: #22d3ee; font-weight: bold;');
        this.loadSystemStatus();
        this.setupFormValidation();
        this.setupNotifications();
        this.showWelcomeMessage();
    }

    showWelcomeMessage() {
        // Brutalist welcome animation
        setTimeout(() => {
            const messages = [
                '🔐 Blockchain Network: Connected',
                '🌐 IPFS Storage: Ready',
                '⚡ Cryptographic Engine: Active',
                '✅ System: Operational'
            ];
            
            messages.forEach((msg, index) => {
                setTimeout(() => {
                    console.log(`%c${msg}`, 'color: #10b981;');
                }, index * 500);
            });
        }, 1000);
    }

    // ============================================================
    // EVENT LISTENERS
    // ============================================================
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

    // ============================================================
    // FORM VALIDATION
    // ============================================================
    setupFormValidation() {
        // GPA validation
        const gpaInputs = document.querySelectorAll('input[type="number"][id*="gpa"]');
        gpaInputs.forEach(input => {
            input.addEventListener('input', (e) => {
                const value = parseFloat(e.target.value);
                if (value < 0 || value > 10) {
                    e.target.setCustomValidity('GPA must be between 0 and 10');
                    this.showFieldError(e.target, 'GPA must be between 0 and 10');
                } else {
                    e.target.setCustomValidity('');
                    this.showFieldSuccess(e.target);
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
                    this.showFieldError(e.target, 'Student ID: Alphanumeric only');
                } else {
                    e.target.setCustomValidity('');
                    if (value) this.showFieldSuccess(e.target);
                }
            });
        });
    }

    validateField(field) {
        const fieldType = field.type;
        const fieldValue = field.value.trim();
        
        // Remove existing validation feedback
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
                    this.showFieldError(field, 'Invalid email address');
                    return false;
                }
                break;
            case 'number':
                if (fieldValue && isNaN(fieldValue)) {
                    this.showFieldError(field, 'Must be a number');
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
        feedback.style.display = 'block';
        feedback.innerHTML = `<i class="fas fa-exclamation-triangle me-1"></i>${message}`;
        field.parentNode.appendChild(feedback);
    }

    showFieldSuccess(field) {
        field.classList.add('is-valid');
        const feedback = document.createElement('div');
        feedback.className = 'valid-feedback';
        feedback.style.display = 'block';
        feedback.innerHTML = `<i class="fas fa-check-circle me-1"></i>Valid`;
        field.parentNode.appendChild(feedback);
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // ============================================================
    // NOTIFICATIONS
    // ============================================================
    setupNotifications() {
        if ('Notification' in window) {
            if (Notification.permission === 'default') {
                Notification.requestPermission();
            }
        }
    }

    showNotification(title, message, type = 'info') {
        // Browser notification
        if (Notification.permission === 'granted') {
            new Notification(title, {
                body: message,
                icon: '/static/favicon.ico',
                tag: 'credential-system'
            });
        }
        
        // Brutalist in-app notification
        this.showBrutalistAlert(message, type);
    }

    showBrutalistAlert(message, type = 'info', duration = 5000) {
        const alertContainer = document.querySelector('.container') || document.body;
        
        const alertElement = document.createElement('div');
        alertElement.className = `alert alert-${type} alert-dismissible fade show custom-alert`;
        alertElement.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 9999;
            min-width: 400px;
            max-width: 600px;
            border: 2px solid;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
        `;
        
        const icons = {
            'success': 'fa-check-circle',
            'info': 'fa-info-circle',
            'warning': 'fa-exclamation-triangle',
            'danger': 'fa-times-circle'
        };
        
        alertElement.innerHTML = `
            <i class="fas ${icons[type]} me-2"></i>
            <strong>${message}</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertElement);
        
        // Auto-dismiss
        if (duration > 0) {
            setTimeout(() => {
                alertElement.classList.remove('show');
                setTimeout(() => alertElement.remove(), 300);
            }, duration);
        }
    }

    showAlert(message, type = 'info', duration = 5000) {
        this.showBrutalistAlert(message, type, duration);
    }

    // ============================================================
    // BLOCKCHAIN STATUS MONITORING
    // ============================================================
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
            console.warn('%c⚠️ Could not update blockchain status', 'color: #f59e0b;', error);
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

        // Update system status cards
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

    // ============================================================
    // FORM SUBMISSION HANDLING
    // ============================================================
    handleFormSubmission(e) {
        const form = e.target;
        const submitButton = form.querySelector('button[type="submit"]');
        
        if (submitButton) {
            const originalText = submitButton.innerHTML;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>PROCESSING...';
            submitButton.disabled = true;
            
            setTimeout(() => {
                if (submitButton.disabled) {
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                }
            }, 5000);
        }
    }

    // ============================================================
    // COPY FUNCTIONALITY
    // ============================================================
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
                // Fallback
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
            }
            return true;
        } catch (error) {
            console.error('Failed to copy:', error);
            return false;
        }
    }

    showCopySuccess(button) {
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check me-1"></i>COPIED!';
        button.classList.remove('btn-outline-primary');
        button.classList.add('btn-success');
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.classList.remove('btn-success');
            button.classList.add('btn-outline-primary');
        }, 2000);
    }

    // ============================================================
    // REFRESH FUNCTIONALITY
    // ============================================================
    handleRefreshClick(e) {
        e.preventDefault();
        const button = e.target.closest('.refresh-btn');
        const originalText = button.innerHTML;
        
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>REFRESHING...';
        button.disabled = true;
        
        setTimeout(() => {
            location.reload();
        }, 1000);
    }

    // ============================================================
    // UTILITY FUNCTIONS
    // ============================================================
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

    // ============================================================
    // LOADING STATES
    // ============================================================
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

    // ============================================================
    // MODAL HELPERS
    // ============================================================
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

    // ============================================================
    // EASTER EGGS SYSTEM
    // ============================================================
    initEasterEggs() {
        console.log('%c🥚 Easter Egg System: Active', 'color: #fbbf24;');
        console.log('%cTry: Konami Code, Triple-click logo, Type "matrix", Click corners!', 'color: #94a3b8;');
        
        // Konami Code
        document.addEventListener('keydown', (e) => {
            this.easterEggs.konamiCode.push(e.key);
            if (this.easterEggs.konamiCode.length > this.konamiSequence.length) {
                this.easterEggs.konamiCode.shift();
            }
            if (JSON.stringify(this.easterEggs.konamiCode) === JSON.stringify(this.konamiSequence)) {
                this.triggerKonamiEasterEgg();
                this.easterEggs.konamiCode = [];
            }
        });

        // Logo triple-click
        const logo = document.querySelector('.navbar-brand');
        if (logo) {
            logo.addEventListener('click', () => {
                this.easterEggs.clickCount++;
                if (this.easterEggs.clickCount >= 3) {
                    this.triggerLogoEasterEgg();
                    this.easterEggs.clickCount = 0;
                }
                setTimeout(() => { this.easterEggs.clickCount = 0; }, 1000);
            });
        }

        // Secret console commands
        window.credify = {
            matrix: () => this.triggerMatrixRain(),
            glitch: () => this.triggerGlitchEffect(),
            stats: () => this.showSecretStats(),
            hack: () => this.triggerHackAnimation(),
            credits: () => this.showCredits()
        };

        console.log('%c💡 Try typing: credify.matrix(), credify.glitch(), credify.stats()', 'color: #22d3ee;');
    }

    triggerKonamiEasterEgg() {
        console.log('%c🎮 KONAMI CODE ACTIVATED!', 'color: #10b981; font-size: 20px; font-weight: bold;');
        
        this.showBrutalistAlert('🎮 KONAMI CODE UNLOCKED! You are a true gamer! 🕹️', 'success', 5000);
        
        // Add rainbow animation to body
        document.body.style.animation = 'rainbow 2s linear';
        setTimeout(() => {
            document.body.style.animation = '';
        }, 2000);
    }

    triggerLogoEasterEgg() {
        console.log('%c⚡ LOGO EASTER EGG!', 'color: #fbbf24; font-size: 16px; font-weight: bold;');
        
        const logo = document.querySelector('.navbar-brand');
        if (logo) {
            logo.style.animation = 'glitchEffect 0.5s ease-in-out';
            setTimeout(() => {
                logo.style.animation = '';
            }, 500);
        }
        
        this.showBrutalistAlert('⚡ You found the logo secret! Welcome to the cyber realm!', 'info', 4000);
    }

    triggerMatrixRain() {
        if (this.easterEggs.matrixActive) {
            this.stopMatrixRain();
            return;
        }

        console.log('%c🌧️ MATRIX MODE: ACTIVATED', 'color: #10b981; font-size: 16px;');
        
        this.easterEggs.matrixActive = true;
        
        const canvas = document.createElement('canvas');
        canvas.id = 'matrix-canvas';
        canvas.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 9998;
            pointer-events: none;
            opacity: 0.3;
        `;
        document.body.appendChild(canvas);

        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        const chars = '01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホ';
        const fontSize = 14;
        const columns = canvas.width / fontSize;
        const drops = Array(Math.floor(columns)).fill(1);

        const matrixInterval = setInterval(() => {
            ctx.fillStyle = 'rgba(15, 23, 42, 0.05)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            ctx.fillStyle = '#06b6d4';
            ctx.font = fontSize + 'px monospace';

            for (let i = 0; i < drops.length; i++) {
                const text = chars[Math.floor(Math.random() * chars.length)];
                ctx.fillText(text, i * fontSize, drops[i] * fontSize);

                if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
                    drops[i] = 0;
                }
                drops[i]++;
            }
        }, 33);

        this.easterEggs.matrixInterval = matrixInterval;
        this.showBrutalistAlert('🌧️ MATRIX RAIN: Press ESC to exit', 'success', 3000);

        // ESC to exit
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                this.stopMatrixRain();
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);
    }

    stopMatrixRain() {
        if (!this.easterEggs.matrixActive) return;
        
        clearInterval(this.easterEggs.matrixInterval);
        const canvas = document.getElementById('matrix-canvas');
        if (canvas) canvas.remove();
        this.easterEggs.matrixActive = false;
        
        console.log('%c🌧️ MATRIX MODE: DEACTIVATED', 'color: #f59e0b;');
        this.showBrutalistAlert('Matrix rain stopped', 'info', 2000);
    }

    triggerGlitchEffect() {
        console.log('%c⚡ GLITCH EFFECT ACTIVATED!', 'color: #ef4444; font-size: 16px;');
        
        document.body.style.animation = 'glitchEffect 0.5s ease-in-out';
        setTimeout(() => {
            document.body.style.animation = '';
        }, 500);
        
        this.showBrutalistAlert('⚡ G̸̢̛L̵͝I̸̧T̴͜C̸̨H̵̡ M̴̛O̵͝D̸̢E̴͜!', 'warning', 2000);
    }

    showSecretStats() {
        console.log('%c📊 SECRET STATISTICS', 'color: #22d3ee; font-size: 16px; font-weight: bold;');
        console.table({
            'Total Page Loads': sessionStorage.getItem('pageLoads') || 1,
            'Credentials Verified': localStorage.getItem('verifiedCount') || 0,
            'Disclosures Created': localStorage.getItem('disclosureCount') || 0,
            'Easter Eggs Found': '4/5',
            'Hack Level': 'ADVANCED'
        });
        
        this.showBrutalistAlert('📊 Check console for secret stats!', 'info', 3000);
    }

    triggerHackAnimation() {
        console.log('%c🔓 INITIATING HACK SEQUENCE...', 'color: #10b981; font-size: 16px;');
        
        const messages = [
            'Connecting to blockchain...',
            'Bypassing cryptographic signatures...',
            'Accessing IPFS network...',
            'Extracting credentials...',
            'HACK COMPLETE! (Just kidding 😄)'
        ];
        
        messages.forEach((msg, index) => {
            setTimeout(() => {
                console.log(`%c[${index + 1}/5] ${msg}`, 'color: #22d3ee;');
                if (index === messages.length - 1) {
                    this.showBrutalistAlert('🔓 Nice try! System is unhackable 😎', 'success', 4000);
                }
            }, index * 800);
        });
    }

    showCredits() {
        console.log('%c' + `
╔═══════════════════════════════════════════════════════════╗
║                    CREDIFY 2026 CREDITS                   ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  👨‍💻 DEVELOPMENT TEAM:                                     ║
║     • SHASHI        - Frontend & IPFS Integration        ║
║     • UDAY          - Backend & Blockchain Logic         ║
║     • TEJA VARSHITH - System Analysis & Documentation    ║
║                                                           ║
║  🏫 INSTITUTION:                                          ║
║     G. Pulla Reddy Engineering College (Autonomous)      ║
║     Department of Computer Science & Engineering         ║
║                                                           ║
║  🎓 PROJECT:                                              ║
║     B.Tech Final Year Project (2026)                     ║
║     Blockchain-Based Verifiable Credentials System       ║
║                                                           ║
║  🛠️ TECHNOLOGIES:                                         ║
║     Python • Flask • Blockchain • IPFS • Cryptography    ║
║     Bootstrap • JavaScript • SQLAlchemy                  ║
║                                                           ║
║  🎨 DESIGN:                                               ║
║     Brutalist Cyber Aesthetic                            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        `, 'color: #06b6d4; font-weight: bold;');
        
        this.showBrutalistAlert('🎓 Check console for full credits!', 'info', 3000);
    }
}

// ============================================================
// CREDENTIAL VERIFIER CLASS
// ============================================================
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
            
            // Update localStorage counter
            const count = parseInt(localStorage.getItem('verifiedCount') || '0') + 1;
            localStorage.setItem('verifiedCount', count);
            
            console.log(`%c✅ Credential ${credentialId} verified successfully`, 'color: #10b981;');
            
            return result;
        } catch (error) {
            console.error('%c❌ Verification error:', 'color: #ef4444;', error);
            throw error;
        }
    }

    getVerificationHistory() {
        return this.verificationHistory;
    }

    clearVerificationHistory() {
        this.verificationHistory = [];
        console.log('%c🗑️ Verification history cleared', 'color: #f59e0b;');
    }
}

// ============================================================
// SELECTIVE DISCLOSURE CLASS
// ============================================================
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
            
            // Update localStorage counter
            const count = parseInt(localStorage.getItem('disclosureCount') || '0') + 1;
            localStorage.setItem('disclosureCount', count);
            
            console.log(`%c🔐 Selective disclosure created for ${credentialId}`, 'color: #22d3ee;');
            
            return result;
        } catch (error) {
            console.error('%c❌ Disclosure error:', 'color: #ef4444;', error);
            throw error;
        }
    }

    getDisclosureHistory() {
        return this.disclosureHistory;
    }
}

// ============================================================
// INITIALIZATION
// ============================================================
document.addEventListener('DOMContentLoaded', function() {
    // Track page loads
    const pageLoads = parseInt(sessionStorage.getItem('pageLoads') || '0') + 1;
    sessionStorage.setItem('pageLoads', pageLoads);
    
    // Initialize main system
    window.credentialSystem = new CredentialSystem();
    window.credentialVerifier = new CredentialVerifier();
    window.selectiveDisclosure = new SelectiveDisclosure();
    
    console.log('%c✅ Blockchain Verifiable Credentials System Loaded Successfully', 'color: #10b981; font-weight: bold; font-size: 14px;');
    console.log('%c🎨 Brutalist Cyber Design: Active', 'color: #22d3ee;');
});

// Export for use in other scripts
window.CredentialSystem = CredentialSystem;
window.CredentialVerifier = CredentialVerifier;
window.SelectiveDisclosure = SelectiveDisclosure;

// ============================================================
// GLOBAL ERROR HANDLING
// ============================================================
window.addEventListener('error', function(e) {
    console.error('%c❌ JavaScript Error:', 'color: #ef4444; font-weight: bold;', e.error);
    
    if (window.credentialSystem) {
        window.credentialSystem.showAlert(
            '❌ An unexpected error occurred. Please refresh and try again.',
            'danger'
        );
    }
});

// ============================================================
// ONLINE/OFFLINE DETECTION
// ============================================================
window.addEventListener('online', function() {
    console.log('%c🌐 Connection Restored', 'color: #10b981; font-weight: bold;');
    if (window.credentialSystem) {
        window.credentialSystem.showAlert('🌐 Connection restored', 'success', 3000);
        window.credentialSystem.updateBlockchainStatus();
    }
});

window.addEventListener('offline', function() {
    console.log('%c⚠️ Connection Lost', 'color: #f59e0b; font-weight: bold;');
    if (window.credentialSystem) {
        window.credentialSystem.showAlert(
            '⚠️ Connection lost. Some features may not work properly.',
            'warning'
        );
    }
});

// ============================================================
// CONSOLE EASTER EGG MESSAGE
// ============================================================
setTimeout(() => {
    console.log('%c', '');
    console.log('%c💡 Pro Tip:', 'color: #fbbf24; font-weight: bold; font-size: 14px;');
    console.log('%cTry these commands:', 'color: #94a3b8;');
    console.log('%ccredify.matrix()  %c- Toggle Matrix rain effect', 'color: #22d3ee;', 'color: #94a3b8;');
    console.log('%ccredify.glitch()  %c- Trigger glitch animation', 'color: #22d3ee;', 'color: #94a3b8;');
    console.log('%ccredify.stats()   %c- View secret statistics', 'color: #22d3ee;', 'color: #94a3b8;');
    console.log('%ccredify.hack()    %c- Initiate "hack" sequence', 'color: #22d3ee;', 'color: #94a3b8;');
    console.log('%ccredify.credits() %c- View full credits', 'color: #22d3ee;', 'color: #94a3b8;');
    console.log('%c', '');
}, 2000);
