/** @type {import('next').NextConfig} */
const backendPort = process.env.BACKEND_PORT || '8008';
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*/',
        destination: `http://127.0.0.1:${backendPort}/api/:path*/`,
      },
      {
        source: '/api/:path*',
        destination: `http://127.0.0.1:${backendPort}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
