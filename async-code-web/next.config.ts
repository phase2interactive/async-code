import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://backend:5000/:path*', // Using Docker service name
      },
    ];
  },
};

export default nextConfig;
