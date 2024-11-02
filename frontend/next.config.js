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
  webpack(config) {
    config.module.rules.push({
      test: /\.svg$/,
      issuer: /\.[jt]sx?$/,
      use: [
        {
          loader: '@svgr/webpack',
          options: { icon: true },
        },
      ],
    });
    return config;
  },
};

module.exports = nextConfig;
