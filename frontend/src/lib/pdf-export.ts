/**
 * Helper robuste et universel pour le téléchargement des fichiers PDF.
 * Fonctionne aussi bien dans l'iframe d'aperçu Arena.ai que sur serveur dédié ou localhost.
 */
export async function downloadPdfFile(endpoint: string, defaultFilename: string): Promise<void> {
  const isBrowser = typeof window !== 'undefined';
  let cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  
  // Toujours utiliser l'URL relative sur le même port que le navigateur pour éviter CORS / port blocking
  const cacheBuster = `_t=${Date.now()}`;
  cleanEndpoint = cleanEndpoint.includes('?') ? `${cleanEndpoint}&${cacheBuster}` : `${cleanEndpoint}?${cacheBuster}`;

  if (isBrowser) {
    // Méthode universelle la plus fiable et native : navigation de téléchargement
    // Ne dépend pas de fetch, ne subit pas les restrictions CORS ou bloquages de popup
    const a = document.createElement('a');
    a.href = cleanEndpoint;
    a.setAttribute('download', defaultFilename);
    a.setAttribute('target', '_blank');
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
    }, 1000);
    return;
  }
}

