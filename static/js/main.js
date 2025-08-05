/**
 * Main JavaScript file for Gen Z Accounts Submission
 * Handles global functionality and utilities
 */

// Global application object
window.GenZApp = {
    // Configuration
    config: {
        apiEndpoint: '/api',
        refreshInterval: 30000, // 30 seconds
        toastDuration: 3000, // 3 seconds
        debounceDelay: 300, // 300ms
    },
    
    // Utility functions
    utils: {},
    
    // Components
    components: {},
    
    // Initialize application
    init: function() {
        this.utils.init();
        this.components.init();
        this.bindGlobalEvents();
        this.checkSession();
    }
};

// Utility functions
GenZApp.utils = {
    init: function() {
        console.log('Initializing utilities...');
    },
    
    // Format currency
    formatCurrency: function(amount, currency = 'TK') {
        return parseFloat(amount).toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }) + ' ' + currency;
    },
    
    // Format number with commas
    formatNumber: function(number) {
        return parseFloat(number).toLocaleString('en-US');
    },
    
    // Format date
    formatDate: function(date, format = 'short') {
        const dateObj = new Date(date);
        const options = format === 'short' 
            ? { month: 'short', day: 'numeric', year: 'numeric' }
            : { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        
        return dateObj.toLocaleDateString('en-US', options);
    },
    
    // Format time ago
    timeAgo: function(date) {
        const now = new Date();
        const past = new Date(date);
        const diffTime = Math.abs(now - past);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
        if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
        return `${Math.floor(diffDays / 365)} years ago`;
    },
    
    // Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Copy to clipboard
    copyToClipboard: function(text, successMessage = 'Copied to clipboard!') {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                this.showToast(successMessage, 'success');
            }).catch(() => {
                this.fallbackCopy(text, successMessage);
            });
        } else {
            this.fallbackCopy(text, successMessage);
        }
    },
    
    // Fallback copy method
    fallbackCopy: function(text, successMessage) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            this.showToast(successMessage, 'success');
        } catch (err) {
            this.showToast('Failed to copy', 'error');
        }
        
        document.body.removeChild(textArea);
    },
    
    // Show toast notification
    showToast: function(message, type = 'info', duration = null) {
        duration = duration || GenZApp.config.toastDuration;
        
        const toastHtml = `
            <div class="toast show position-fixed top-0 end-0 m-3" style="z-index: 9999;" role="alert">
                <div class="toast-header">
                    <i class="fas fa-${this.getToastIcon(type)} text-${type} me-2"></i>
                    <strong class="me-auto">${this.getToastTitle(type)}</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">${message}</div>
            </div>
        `;
        
        const toastElement = document.createElement('div');
        toastElement.innerHTML = toastHtml;
        document.body.appendChild(toastElement.firstElementChild);
        
        // Auto remove after duration
        setTimeout(() => {
            const toastEl = document.querySelector('.toast');
            if (toastEl) {
                toastEl.remove();
            }
        }, duration);
    },
    
    getToastIcon: function(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || icons.info;
    },
    
    getToastTitle: function(type) {
        const titles = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Info'
        };
        return titles[type] || titles.info;
    },
    
    // Validate email
    isValidEmail: function(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    // Validate phone number (basic)
    isValidPhone: function(phone) {
        const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
        return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''));
    },
    
    // Format file size
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // Get file extension
    getFileExtension: function(filename) {
        return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2);
    },
    
    // Validate file type
    isValidFileType: function(filename, allowedTypes = ['.xlsx', '.xls', '.csv', '.txt']) {
        const extension = '.' + this.getFileExtension(filename).toLowerCase();
        return allowedTypes.includes(extension);
    }
};

