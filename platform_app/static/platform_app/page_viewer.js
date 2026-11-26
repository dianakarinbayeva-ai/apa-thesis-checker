const image = document.getElementById('page-image');
const statusLabel = document.getElementById('viewer-status');
const retry = document.getElementById('viewer-retry');
let objectUrl;
if (image) {
  fetch(image.dataset.imageUrl, {cache: 'no-store', credentials: 'same-origin'})
    .then(async response => {
      if (!response.ok || !response.headers.get('Content-Type')?.startsWith('image/png')) throw new Error('page');
      const focus = response.headers.get('X-Focus-Top');
      const count = Number(response.headers.get('X-Highlight-Count'));
      objectUrl = URL.createObjectURL(await response.blob());
      image.addEventListener('load', () => {
        statusLabel.textContent = count ? '' : image.dataset.noMarks;
        if (focus !== null && Number.isFinite(Number(focus))) {
          window.scrollTo({top: Math.max(0, image.offsetTop + Number(focus) * image.clientHeight - 100), behavior: 'auto'});
        }
      }, {once:true});
      image.src = objectUrl;
    }).catch(() => {
      statusLabel.textContent = image.dataset.error;
      retry.hidden = false;
    });
  window.addEventListener('pagehide', () => { if (objectUrl) URL.revokeObjectURL(objectUrl); });
}
document.getElementById('zoom')?.addEventListener('change', event => {
  document.querySelector('.page-sheet').style.width = `${Number(event.target.value)}%`;
});
