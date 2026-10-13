/**
 * ExamGuard AI — Main JavaScript
 * Complete interactive UI/UX feature suite:
 * Theme, Search, Modals, Loading, Mobile Menu, Clipboard, Scroll Progress, Cookies.
 */

document.addEventListener('DOMContentLoaded', function () {
    initTheme();
    initMobileSidebar();
    initScrollProgress();
    initBackToTop();
    initCookieBanner();
    initPasswordToggles();
    initCopyButtons();
    initConfirmModals();
    initGlobalSearch();
    initFormLoadingStates();
    initFlashAlerts();
});

// ── 1. THEME TOGGLE ──
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || localStorage.getItem('examguard_theme') || 'dark';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
    localStorage.setItem('theme', savedTheme);
    localStorage.setItem('examguard_theme', savedTheme);
    updateAllThemeIcons(savedTheme);

    const toggleButtons = document.querySelectorAll('.theme-toggle-btn, #theme-toggle');
    toggleButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const currentTheme = document.documentElement.getAttribute('data-bs-theme') || 'dark';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

            document.documentElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            localStorage.setItem('examguard_theme', newTheme);
            updateAllThemeIcons(newTheme);
            document.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: newTheme } }));
        });
    });
}

function updateAllThemeIcons(theme) {
    const icons = document.querySelectorAll('#theme-icon, .theme-icon');
    icons.forEach(icon => {
        if (theme === 'dark') {
            icon.className = 'bi bi-moon-stars-fill';
        } else {
            icon.className = 'bi bi-sun-fill';
        }
    });
}

// ── 2. MOBILE MENU & SIDEBAR DRAWER ──
function initMobileSidebar() {
    const toggleBtn = document.getElementById('sidebar-toggle-btn');
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');

    if (!sidebar) return;

    function openSidebar() {
        sidebar.classList.add('show');
        if (backdrop) backdrop.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        sidebar.classList.remove('show');
        if (backdrop) backdrop.classList.remove('show');
        document.body.style.overflow = '';
    }

    if (toggleBtn) {
        toggleBtn.addEventListener('click', function () {
            if (sidebar.classList.contains('show')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
    }

    if (backdrop) {
        backdrop.addEventListener('click', closeSidebar);
    }

    // Close sidebar on link click on small screens
    const navLinks = sidebar.querySelectorAll('.sidebar-nav a');
    navLinks.forEach(link => {
        link.addEventListener('click', function () {
            if (window.innerWidth < 768) {
                closeSidebar();
            }
        });
    });

    // Close on Escape key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && sidebar.classList.contains('show')) {
            closeSidebar();
        }
    });
}

// ── 3. SCROLL PROGRESS BAR ──
function initScrollProgress() {
    const progressBar = document.getElementById('scroll-progress');
    if (!progressBar) return;

    window.addEventListener('scroll', function () {
        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        if (scrollHeight > 100) {
            const percentage = Math.min(100, Math.max(0, (scrollTop / scrollHeight) * 100));
            progressBar.style.width = percentage + '%';
            progressBar.setAttribute('aria-valuenow', Math.round(percentage));
            progressBar.style.display = 'block';
        } else {
            progressBar.style.display = 'none';
        }
    }, { passive: true });
}

