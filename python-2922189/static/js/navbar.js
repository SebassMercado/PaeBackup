// ===== Sidebar Toggle =====
const body = document.querySelector('body'),
      sidebar = body.querySelector('.sidebar'),
      toggle = body.querySelector('.toggle'),
      modeSwitch = body.querySelector('.toggle-switch'),
      modeText = body.querySelector('.mode-text');

// ===== Restaurar estado de la sidebar INMEDIATAMENTE =====
// Esto se ejecuta antes del DOMContentLoaded para evitar parpadeos
if (sidebar) {
    const savedSidebarState = localStorage.getItem('sidebarState');
    if (savedSidebarState === 'closed') {
        sidebar.classList.add('close');
    } else if (savedSidebarState === 'open') {
        sidebar.classList.remove('close');
    }
}

// ===== Toggle Sidebar =====
if (toggle) {
    toggle.addEventListener('click', () => {
        sidebar.classList.toggle('close');
        // Guardar el estado de la sidebar en localStorage
        if (sidebar.classList.contains('close')) {
            localStorage.setItem('sidebarState', 'closed');
        } else {
            localStorage.setItem('sidebarState', 'open');
        }
    });
}

// ===== Dark/Light Mode Toggle =====
if (modeSwitch) {
    modeSwitch.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        document.body.classList.toggle('dark-mode');
        
        if (document.body.classList.contains('dark-mode')) {
            if (modeText) modeText.innerText = 'Claro';
            localStorage.setItem('theme', 'dark');
        } else {
            if (modeText) modeText.innerText = 'Oscuro';
            localStorage.setItem('theme', 'light');
        }
    });
}

// ===== Aplicar tema y configuración inicial =====
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme');
    const savedSidebarState = localStorage.getItem('sidebarState');
    
    // Aplicar tema
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        if (modeText) modeText.innerText = 'Claro';
    } else {
        document.body.classList.remove('dark-mode');
        if (modeText) modeText.innerText = 'Oscuro';
    }
    
    // Si no hay estado guardado, establecer uno por defecto
    if (!savedSidebarState && sidebar) {
        if (window.innerWidth <= 768) {
            sidebar.classList.add('close');
            localStorage.setItem('sidebarState', 'closed');
        } else {
            localStorage.setItem('sidebarState', 'open');
        }
    }
    // Quitar clase inicial forzada para permitir expansión normal tras la carga
    try { document.documentElement.classList.remove('sidebar-closed-init'); } catch(e) {}
});

// ===== Active Link Highlighting =====
document.addEventListener('DOMContentLoaded', () => {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link a');
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        
        if (link.getAttribute('href') === currentPath ||
            (currentPath.includes(link.getAttribute('href')) && 
             link.getAttribute('href') !== '/')) {
            link.classList.add('active');
        }
    });
});