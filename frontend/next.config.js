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
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
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