// ── 4. BACK TO TOP BUTTON ──
function initBackToTop() {
    const backToTopBtn = document.getElementById('back-to-top');
    if (!backToTopBtn) return;

    window.addEventListener('scroll', function () {
        if (window.scrollY > 250) {
            backToTopBtn.classList.add('show');
        } else {
            backToTopBtn.classList.remove('show');
        }
    }, { passive: true });

    backToTopBtn.addEventListener('click', function () {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// ── 5. COOKIE & STORAGE BANNER ──
function initCookieBanner() {
    const banner = document.getElementById('cookie-consent-banner');
    const acceptBtn = document.getElementById('cookie-accept-btn');
    if (!banner || !acceptBtn) return;

    const consentGiven = localStorage.getItem('cookie_consent_accepted');
    if (!consentGiven) {
        banner.style.display = 'block';
    }

    acceptBtn.addEventListener('click', function () {
        localStorage.setItem('cookie_consent_accepted', 'true');
        banner.style.opacity = '0';
        banner.style.transition = 'opacity 0.3s ease';
        setTimeout(() => {
            banner.style.display = 'none';
        }, 300);
    });
}

// ── 6. PASSWORD VISIBILITY TOGGLE ──
function initPasswordToggles() {
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('#togglePassword, .password-toggle-btn');
        if (!btn) return;

        // Find associated password input
        let input = null;
        if (btn.dataset.target) {
            input = document.querySelector(btn.dataset.target);
        } else {
            const group = btn.closest('.input-group');
            if (group) input = group.querySelector('input[type="password"], input[type="text"]');
        }

        if (!input) return;

        const icon = btn.querySelector('i');
        const isPassword = input.type === 'password';

        input.type = isPassword ? 'text' : 'password';
        btn.setAttribute('aria-pressed', isPassword ? 'true' : 'false');
        btn.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');

        if (icon) {
            if (isPassword) {
                icon.className = 'bi bi-eye-slash-fill';
            } else {
                icon.className = 'bi bi-eye-fill';
            }
        }
    });
}

// ── 7. UNIVERSAL COPY TO CLIPBOARD ──
function initCopyButtons() {
    document.addEventListener('click', function (e) {
        const copyBtn = e.target.closest('.btn-copy, [data-copy]');
        if (!copyBtn) return;

        let textToCopy = copyBtn.getAttribute('data-copy');
        if (!textToCopy && copyBtn.dataset.copyTarget) {
            const targetEl = document.querySelector(copyBtn.dataset.copyTarget);
            if (targetEl) textToCopy = targetEl.textContent.trim();
        }
        if (!textToCopy) {
            // Check previous sibling or parent text
            const prev = copyBtn.previousElementSibling;
            if (prev) textToCopy = prev.textContent.trim();
        }

        if (!textToCopy) return;

        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(textToCopy).then(() => {
                showCopySuccess(copyBtn);
            }).catch(err => {
                fallbackCopy(textToCopy, copyBtn);
            });
        } else {
            fallbackCopy(textToCopy, copyBtn);
        }
    });
}

function showCopySuccess(btn) {
    const originalHtml = btn.innerHTML;
    btn.classList.add('copied');
    btn.innerHTML = '<i class="bi bi-check2"></i> Copied!';
    setTimeout(() => {
        btn.classList.remove('copied');
        btn.innerHTML = originalHtml;
    }, 2000);
}

function fallbackCopy(text, btn) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try {
        document.execCommand('copy');
        showCopySuccess(btn);
    } catch (e) {
        console.warn('Copy failed:', e);
    }
    document.body.removeChild(textarea);
}

// ── 8. REUSABLE CONFIRMATION MODALS ──
function initConfirmModals() {
    const confirmModalEl = document.getElementById('confirmActionModal');
    if (!confirmModalEl) return;

    let targetForm = null;
    let targetLink = null;
    const titleEl = document.getElementById('confirmModalTitle');
    const msgEl = document.getElementById('confirmModalMessage');
    const submitBtn = document.getElementById('confirmModalSubmitBtn');

    document.addEventListener('click', function (e) {
        const trigger = e.target.closest('[data-confirm]');
        if (!trigger) return;

        e.preventDefault();
        targetForm = trigger.closest('form');
        targetLink = trigger.tagName === 'A' ? trigger : null;

        const confirmMsg = trigger.getAttribute('data-confirm') || 'Are you sure you want to proceed?';
        const confirmTitle = trigger.getAttribute('data-confirm-title') || 'Confirm Action';
        const btnText = trigger.getAttribute('data-confirm-btn') || 'Confirm';

        if (titleEl) titleEl.textContent = confirmTitle;
        if (msgEl) msgEl.textContent = confirmMsg;
        if (submitBtn) {
            const btnTextSpan = submitBtn.querySelector('.confirm-btn-text');
            if (btnTextSpan) btnTextSpan.textContent = btnText;
            submitBtn.disabled = false;
        }

        const modal = bootstrap.Modal.getOrCreateInstance(confirmModalEl);
        modal.show();
    });

    if (submitBtn) {
        submitBtn.addEventListener('click', function () {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Processing...';

            if (targetForm) {
                targetForm.submit();
            } else if (targetLink && targetLink.href) {
                window.location.href = targetLink.href;
            }
        });
    }
}

