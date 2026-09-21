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

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new ApiError(
      data.message || data.error || 'Une erreur est survenue sur le serveur.',
      data.code || 'request_failed',
      data.details || data,
      response.status
    );
  }

  return data as T;
}
