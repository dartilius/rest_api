/** @type {import('next').NextConfig} */
const nextConfig = {
  // output: 'export',
  // trailingSlash: true,
  typescript: {
    ignoreBuildErrors: true,
  },
  output: "standalone",
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
