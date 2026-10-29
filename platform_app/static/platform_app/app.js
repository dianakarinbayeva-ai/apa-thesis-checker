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

document.querySelectorAll('[data-password-target]').forEach(button => {
  button.addEventListener('click', () => {
    const input = document.getElementById(button.dataset.passwordTarget);
    const reveal = input.type === 'password';
    input.type = reveal ? 'text' : 'password';
    button.setAttribute('aria-pressed', String(reveal));
    button.setAttribute('aria-label', reveal ? button.dataset.hideLabel : button.dataset.showLabel);
  });
});

const fileInput = document.getElementById('file');
const dropZone = document.querySelector('[data-drop-zone]');
const selectedName = document.querySelector('[data-file-name]');
if (fileInput && dropZone && selectedName) {
  const showFile = () => {
    const file = fileInput.files[0];
    selectedName.textContent = file ? `${file.name} · ${(file.size / 1024 / 1024).toFixed(1)} MB` : selectedName.dataset.empty;
  };
  fileInput.addEventListener('change', showFile);
  ['dragenter', 'dragover'].forEach(name => dropZone.addEventListener(name, event => {
    event.preventDefault(); dropZone.classList.add('is-dragging');
  }));
  ['dragleave', 'drop'].forEach(name => dropZone.addEventListener(name, event => {
    event.preventDefault(); dropZone.classList.remove('is-dragging');
  }));
  dropZone.addEventListener('drop', event => {
    const dropped = event.dataTransfer.files[0];
    if (!dropped) return;
    const transfer = new DataTransfer();
    transfer.items.add(dropped);
    fileInput.files = transfer.files;
    showFile();
  });
}

const documentPreview = document.getElementById('document-preview');
if (documentPreview) {
  document.querySelectorAll('[data-pdf-page]').forEach(link => link.addEventListener('click', event => {
    event.preventDefault();
    documentPreview.src = `${documentPreview.dataset.pdfUrl}#page=${link.dataset.pdfPage}&toolbar=0`;
    documentPreview.scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start'});
  }));
}
