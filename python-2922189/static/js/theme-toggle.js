(function(){
  function applyTheme(mode){
    var root = document.documentElement;
    if(mode === 'dark'){ root.setAttribute('data-theme','dark'); document.body.classList.add('dark-mode'); }
    else { root.setAttribute('data-theme','light'); document.body.classList.remove('dark-mode'); }
    var btn = document.getElementById('themeToggle');
    if(btn){ btn.dataset.mode = mode; btn.querySelector('.icon').textContent = mode === 'dark' ? '🌙' : '☀️'; }
  }

  function toggleTheme(){
    var current = localStorage.getItem('theme') || 'light';
    var next = current === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', next);
    applyTheme(next);
  }

  document.addEventListener('DOMContentLoaded', function(){
    // Pre-aplicar antes del repintado (flash reducción)
    var saved = localStorage.getItem('theme');
    if(!saved){
      // Preferencia del sistema
      saved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      localStorage.setItem('theme', saved);
    }
    applyTheme(saved);

    var btn = document.getElementById('themeToggle');
    if(btn){ btn.addEventListener('click', toggleTheme); }
  });
})();
