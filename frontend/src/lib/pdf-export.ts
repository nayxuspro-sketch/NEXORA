/**
 * Helper robuste et universel pour le téléchargement des fichiers PDF.
 * Évite les boucles de redirection 301/308 entre Next.js et Django
 * en interrogeant directement le port backend 8008 en priorité.
 */
export async function downloadPdfFile(endpoint: string, defaultFilename: string): Promise<void> {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

  // En environnement navigateur, cibler directement le backend sur le port 8008
  const isBrowser = typeof window !== 'undefined';
  const hostname = isBrowser ? window.location.hostname : '127.0.0.1';

  const urls = [
    `http://${hostname}:8008${cleanEndpoint}`,
    `http://127.0.0.1:8008${cleanEndpoint}`,
    `http://localhost:8008${cleanEndpoint}`,
    cleanEndpoint
  ];

  let lastError: any = null;
  let response: Response | null = null;

  for (const url of urls) {
    try {
      const token = isBrowser
        ? (sessionStorage.getItem('nexora_session_token') || sessionStorage.getItem('nexora_access_token'))
        : null;

      const headers: Record<string, string> = {
        'Accept': 'application/pdf, */*'
      };
      if (token && token.startsWith('eyJ')) {
        headers['Authorization'] = `Bearer ${token}`;
      }

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
    throw new Error(
      lastError?.message ||
      `Impossible de générer le PDF (statut serveur: ${response?.status || 'hors-ligne'}). Vérifiez que le backend tourne sur le port 8008.`
    );
  }

  // Extraire le nom de fichier depuis l'en-tête Content-Disposition
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
