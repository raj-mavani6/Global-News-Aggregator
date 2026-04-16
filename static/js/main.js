/**
 * main.js - Frontend JavaScript for the News Scraper Project.
 * Handles scrape triggers, toast notifications, and UI interactions.
 */

// ═══════════════════════════════════════════
// Toast Notification System
// ═══════════════════════════════════════════
function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = {
        success: '✅',
        error: '❌',
        info: 'ℹ️',
    };

    toast.innerHTML = `<span>${icons[type] || icons.info}</span><span>${message}</span>`;
    container.appendChild(toast);

    // Auto-remove after duration
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(40px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}


// ═══════════════════════════════════════════
// Scrape Trigger
// ═══════════════════════════════════════════
function triggerScrape() {
    const btn = document.getElementById('btn-scrape') || document.getElementById('btn-scrape-dash');
    if (btn) {
        btn.innerHTML = '<span class="spinner"></span> Scraping...';
        btn.disabled = true;
    }

    showToast('Starting scrape of all news sites...', 'info');

    const formData = new FormData();
    formData.append('category', 'all');

    fetch('/scrape', {
        method: 'POST',
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        showToast(data.message || 'Scrape started in background!', 'success');
        if (btn) {
            btn.innerHTML = '<span class="btn-icon">🔄</span> Scrape Now';
            btn.disabled = false;
        }
    })
    .catch(error => {
        showToast('Failed to start scrape. Please try again.', 'error');
        console.error('Scrape error:', error);
        if (btn) {
            btn.innerHTML = '<span class="btn-icon">🔄</span> Scrape Now';
            btn.disabled = false;
        }
    });
}


// ═══════════════════════════════════════════
// Auto-submit filters on change
// ═══════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    // Auto-submit form when filter dropdowns change
    const filterSelects = document.querySelectorAll('.filter-select');
    filterSelects.forEach(select => {
        select.addEventListener('change', () => {
            const form = document.getElementById('search-form');
            if (form) form.submit();
        });
    });

    // Add entrance animation to elements
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });

    // Observe cards for stagger animation
    document.querySelectorAll('.news-card, .stat-card, .chart-card').forEach(el => {
        observer.observe(el);
    });

    // Keyboard shortcut: focus search on '/'
    document.addEventListener('keydown', (e) => {
        if (e.key === '/' && document.activeElement.tagName !== 'INPUT') {
            e.preventDefault();
            const searchInput = document.getElementById('search-input');
            if (searchInput) searchInput.focus();
        }
    });
});


// ═══════════════════════════════════════════
// Navbar Scroll Effect
// ═══════════════════════════════════════════
let lastScrollY = 0;
window.addEventListener('scroll', () => {
    const navbar = document.getElementById('navbar');
    if (!navbar) return;

    if (window.scrollY > 50) {
        navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.4)';
    } else {
        navbar.style.boxShadow = 'none';
    }

    lastScrollY = window.scrollY;
});
