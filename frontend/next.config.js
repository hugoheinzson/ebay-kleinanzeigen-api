/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'img.kleinanzeigen.de',
      },
    ],
  },
  async rewrites() {
    // Mehrere mögliche Variablennamen unterstützen.
    // Wichtig: Diese werden zur Build-Zeit aufgelöst – deshalb BACKEND_URL auch als build arg setzen.
    const backendUrl =
      process.env.BACKEND_URL ||
      process.env.API_BASE_URL ||
      process.env.NEXT_PUBLIC_API_BASE_URL ||
      'http://backend:8000'
    const normalizedBackendUrl = backendUrl.endsWith('/')
      ? backendUrl.slice(0, -1)
      : backendUrl

    return [
      {
        source: '/api/backend/:path*',
        destination: `${normalizedBackendUrl}/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
