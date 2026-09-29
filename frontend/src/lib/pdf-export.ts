/**
 * Helper robuste et universel pour le téléchargement des fichiers PDF.
 * Fonctionne aussi bien dans l'iframe d'aperçu Arena.ai que sur serveur dédié ou localhost.
 */
export function openPdfViewerModal(pdfUrl: string, title: string = 'Visualisation du Document PDF') {
  if (typeof window === 'undefined') return;

  // Supprimer tout modal existant
  const existing = document.getElementById('nexora-pdf-viewer-overlay');
  if (existing) {
    document.body.removeChild(existing);
  }

  const overlay = document.createElement('div');
  overlay.id = 'nexora-pdf-viewer-overlay';
  overlay.style.position = 'fixed';
  overlay.style.top = '0';
  overlay.style.left = '0';
  overlay.style.width = '100vw';
  overlay.style.height = '100vh';
  overlay.style.backgroundColor = 'rgba(15, 23, 42, 0.85)';
  overlay.style.backdropFilter = 'blur(6px)';
  overlay.style.zIndex = '99999';
  overlay.style.display = 'flex';
  overlay.style.flexDirection = 'column';
  overlay.style.alignItems = 'center';
  overlay.style.justifyContent = 'center';
  overlay.style.padding = '16px';

  overlay.innerHTML = `
    <div style="background: #1e293b; border: 1px solid #334155; border-radius: 16px; width: 95%; max-width: 1050px; height: 90vh; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);">
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 14px 20px; border-bottom: 1px solid #334155; background: #0f172a;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #38bdf8;"></span>
          <h3 style="margin: 0; color: #f8fafc; font-size: 15px; font-weight: 700;">${title}</h3>
        </div>
        <div style="display: flex; align-items: center; gap: 10px;">
          <a href="${pdfUrl}" download target="_blank" style="background: #0284c7; color: #fff; text-decoration: none; font-size: 12px; font-weight: 700; padding: 7px 14px; border-radius: 8px; display: inline-flex; align-items: center; gap: 6px;">
            📥 Télécharger PDF
          </a>
          <a href="${pdfUrl}" target="_blank" rel="noopener noreferrer" style="background: rgba(255,255,255,0.08); color: #cbd5e1; text-decoration: none; font-size: 12px; font-weight: 600; padding: 7px 14px; border-radius: 8px;">
            ↗ Plein Écran
          </a>
          <button id="nexora-close-pdf-btn" style="background: transparent; border: none; color: #94a3b8; font-size: 20px; cursor: pointer; padding: 4px 8px; line-height: 1; border-radius: 6px;">✕</button>
        </div>
      </div>
      <div style="flex: 1; background: #0b132b; position: relative;">
        <iframe src="${pdfUrl}#toolbar=1&navpanes=0" style="width: 100%; height: 100%; border: none;" title="${title}"></iframe>
      </div>
    </div>
  `;

  document.body.appendChild(overlay);

  const closeBtn = document.getElementById('nexora-close-pdf-btn');
  if (closeBtn) {
    closeBtn.onclick = () => {
      if (document.body.contains(overlay)) {
        document.body.removeChild(overlay);
      }
    };
  }

  overlay.onclick = (e) => {
    if (e.target === overlay) {
      if (document.body.contains(overlay)) {
        document.body.removeChild(overlay);
      }
    }
  };
}

export async function downloadPdfFile(endpoint: string, defaultFilename: string): Promise<void> {
  const isBrowser = typeof window !== 'undefined';
  let cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  
  const cacheBuster = `_t=${Date.now()}`;
  cleanEndpoint = cleanEndpoint.includes('?') ? `${cleanEndpoint}&${cacheBuster}` : `${cleanEndpoint}?${cacheBuster}`;

  if (isBrowser) {
    // 1. Ouvrir immédiatement la visionneuse PDF intégrée à l'écran
    openPdfViewerModal(cleanEndpoint, defaultFilename.replace('.pdf', '').replace(/_/g, ' '));

    // 2. Déclencher également le téléchargement standard du fichier
    const a = document.createElement('a');
    a.href = cleanEndpoint;
    a.setAttribute('download', defaultFilename);
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      if (document.body.contains(a)) {
        document.body.removeChild(a);
      }
    }, 1000);
  }
}