// Components
GenZApp.components = {
    init: function() {
        this.initDataTables();
        this.initTooltips();
        this.initPopovers();
        this.initFormValidation();
        this.initFileUpload();
        this.initSearchFilters();
    },
    
    // Initialize DataTables if present
    initDataTables: function() {
        if (typeof $.fn.DataTable !== 'undefined') {
            $('.data-table').DataTable({
                responsive: true,
                pageLength: 25,
                order: [[0, 'desc']],
                language: {
                    search: "Search records:",
                    lengthMenu: "Show _MENU_ entries per page",
                    info: "Showing _START_ to _END_ of _TOTAL_ entries",
                    paginate: {
                        first: "First",
                        last: "Last",
                        next: "Next",
                        previous: "Previous"
                    }
                }
            });
        }
    },
    
    // Initialize Bootstrap tooltips
    initTooltips: function() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    },
    
    // Initialize Bootstrap popovers
    initPopovers: function() {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    },
    
    // Initialize form validation
    initFormValidation: function() {
        // Custom validation for forms
        const forms = document.querySelectorAll('.needs-validation');
        Array.from(forms).forEach(form => {
            form.addEventListener('submit', event => {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        });
        
        // Real-time validation
        document.querySelectorAll('input[type="email"]').forEach(input => {
            input.addEventListener('blur', function() {
                if (this.value && !GenZApp.utils.isValidEmail(this.value)) {
                    this.setCustomValidity('Please enter a valid email address');
                } else {
                    this.setCustomValidity('');
                }
            });
        });
        
        document.querySelectorAll('input[type="tel"]').forEach(input => {
            input.addEventListener('blur', function() {
                if (this.value && !GenZApp.utils.isValidPhone(this.value)) {
                    this.setCustomValidity('Please enter a valid phone number');
                } else {
                    this.setCustomValidity('');
                }
            });
        });
    },
    
    // Initialize file upload handling
    initFileUpload: function() {
        document.querySelectorAll('input[type="file"]').forEach(input => {
            input.addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (!file) return;
                
                // Validate file size (10MB limit)
                if (file.size > 10 * 1024 * 1024) {
                    GenZApp.utils.showToast('File too large. Maximum size is 10MB.', 'error');
                    this.value = '';
                    return;
                }
                
                // Validate file type
                if (!GenZApp.utils.isValidFileType(file.name)) {
                    GenZApp.utils.showToast('Invalid file type. Please upload Excel, CSV, or text files.', 'error');
                    this.value = '';
                    return;
                }
                
                // Show file info
                const fileInfo = `${file.name} (${GenZApp.utils.formatFileSize(file.size)})`;
                GenZApp.utils.showToast(`File selected: ${fileInfo}`, 'success');
            });
        });
    },
    
    // Initialize search and filter functionality
    initSearchFilters: function() {
        const searchInputs = document.querySelectorAll('.search-filter');
        searchInputs.forEach(input => {
            const debouncedSearch = GenZApp.utils.debounce((value) => {
                this.performSearch(value, input.dataset.target);
            }, GenZApp.config.debounceDelay);
            
            input.addEventListener('input', (e) => {
                debouncedSearch(e.target.value);
            });
        });
    },
    
    // Perform search
    performSearch: function(query, target) {
        const targetElements = document.querySelectorAll(target);
        targetElements.forEach(element => {
            const text = element.textContent.toLowerCase();
            const matches = text.includes(query.toLowerCase());
            element.style.display = matches ? '' : 'none';
        });
    }
};

// Global event handlers
GenZApp.bindGlobalEvents = function() {
    // Handle copy buttons
    document.addEventListener('click', function(e) {
        if (e.target.matches('.copy-btn') || e.target.closest('.copy-btn')) {
            const btn = e.target.matches('.copy-btn') ? e.target : e.target.closest('.copy-btn');
            const textToCopy = btn.dataset.copy || btn.textContent;
            GenZApp.utils.copyToClipboard(textToCopy);
        }
    });
    
    // Handle form submissions with loading states
    document.addEventListener('submit', function(e) {
        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        
        if (submitBtn && !submitBtn.disabled) {
            const originalText = submitBtn.innerHTML;
            const loadingText = submitBtn.dataset.loading || '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
            
            submitBtn.disabled = true;
            submitBtn.innerHTML = loadingText;
            
            // Re-enable after 10 seconds as fallback
            setTimeout(() => {
                if (submitBtn.disabled) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }
            }, 10000);
        }
    });
    
    // Handle AJAX requests
    document.addEventListener('click', function(e) {
        if (e.target.matches('.ajax-btn') || e.target.closest('.ajax-btn')) {
            e.preventDefault();
            const btn = e.target.matches('.ajax-btn') ? e.target : e.target.closest('.ajax-btn');
            GenZApp.handleAjaxRequest(btn);
        }
    });
    
    // Handle keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for search focus
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="search"], input[name="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const modal = bootstrap.Modal.getInstance(openModal);
                if (modal) {
                    modal.hide();
                }
            }
        }
    });
    
    // Auto-save form data to localStorage
    document.addEventListener('input', GenZApp.utils.debounce(function(e) {
        if (e.target.matches('.auto-save')) {
            const key = `genZ_autosave_${e.target.name || e.target.id}`;
            localStorage.setItem(key, e.target.value);
        }
    }, 1000));
    
    // Restore auto-saved data
    document.querySelectorAll('.auto-save').forEach(input => {
        const key = `genZ_autosave_${input.name || input.id}`;
        const savedValue = localStorage.getItem(key);
        if (savedValue && !input.value) {
            input.value = savedValue;
        }
    });
};

