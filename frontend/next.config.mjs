/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  async redirects() {
    return [
      {
        source: "/",
        destination: "/nomenclatures",
        permanent: true,
      },
    ];
  },
  // poweredByHeader: false,
  // env: {
  //   APP_URL: process.env.REACT_APP_URL,
	// 	APP_ENV: process.env.REACT_APP_ENV,
	// 	APP_SERVER_URL: process.env.REACT_APP_SERVER_URL,
  // },
  // async rewrites() {
	// 	return [
	// 		{
	// 			source: '/api/:path*',
	// 			destination: 'http://192.168.0.180:8000/api/:path*',
	// 		},
	// 	]
	// },
};

export default nextConfig;
