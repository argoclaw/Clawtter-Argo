/**
 * Theme mode controller: light / dark / system
 */
(function () {
    'use strict';

    const STORAGE_KEY = 'theme-preference';
    const MODES = ['light', 'dark', 'system'];

    const mq = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;

    function getStoredMode() {
        const saved = localStorage.getItem(STORAGE_KEY);
        return MODES.includes(saved) ? saved : 'system';
    }

    function resolveTheme(mode) {
        if (mode === 'system') {
            return (mq && mq.matches) ? 'dark' : 'light';
        }
        return mode;
    }

    function applyMode(mode, persist = true) {
        const effective = resolveTheme(mode);
        document.documentElement.setAttribute('data-theme-mode', mode);
        document.documentElement.setAttribute('data-theme', effective);

        if (persist) {
            localStorage.setItem(STORAGE_KEY, mode);
        }

        document.querySelectorAll('.theme-toggle[data-theme-mode]').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-theme-mode') === mode);
        });
    }

    function init() {
        const mode = getStoredMode();
        applyMode(mode, false);

        document.querySelectorAll('.theme-toggle[data-theme-mode]').forEach(btn => {
            btn.addEventListener('click', () => {
                const nextMode = btn.getAttribute('data-theme-mode');
                if (!MODES.includes(nextMode)) return;
                applyMode(nextMode, true);
            });
        });

        if (mq && mq.addEventListener) {
            mq.addEventListener('change', () => {
                if (getStoredMode() === 'system') {
                    applyMode('system', false);
                }
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
