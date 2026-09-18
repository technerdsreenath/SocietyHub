/**
 * SocietyHub Global Loading & Route Transition Controller
 * Provides an ultra-smooth top progress bar & centered glassmorphic loading indicator
 * whenever navigation, form submission, or file opening occurs.
 */

(function () {
    'use strict';

    let progressInterval = null;
    let currentProgress = 0;
    let showModalTimeout = null;
    let safetyTimeout = null;

    // Build or get elements
    function ensureLoaderElements() {
        let progressBar = document.getElementById('societyhub-progress-bar');
        if (!progressBar) {
            progressBar = document.createElement('div');
            progressBar.id = 'societyhub-progress-bar';
            document.documentElement.appendChild(progressBar);
        }

        let modalOverlay = document.getElementById('societyhub-global-loader');
        if (!modalOverlay) {
            modalOverlay = document.createElement('div');
            modalOverlay.id = 'societyhub-global-loader';
            modalOverlay.setAttribute('aria-hidden', 'true');
            modalOverlay.innerHTML = `
                <div id="societyhub-loader-card" class="flex flex-col items-center">
                    <div class="societyhub-spinner-ring">
                        <div class="societyhub-spinner-pulse"></div>
                        <div class="societyhub-spinner-track"></div>
                        <div class="societyhub-spinner-blade"></div>
                        <div class="societyhub-spinner-core">
                            <!-- SocietyHub Building Emblem SVG -->
                            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/>
                                <path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/>
                                <path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/>
                                <path d="M10 6h4"/>
                                <path d="M10 10h4"/>
                                <path d="M10 14h4"/>
                                <path d="M10 18h4"/>
                            </svg>
                        </div>
                    </div>
                    <div class="space-y-1 text-center">
                        <h3 id="societyhub-loader-title" class="text-sm font-bold text-slate-800 tracking-tight">
                            Opening...
                        </h3>
                        <p id="societyhub-loader-subtitle" class="text-xs text-slate-500 font-medium flex items-center justify-center">
                            <span>Please wait</span>
                            <span class="inline-flex items-center ml-1">
                                <span class="loader-dot"></span>
                                <span class="loader-dot"></span>
                                <span class="loader-dot"></span>
                            </span>
                        </p>
                    </div>
                </div>
            `;
            document.body ? document.body.appendChild(modalOverlay) : document.documentElement.appendChild(modalOverlay);
        }

        return { progressBar, modalOverlay };
    }

    const Loader = {
        /**
         * Starts the top progress bar with dynamic trickle
         */
        startProgress: function () {
            const { progressBar } = ensureLoaderElements();
            if (!progressBar) return;

            clearInterval(progressInterval);
            currentProgress = Math.max(currentProgress, 10);
            progressBar.classList.add('active');
            progressBar.style.opacity = '1';
            progressBar.style.width = currentProgress + '%';

            progressInterval = setInterval(() => {
                if (currentProgress < 70) {
                    currentProgress += Math.random() * 12 + 4;
                } else if (currentProgress < 90) {
                    currentProgress += Math.random() * 3 + 1;
                }
                progressBar.style.width = Math.min(currentProgress, 94) + '%';
            }, 180);
        },

        /**
         * Sets specific progress percentage
         */
        setProgress: function (pct) {
            const { progressBar } = ensureLoaderElements();
            if (!progressBar) return;
            currentProgress = pct;
            progressBar.style.width = pct + '%';
        },

        /**
         * Finishes progress bar with smooth slide to 100% and fade out
         */
        finishProgress: function () {
            const { progressBar } = ensureLoaderElements();
            if (!progressBar) return;

            clearInterval(progressInterval);
            currentProgress = 100;
            progressBar.style.width = '100%';

            setTimeout(() => {
                progressBar.style.opacity = '0';
                setTimeout(() => {
                    progressBar.classList.remove('active');
                    progressBar.style.width = '0%';
                    currentProgress = 0;
                }, 300);
            }, 200);
        },

        /**
         * Displays the centered loading screen overlay
         * @param {string} [title="Opening..."]
         * @param {string} [subtitle="Please wait"]
         */
        show: function (title = 'Opening...', subtitle = 'Please wait') {
            const { modalOverlay } = ensureLoaderElements();
            this.startProgress();

            const titleEl = document.getElementById('societyhub-loader-title');
            if (titleEl) titleEl.innerText = title;

            clearTimeout(showModalTimeout);
            showModalTimeout = setTimeout(() => {
                if (modalOverlay) {
                    modalOverlay.classList.add('active');
                    modalOverlay.setAttribute('aria-hidden', 'false');
                }
            }, 60);

            // Safety timeout to avoid permanent freeze if navigation fails
            clearTimeout(safetyTimeout);
            safetyTimeout = setTimeout(() => {
                Loader.hide();
            }, 8000);
        },

        /**
         * Hides the loading screen and completes progress
         */
        hide: function () {
            clearTimeout(showModalTimeout);
            clearTimeout(safetyTimeout);
            const modalOverlay = document.getElementById('societyhub-global-loader');
            if (modalOverlay) {
                modalOverlay.classList.remove('active');
                modalOverlay.setAttribute('aria-hidden', 'true');
            }
            this.finishProgress();
        }
    };

    // Expose API globally
    window.SocietyHubLoader = Loader;
    window.showLoading = (title, subtitle) => Loader.show(title, subtitle);
    window.hideLoading = () => Loader.hide();

    // Initial page load progress
    Loader.startProgress();

    function onPageReady() {
        Loader.finishProgress();
    }

    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(onPageReady, 100);
    } else {
        window.addEventListener('DOMContentLoaded', onPageReady);
        window.addEventListener('load', onPageReady);
    }

    // Handle BFCache (back/forward button restorations)
    window.addEventListener('pageshow', function (event) {
        Loader.hide();
    });

    // Close on Escape key press for safety
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            Loader.hide();
        }
    });

    // Auto-intercept navigation links
    document.addEventListener('click', function (e) {
        const link = e.target.closest('a');
        if (!link) return;

        // Skip modifiers (Ctrl+click, Cmd+click, etc.)
        if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey || e.button !== 0) return;

        // Skip blank targets, javascript, hash anchors, mailto, tel
        const href = link.getAttribute('href');
        const target = link.getAttribute('target');
        if (!href || href.startsWith('#') || href.startsWith('javascript:') || href.startsWith('mailto:') || href.startsWith('tel:') || target === '_blank') {
            return;
        }

        // Check origin
        try {
            const url = new URL(link.href, window.location.origin);
            if (url.origin !== window.location.origin) return;

            // Same page hash anchor check
            if (url.pathname === window.location.pathname && url.search === window.location.search && url.hash) {
                return;
            }

            // Detect download links
            const isDownload = link.hasAttribute('download') || url.pathname.includes('/pdf/') || url.pathname.endsWith('.pdf') || url.pathname.includes('download_bill_pdf');
            if (isDownload) {
                Loader.startProgress();
                if (window.showToast) {
                    window.showToast('Preparing download...', 'info', 2000);
                }
                setTimeout(() => Loader.finishProgress(), 2200);
                return;
            }

            // Check after event propagation if click was cancelled (e.g. by another listener)
            setTimeout(() => {
                if (e.defaultPrevented) {
                    Loader.hide();
                    return;
                }
            }, 10);

            // Determine appropriate contextual text
            let actionText = 'Opening...';
            const rawText = (link.innerText || '').trim().replace(/\s+/g, ' ');
            if (rawText && rawText.length <= 25) {
                actionText = `Opening ${rawText}...`;
            } else if (rawText.toLowerCase().includes('bill') || href.includes('billing')) {
                actionText = 'Opening Billing...';
            } else if (rawText.toLowerCase().includes('complaint') || href.includes('complaints')) {
                actionText = 'Opening Complaints...';
            } else if (rawText.toLowerCase().includes('booking') || rawText.toLowerCase().includes('amenit') || href.includes('booking')) {
                actionText = 'Opening Facilities...';
            } else if (rawText.toLowerCase().includes('notice') || href.includes('notices')) {
                actionText = 'Opening Notices...';
            } else if (rawText.toLowerCase().includes('visitor') || href.includes('visitors')) {
                actionText = 'Opening Visitor Log...';
            } else if (rawText.toLowerCase().includes('approval') || href.includes('approvals')) {
                actionText = 'Opening Approvals...';
            } else if (rawText.toLowerCase().includes('pay') || href.includes('pay_bill')) {
                actionText = 'Opening Checkout...';
            }

            Loader.show(actionText, 'Loading page content');
        } catch (err) {
            // Ignore parse errors
        }
    }, true);

    // Auto-intercept form submissions
    document.addEventListener('submit', function (e) {
        const form = e.target;
        if (!form) return;

        // Skip if form targets a new window
        if (form.getAttribute('target') === '_blank') return;

        // Skip if form was already marked or prevented
        if (e.defaultPrevented) return;

        let submitText = 'Processing...';
        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitBtn) {
            const btnText = (submitBtn.innerText || submitBtn.value || '').trim();
            if (btnText.toLowerCase().includes('sign in') || btnText.toLowerCase().includes('login')) {
                submitText = 'Signing In...';
            } else if (btnText.toLowerCase().includes('register')) {
                submitText = 'Creating Account...';
            } else if (btnText.toLowerCase().includes('pay')) {
                submitText = 'Opening Secure Gateway...';
            } else if (btnText.toLowerCase().includes('save') || btnText.toLowerCase().includes('submit')) {
                submitText = 'Saving Details...';
            } else if (btnText.toLowerCase().includes('delete')) {
                submitText = 'Deleting Item...';
            } else if (btnText.length > 0 && btnText.length <= 20) {
                submitText = `${btnText}...`;
            }

            // Add loading spinner to submit button without breaking layout
            submitBtn.style.opacity = '0.7';
            submitBtn.style.pointerEvents = 'none';
        }

        Loader.show(submitText, 'Submitting your request');
    }, true);

})();
