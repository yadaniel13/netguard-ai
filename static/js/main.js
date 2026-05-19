/* NetGuard AI — Main JavaScript */

// Sidebar mobile toggle
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.getElementById('sidebar');
if (sidebarToggle && sidebar) {
  sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  document.addEventListener('click', e => {
    if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
      sidebar.classList.remove('open');
    }
  });
}

// Auto-dismiss alerts after 5 s
document.querySelectorAll('.alert-dismissible').forEach(el => {
  setTimeout(() => {
    const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
    if (bsAlert) bsAlert.close();
  }, 5000);
});

// Highlight active nav link based on current path
document.querySelectorAll('.ng-nav-link').forEach(link => {
  if (link.getAttribute('href') === window.location.pathname) {
    link.classList.add('active');
  }
});

// Animate stat values (count-up)
function animateCount(el) {
  const target = parseInt(el.textContent.replace(/[^0-9]/g, ''), 10);
  if (isNaN(target) || target === 0) return;
  let current = 0;
  const step = Math.ceil(target / 60);
  const timer = setInterval(() => {
    current = Math.min(current + step, target);
    el.textContent = current.toLocaleString('ru-RU');
    if (current >= target) clearInterval(timer);
  }, 16);
}

document.querySelectorAll('.ng-stat-value').forEach(animateCount);