// ── 9. SITE SEARCH (CTRL+K & LIVE API) ──
function initGlobalSearch() {
    const searchModalEl = document.getElementById('searchModal');
    const searchInput = document.getElementById('globalSearchInput');
    const resultsContainer = document.getElementById('searchResultsList');
    const loadingIndicator = document.getElementById('searchLoading');

    // Shortcut: Ctrl+K / Cmd+K
    document.addEventListener('keydown', function (e) {
        if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
            e.preventDefault();
            if (searchModalEl) {
                const modal = bootstrap.Modal.getOrCreateInstance(searchModalEl);
                modal.show();
            }
        }
    });

    if (searchModalEl && searchInput) {
        searchModalEl.addEventListener('shown.bs.modal', function () {
            searchInput.focus();
            searchInput.select();
        });

        let debounceTimer = null;
        searchInput.addEventListener('input', function () {
            clearTimeout(debounceTimer);
            const query = this.value.trim();

            if (query.length < 2) {
                renderEmptySearch("Type at least 2 characters to search records.");
                return;
            }

            if (loadingIndicator) loadingIndicator.classList.remove('d-none');

            debounceTimer = setTimeout(() => {
                fetch(`/api/search?q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        if (loadingIndicator) loadingIndicator.classList.add('d-none');
                        renderSearchResults(data.results || [], query);
                    })
                    .catch(err => {
                        if (loadingIndicator) loadingIndicator.classList.add('d-none');
                        renderEmptySearch("An error occurred while searching. Please try again.");
                    });
            }, 250);
        });
    }

    function renderEmptySearch(message) {
        if (!resultsContainer) return;
        resultsContainer.innerHTML = `
            <div class="text-center text-muted py-5 empty-search-state">
                <i class="bi bi-search fs-2 d-block mb-2 text-accent opacity-50"></i>
                <p class="mb-1">${message}</p>
                <small class="text-muted">Results are filtered by your authorization role.</small>
            </div>
        `;
    }

    function renderSearchResults(results, query) {
        if (!resultsContainer) return;

        if (results.length === 0) {
            resultsContainer.innerHTML = `
                <div class="text-center text-muted py-5 empty-search-state">
                    <i class="bi bi-emoji-neutral fs-2 d-block mb-2 text-warning opacity-75"></i>
                    <p class="mb-1 fw-semibold text-primary">No matching records found for "${query}"</p>
                    <small class="text-muted">Try checking the spelling or searching by code, room, or name.</small>
                </div>
            `;
            return;
        }

        let html = '';
        results.forEach(item => {
            html += `
                <a href="${item.url}" class="search-item list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                    <div>
                        <div class="d-flex align-items-center gap-2 mb-1">
                            <span class="badge bg-${item.badge_color || 'secondary'}">${item.badge}</span>
                            <strong class="text-primary">${item.title}</strong>
                        </div>
                        <small class="text-muted">${item.subtitle}</small>
                    </div>
                    <i class="bi bi-chevron-right text-muted small"></i>
                </a>
            `;
        });
        resultsContainer.innerHTML = html;
    }
}

// ── 10. FORM LOADING STATES & DUPLICATE SUBMISSION PREVENTION ──
function initFormLoadingStates() {
    document.addEventListener('submit', function (e) {
        const form = e.target;
        if (!form || form.hasAttribute('data-no-loading')) return;

        // Validate first if required fields exist
        if (!form.checkValidity()) {
            return; // Let browser HTML5 validation handle invalid states
        }

        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn && !submitBtn.disabled) {
            // Prevent immediate duplicate clicks
            const originalText = submitBtn.innerHTML;
            submitBtn.dataset.originalText = originalText;
            submitBtn.disabled = true;

            const loadingText = submitBtn.dataset.loadingText || 'Processing...';
            submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>${loadingText}`;

            // Safety timeout: if page doesn't unload in 8s, restore button
            setTimeout(() => {
                if (submitBtn.disabled) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }
            }, 8000);
        }
    });
}

// ── 11. AUTO-DISMISS FLASH ALERTS ──
function initFlashAlerts() {
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            if (document.body.contains(alert)) {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            }
        }, 5000);
    });
}