// Handle AJAX requests
GenZApp.handleAjaxRequest = function(element) {
    const url = element.dataset.url || element.href;
    const method = element.dataset.method || 'GET';
    const target = element.dataset.target;
    const confirm = element.dataset.confirm;
    
    if (confirm && !window.confirm(confirm)) {
        return;
    }
    
    // Show loading state
    const originalText = element.innerHTML;
    element.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    element.disabled = true;
    
    fetch(url, {
        method: method,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            GenZApp.utils.showToast(data.message || 'Operation completed successfully', 'success');
            
            if (target) {
                const targetElement = document.querySelector(target);
                if (targetElement && data.html) {
                    targetElement.innerHTML = data.html;
                }
            }
            
            if (data.redirect) {
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 1000);
            } else if (data.reload) {
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        } else {
            GenZApp.utils.showToast(data.message || 'Operation failed', 'error');
        }
    })
    .catch(error => {
        console.error('AJAX Error:', error);
        GenZApp.utils.showToast('An error occurred. Please try again.', 'error');
    })
    .finally(() => {
        element.innerHTML = originalText;
        element.disabled = false;
    });
};

// Check session and handle timeout
GenZApp.checkSession = function() {
    const checkInterval = 5 * 60 * 1000; // 5 minutes
    
    setInterval(() => {
        fetch('/auth/check-session', {
            method: 'POST',
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (!data.valid) {
                GenZApp.utils.showToast('Your session has expired. Please log in again.', 'warning');
                setTimeout(() => {
                    window.location.href = '/auth/login';
                }, 3000);
            }
        })
        .catch(() => {
            // Ignore session check errors
        });
    }, checkInterval);
};

// Auto-refresh functionality for admin pages
GenZApp.initAutoRefresh = function() {
    if (window.location.pathname.includes('/admin/')) {
        const refreshInterval = 2 * 60 * 1000; // 2 minutes for admin pages
        
        setInterval(() => {
            // Only refresh if page is visible and user is not interacting
            if (!document.hidden && Date.now() - GenZApp.lastInteraction > 30000) {
                const refreshElements = document.querySelectorAll('.auto-refresh');
                refreshElements.forEach(element => {
                    const url = element.dataset.refreshUrl || window.location.href;
                    fetch(url)
                        .then(response => response.text())
                        .then(html => {
                            const parser = new DOMParser();
                            const doc = parser.parseFromString(html, 'text/html');
                            const newElement = doc.querySelector('#' + element.id);
                            if (newElement) {
                                element.innerHTML = newElement.innerHTML;
                            }
                        })
                        .catch(() => {
                            // Ignore refresh errors
                        });
                });
            }
        }, refreshInterval);
    }
};

// Track user interaction for auto-refresh
GenZApp.lastInteraction = Date.now();
document.addEventListener('click', () => {
    GenZApp.lastInteraction = Date.now();
});
document.addEventListener('keypress', () => {
    GenZApp.lastInteraction = Date.now();
});

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    GenZApp.init();
    GenZApp.initAutoRefresh();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        // Page became visible, update last interaction
        GenZApp.lastInteraction = Date.now();
    }
});

// Export for global access
window.GenZApp = GenZApp;
