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
    const toggle = document.getElementById('mobileToggle');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');

    function toggleSidebar(e) {
        if (e) e.stopPropagation();
        if (sidebar) {
            if (window.innerWidth > 991) {
                sidebar.classList.toggle('collapsed');
            } else {
                sidebar.classList.toggle('mobile-open');
                // Ensure desktop 'collapsed' is removed on mobile if we want it open
                sidebar.classList.remove('collapsed');
            }
        }
    }

    if (toggle) {
        toggle.addEventListener('click', toggleSidebar);
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }

    // Close when clicking outside sidebar on mobile
    document.addEventListener('click', function (e) {
        if (sidebar && sidebar.classList.contains('mobile-open')) {
            const isClickInsideSidebar = sidebar.contains(e.target);
            const isClickOnToggle = (toggle && toggle.contains(e.target)) ||
                (sidebarToggle && sidebarToggle.contains(e.target));

            if (!isClickInsideSidebar && !isClickOnToggle) {
                sidebar.classList.remove('mobile-open');
            }
        }
    });

    // Prevent sidebar from closing when clicking inside it on mobile
    if (sidebar) {
        sidebar.addEventListener('click', function (e) {
            if (window.innerWidth <= 991) {
                e.stopPropagation();
            }
        });
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
