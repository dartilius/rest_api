const nextConfig = {
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

export default nextConfig;
