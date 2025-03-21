const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    domains: ['api1.krasrm.com'],
  },
  output: 'standalone',
  redirects() {
    return [
      {
        source: '/', //начальный путь
        destination: '/nomenclatures', //конечный путь
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
