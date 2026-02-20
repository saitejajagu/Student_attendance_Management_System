// =====================================================
// AttendMS — Global JavaScript
// =====================================================

// Update current date in topbar
(function () {
    const el = document.getElementById('currentDate');
    if (el) {
        const now = new Date();
        el.textContent = now.toLocaleDateString('en-IN', {
            weekday: 'short', year: 'numeric', month: 'short', day: 'numeric'
        });
    }
})();

// ---- MODALS ----
function openModal(id) {
    const el = document.getElementById(id);
    if (el) {
        el.classList.add('open');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(id) {
    const el = document.getElementById(id);
    if (el) {
        el.classList.remove('open');
        document.body.style.overflow = '';
    }
}

// Close modal on overlay click
document.addEventListener('click', function (e) {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('open');
        document.body.style.overflow = '';
    }
});

// Close modal on Escape
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.open').forEach(el => {
            el.classList.remove('open');
            document.body.style.overflow = '';
        });
    }
});

// ---- DELETE CONFIRM MODAL ----
function confirmDelete(url, name) {
    const form = document.getElementById('deleteForm');
    const nameEl = document.getElementById('deleteItemName');
    if (form) form.action = url;
    if (nameEl) nameEl.textContent = name;
    openModal('deleteModal');
}

// ---- SIDEBAR SLIDE TOGGLE ----
(function () {
    var toggle = document.getElementById('mobileToggle');
    var sidebar = document.getElementById('sidebar');
    var main = document.getElementById('mainContent');
    if (toggle && sidebar) {
        toggle.addEventListener('click', function () {
            sidebar.classList.toggle('mobile-open');
        });
        // Close when clicking outside sidebar on mobile
        if (main) {
            main.addEventListener('click', function () {
                sidebar.classList.remove('mobile-open');
            });
        }
    }
})();

// ---- AUTO-DISMISS FLASH MESSAGES ----
(function () {
    setTimeout(function () {
        document.querySelectorAll('.alert').forEach(function (el) {
            el.style.transition = 'opacity 0.5s ease';
            el.style.opacity = '0';
            setTimeout(() => el.remove(), 500);
        });
    }, 4000);
})();
