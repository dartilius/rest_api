/** @type {import('next').NextConfig} */
const nextConfig = {
   output: 'standalone',
  trailingSlash: true,
  // typescript: {
  //   ignoreBuildErrors: true,
  // },
  redirects() {
    return [
      {
        source: '/', //начальный путь
        destination: '/nomenclatures', //конечный путь
        permanent: true,
      }
    ]
  },
}

module.exports = nextConfig
