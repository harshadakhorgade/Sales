/**
 * Simple Toast Notification System
 * Based on the working referral link copy button approach
 */

// Simple toast function that works like the referral link copy button
function showToast(message, type = 'info') {
    // Remove existing toast if any
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    // Create new toast
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    // Add styling based on type
    let bgColor = '#007bff'; // Default blue
    let textColor = '#fff';
    
    if (type === 'success') {
        bgColor = '#28a745';
    } else if (type === 'error') {
        bgColor = '#dc3545';
    } else if (type === 'warning') {
        bgColor = '#ffc107';
        textColor = '#000';
    }
    
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${bgColor};
        color: ${textColor};
        padding: 15px 20px;
        border-radius: 5px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 9999;
        font-size: 14px;
        font-weight: 500;
        max-width: 300px;
        word-wrap: break-word;
        transform: translateX(100%);
        transition: transform 0.3s ease-in-out;
    `;
    
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // Slide in animation
    setTimeout(() => {
        toast.style.transform = 'translateX(0)';
    }, 10);
    
    // Remove toast after 3 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }
    }, 3000);
}

// Process Django messages and convert to simple toasts
function processDjangoMessages() {
    const messageElements = document.querySelectorAll('.alert-message:not(.toast-processed)');
    
    messageElements.forEach(element => {
        // Mark as processed
        element.classList.add('toast-processed');
        
        const message = element.textContent.trim();
        const closeButton = element.querySelector('.close-message');
        let cleanMessage = message;
        if (closeButton) {
            cleanMessage = message.replace(closeButton.textContent, '').trim();
        }
        
        if (!cleanMessage) return;
        
        // Determine message type
        let type = 'info';
        if (cleanMessage.includes('success') || cleanMessage.includes('Success') || cleanMessage.includes('successful') || cleanMessage.includes('Successfully') || cleanMessage.includes('added to cart') || cleanMessage.includes('withdrawal') || cleanMessage.includes('initiated')) {
            type = 'success';
        } else if (cleanMessage.includes('error') || cleanMessage.includes('Error') || cleanMessage.includes('failed') || cleanMessage.includes('Failed') || cleanMessage.includes('❌') || cleanMessage.includes('Invalid') || cleanMessage.includes('Please correct')) {
            type = 'error';
        } else if (cleanMessage.includes('warning') || cleanMessage.includes('Warning') || cleanMessage.includes('⚠') || cleanMessage.includes('expired') || cleanMessage.includes('session')) {
            type = 'warning';
        }
        
        // Show simple toast
        showToast(cleanMessage, type);
        
        // Hide original message
        element.style.display = 'none';
    });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', processDjangoMessages);
} else {
    processDjangoMessages();
}

// Global functions for easy access
window.showToast = showToast;
window.showSuccess = (message) => showToast(message, 'success');
window.showError = (message) => showToast(message, 'error');
window.showWarning = (message) => showToast(message, 'warning');
window.showInfo = (message) => showToast(message, 'info');

// Handle page visibility change to pause/resume auto-dismiss
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Pause auto-dismiss when page is hidden
        toastNotification.toasts.forEach(toast => {
            const progressBar = toast.querySelector('.toast-progress');
            if (progressBar) {
                progressBar.style.animationPlayState = 'paused';
            }
        });
    } else {
        // Resume auto-dismiss when page is visible
        toastNotification.toasts.forEach(toast => {
            const progressBar = toast.querySelector('.toast-progress');
            if (progressBar) {
                progressBar.style.animationPlayState = 'running';
            }
        });
    }
});
