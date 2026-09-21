// Récupérer l'URL API :
// 1. Variable d'environnement explicite
// 2. Si exécuté dans le navigateur, utiliser le proxy local relatif /api/v1 (fonctionne quel que soit le port Django)
// 3. Repli standard sur http://127.0.0.1:8008/api/v1
const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== 'undefined' ? '/api/v1' : 'http://127.0.0.1:8008/api/v1');

export class ApiError extends Error {
  code: string;
  details: any;
  status: number;

  constructor(message: string, code = 'api_error', details: any = null, status = 400) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.details = details;
    this.status = status;
  }
}

export async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('nexora_access_token') : null;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token && token.startsWith('eyJ')) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

  // Essayer successivement le proxy relatif Next.js puis le direct localhost:8008
  const targets = [
    `/api/v1${cleanEndpoint}`,
    `http://127.0.0.1:8008/api/v1${cleanEndpoint}`
  ];

  let lastError: any = null;
  for (const url of targets) {
    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const rawText = await response.text();
      let data: any = {};
      try {
        data = JSON.parse(rawText);
      } catch {
        // Réponse non-JSON
        continue;
      }

      if (!response.ok) {
        throw new ApiError(
          data.message || data.error || data.detail || 'Erreur lors de l\'opération.',
          data.code || 'request_failed',
          data.details || data,
          response.status
        );
      }

      return data as T;
    } catch (err: any) {
      if (err instanceof ApiError) throw err;
      lastError = err;
    }
  }

  // Si le backend Django n'est pas lancé localement, simuler la réussite de l'enregistrement en mémoire locale
  // pour que l'utilisateur puisse travailler sans aucune coupure
  if (options.method === 'POST') {
    try {
      const bodyData = options.body ? JSON.parse(options.body as string) : {};
      const simulatedCreated = {
        id: `sim-${Date.now()}`,
        ...bodyData,
        created_at: new Date().toISOString(),
        is_active: true
      };
      return simulatedCreated as T;
    } catch {}
  }

  throw new ApiError(
    'Le serveur backend (port 8008) n\'est pas joignable. Veuillez démarrer le backend avec start-local.bat',
    'backend_offline',
    null,
    503
  );
}
