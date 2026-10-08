/**
 * Helper robuste et universel pour la génération, visualisation et téléchargement des PDF.
 * Fonctionne avec fiabilité absolue dans tous les navigateurs et environnements :
 * - Route serveur Next.js dédiée (/api/pdf-proxy/?endpoint=...)
 * - Proxy relatif Next.js (/api/v1/...)
 * - Téléchargement binaire sécurisé en mémoire Blob sans blocage iframe/popup
 */

export function openPdfViewerModal(blobUrl: string, title: string = 'Visualisation du Document PDF', filename: string = 'document.pdf') {
  if (typeof window === 'undefined') return;

  // Supprimer tout modal existant
  const existing = document.getElementById('nexora-pdf-viewer-overlay');
  if (existing && document.body.contains(existing)) {
    document.body.removeChild(existing);
  }

  const overlay = document.createElement('div');
  overlay.id = 'nexora-pdf-viewer-overlay';
  overlay.style.position = 'fixed';
  overlay.style.top = '0';
  overlay.style.left = '0';
  overlay.style.width = '100vw';
  overlay.style.height = '100vh';
  overlay.style.backgroundColor = 'rgba(15, 23, 42, 0.88)';
  overlay.style.backdropFilter = 'blur(6px)';
  overlay.style.zIndex = '99999';
  overlay.style.display = 'flex';
  overlay.style.flexDirection = 'column';
  overlay.style.alignItems = 'center';
  overlay.style.justifyContent = 'center';
  overlay.style.padding = '12px';

  overlay.innerHTML = `
    <div style="background: #1e293b; border: 1px solid #334155; border-radius: 16px; width: 95%; max-width: 1050px; height: 92vh; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);">
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 14px 20px; border-bottom: 1px solid #334155; background: #0f172a; flex-wrap: wrap; gap: 8px;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #38bdf8;"></span>
          <h3 style="margin: 0; color: #f8fafc; font-size: 15px; font-weight: 700;">${title}</h3>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <a id="nexora-direct-download-btn" href="${blobUrl}" download="${filename}" style="background: #0284c7; color: #fff; text-decoration: none; font-size: 12px; font-weight: 700; padding: 7px 14px; border-radius: 8px; display: inline-flex; align-items: center; gap: 6px; cursor: pointer;">
            📥 Enregistrer PDF
          </a>
          <a href="${blobUrl}" target="_blank" rel="noopener noreferrer" style="background: rgba(255,255,255,0.08); color: #cbd5e1; text-decoration: none; font-size: 12px; font-weight: 600; padding: 7px 14px; border-radius: 8px;">
            ↗ Nouvel Onglet
          </a>
          <button id="nexora-close-pdf-btn" style="background: rgba(255,255,255,0.1); border: none; color: #f8fafc; font-size: 16px; font-weight: bold; cursor: pointer; padding: 4px 10px; border-radius: 6px;">✕ Fermer</button>
        </div>
      </div>
      <div style="flex: 1; background: #0b132b; position: relative;">
        <iframe src="${blobUrl}#toolbar=1&navpanes=0" style="width: 100%; height: 100%; border: none;" title="${title}"></iframe>
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

/**
 * Télécharge et affiche immédiatement un PDF en utilisant l'API Fetch avec repli multi-adresses et Blob mémoire.
 */
export async function downloadPdfFile(endpoint: string, defaultFilename: string): Promise<void> {
  const isBrowser = typeof window !== 'undefined';
  if (!isBrowser) return;

  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const cacheBuster = `_t=${Date.now()}`;
  const fullEndpoint = cleanEndpoint.includes('?') ? `${cleanEndpoint}&${cacheBuster}` : `${cleanEndpoint}?${cacheBuster}`;

  // Récupérer le token d'authentification si disponible
  const token = sessionStorage.getItem('nexora_session_token') ||
    sessionStorage.getItem('nexora_access_token') ||
    localStorage.getItem('nexora_access_token');

  const headers: Record<string, string> = {
    'Accept': 'application/pdf, application/octet-stream, */*',
  };

  if (token && token.startsWith('eyJ')) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const apiPath = fullEndpoint.startsWith('/api/v1') ? fullEndpoint : `/api/v1${fullEndpoint}`;

  // Pipeline ordonné de requêtes :
  // 1. Route de proxy serveur dédiée Next.js (sécurisée côté serveur Node.js vers 127.0.0.1:8008)
  // 2. Rewrite direct /api/v1/...
  const proxyUrl = `/api/pdf-proxy/?endpoint=${encodeURIComponent(apiPath)}`;
  const candidateUrls = [
    proxyUrl,
    apiPath,
  ];

  let blob: Blob | null = null;
  let lastError: any = null;

  for (const url of candidateUrls) {
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        let errDetails = `Erreur serveur HTTP ${response.status}`;
        try {
          const errBody = await response.text();
          if (errBody && errBody.length < 300) {
            errDetails += `: ${errBody}`;
          }
        } catch {}
        lastError = new Error(errDetails);
        continue;
      }

      const contentType = response.headers.get('content-type') || '';
      if (!contentType.includes('pdf') && !contentType.includes('octet-stream')) {
        const text = await response.text();
        if (text.startsWith('%PDF')) {
          blob = new Blob([text], { type: 'application/pdf' });
          break;
        }
        continue;
      }

      blob = await response.blob();
      if (blob && blob.size > 0) {
        break;
      }
    } catch (err: any) {
      lastError = err;
    }
  }

  if (!blob || blob.size === 0) {
    throw new Error(lastError?.message || 'Impossible de joindre le serveur pour générer le document PDF.');
  }

  // Créer un Blob URL dédié de type application/pdf
  const pdfBlob = new Blob([blob], { type: 'application/pdf' });
  const blobUrl = URL.createObjectURL(pdfBlob);

  // 1. Déclencher le téléchargement immédiat du fichier
  const a = document.createElement('a');
  a.href = blobUrl;
  a.download = defaultFilename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    if (document.body.contains(a)) {
      document.body.removeChild(a);
    }
  }, 1000);

  // 2. Afficher la visionneuse interactive plein écran avec iframe locale (blob URL 100% compatible)
  const displayTitle = defaultFilename.replace('.pdf', '').replace(/_/g, ' ');
  openPdfViewerModal(blobUrl, displayTitle, defaultFilename);
}
