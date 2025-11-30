/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  distDir: 'out',
  images: {
    unoptimized: true
  },
  trailingSlash: true,
  // Configuración para servir desde FastAPI
  basePath: '',
  assetPrefix: '',
}

module.exports = nextConfig

