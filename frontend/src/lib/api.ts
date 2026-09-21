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

  // N'ajouter l'en-tête Authorization que si le token est un vrai JWT (commençant par eyJ...)
  if (token && token.startsWith('eyJ')) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Tenter l'appel : d'abord via le proxy relatif /api/v1, sinon directement sur 127.0.0.1:8008
  const primaryUrl = endpoint.startsWith('http') ? endpoint : `/api/v1${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  
  let response: Response;
  try {
    response = await fetch(primaryUrl, {
      ...options,
      headers,
    });
  } catch {
    // Si échec du proxy (ex: Next.js dev server non redémarré), repli direct sur le port 8008
    const fallbackUrl = `http://127.0.0.1:8008/api/v1${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    response = await fetch(fallbackUrl, {
      ...options,
      headers,
    });
  }

  const rawText = await response.text();
  let data: any = {};
  try {
    data = JSON.parse(rawText);
  } catch {
    // Si la réponse n'est pas du JSON valide (erreur proxy HTML 502/504)
    if (!response.ok) {
      throw new ApiError(
        'Le serveur backend (port 8008) n\'a pas renvoyé de données valides. Vérifiez que Django tourne.',
        'server_unreachable',
        null,
        response.status
      );
    }
  }

  if (!response.ok) {
    throw new ApiError(
      data.message || data.error || data.detail || 'Une erreur est survenue lors de l\'enregistrement.',
      data.code || 'request_failed',
      data.details || data,
      response.status
    );
  }

  return data as T;
}
