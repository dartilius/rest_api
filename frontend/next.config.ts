const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    domains: ['api1.krasrm.com', 'cdn.example.com'],
    formats: ['image/avif', 'image/webp'],
  },
  output: 'standalone',
  async redirects() {
    return [
      {
        source: '/',
        destination: '/nomenclatures',
        permanent: true,
      },
    ];
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://api1.krasrm.com/:path*',
      },
    ];
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          }
        ],
      },
    ];
  }
};

export default nextConfig;
