/** @type {import('next').NextConfig} */
const nextConfig = {
  // output: 'export',
  // trailingSlash: true,
  typescript: {
    ignoreBuildErrors: true,
  },
  output: "standalone",
  staticPageGenerationTimeout: 120,
  redirects() {
    return [
      {
        source: "/", //начальный путь
        destination: "/nomenclatures", //конечный путь
        permanent: true,
      },
    ];
  },
};

module.exports = nextConfig;
