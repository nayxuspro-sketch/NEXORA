import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const targetPath = searchParams.get('endpoint');

  if (!targetPath) {
    return NextResponse.json({ error: 'Endpoint manquant' }, { status: 400 });
  }

  // Cloner tous les paramètres sauf 'endpoint' pour les transférer au backend
  const forwardParams = new URLSearchParams();
  searchParams.forEach((value, key) => {
    if (key !== 'endpoint') {
      forwardParams.append(key, value);
    }
  });

  const queryString = forwardParams.toString();
  const cleanPath = targetPath.startsWith('/') ? targetPath : `/${targetPath}`;
  const targetUrl = `http://127.0.0.1:8008${cleanPath}${queryString ? (cleanPath.includes('?') ? `&${queryString}` : `?${queryString}`) : ''}`;

  const headers: Record<string, string> = {
    'Accept': 'application/pdf, application/octet-stream, */*',
  };

  const authHeader = request.headers.get('authorization');
  if (authHeader) {
    headers['Authorization'] = authHeader;
  }

  try {
    const backendRes = await fetch(targetUrl, {
      method: 'GET',
      headers,
      cache: 'no-store',
    });

    if (!backendRes.ok) {
      const errText = await backendRes.text();
      return new NextResponse(errText, {
        status: backendRes.status,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const blob = await backendRes.blob();
    const contentDisposition = backendRes.headers.get('content-disposition') || 'inline; filename="document.pdf"';

    return new NextResponse(blob, {
      status: 200,
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': contentDisposition,
        'Cache-Control': 'no-cache, no-store, must-revalidate',
      },
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: 'Erreur proxy backend PDF', details: err?.message || String(err) },
      { status: 502 }
    );
  }
}
