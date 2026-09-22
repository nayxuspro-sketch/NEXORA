/**
 * Helper robuste et universel pour le téléchargement des fichiers PDF.
 * Fonctionne aussi bien dans l'iframe d'aperçu Arena.ai que sur serveur dédié ou localhost.
 */
export async function downloadPdfFile(endpoint: string, defaultFilename: string): Promise<void> {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

  // Récupérer le token d'authentification disponible
  const isBrowser = typeof window !== 'undefined';
  const token = isBrowser
    ? (sessionStorage.getItem('nexora_session_token') || sessionStorage.getItem('nexora_access_token') || localStorage.getItem('nexora_access_token'))
    : null;

  const headers: Record<string, string> = {
    'Accept': 'application/pdf, */*'
  };
  if (token && token.startsWith('eyJ')) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // 1. Liste ordonnée des URLs candidates :
  // - L'URL relative (qui passe par le proxy configuré de Next.js)
  // - Si localhost/127.0.0.1, le port direct 8008
  const urls: string[] = [cleanEndpoint];

  if (isBrowser) {
    const host = window.location.hostname;
    if (host === 'localhost' || host === '127.0.0.1' || host === '0.0.0.0') {
      urls.unshift(`http://127.0.0.1:8008${cleanEndpoint}`);
      urls.unshift(`http://localhost:8008${cleanEndpoint}`);
    }
  }

  let lastError: any = null;
  let response: Response | null = null;

  for (const url of urls) {
    try {
      response = await fetch(url, {
        method: 'GET',
        headers
      });

      if (response && response.ok) {
        break;
      }
    } catch (err) {
      lastError = err;
    }
  }

  if (!response || !response.ok) {
    // Si fetch direct a échoué (restrictions sandbox), déclencher un lien direct navigateur
    if (isBrowser) {
      try {
        const directLink = document.createElement('a');
        directLink.href = cleanEndpoint;
        directLink.target = '_blank';
        directLink.download = defaultFilename;
        document.body.appendChild(directLink);
        directLink.click();
        document.body.removeChild(directLink);
        return;
      } catch (fallbackErr) {
        // Fallback silently
      }
    }

    throw new Error(
      lastError?.message ||
      `Impossible d'exporter le document PDF (statut serveur: ${response?.status || 'hors-ligne'}). Vérifiez que les services NEXORA sont bien lancés.`
    );
  }

  // Extraire le nom de fichier officiel depuis Content-Disposition
  let filename = defaultFilename;
  const disposition = response.headers.get('Content-Disposition');
  if (disposition && disposition.includes('filename=')) {
    const match = disposition.match(/filename=["']?([^"';]+)["']?/);
    if (match && match[1]) {
      filename = match[1].trim();
    }
  }

  const blob = await response.blob();
  const blobUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = blobUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  window.URL.revokeObjectURL(blobUrl);
  document.body.removeChild(link);
}
