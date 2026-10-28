document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {
  document.querySelectorAll('[data-filter]').forEach(b => b.classList.toggle('active', b === button));
  document.querySelectorAll('[data-finding-status]').forEach(f => { f.hidden = button.dataset.filter !== 'all' && f.dataset.findingStatus !== button.dataset.filter; });
}));
document.querySelectorAll('[data-confirm]').forEach(form => form.addEventListener('submit', event => {
  if (!window.confirm(form.dataset.confirm)) event.preventDefault();
}));
const progress = document.querySelector('[data-status-url]');
if (progress) {
  const check = async () => {
    try { const response = await fetch(progress.dataset.statusUrl, {cache: 'no-store'});
      if (response.ok) { const result = await response.json(); if (['done', 'failed'].includes(result.status)) { location.reload(); return; } }
    } catch (_) {}
    setTimeout(check, 2500);
  }; setTimeout(check, 1500);
}
