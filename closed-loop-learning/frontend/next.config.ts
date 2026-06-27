import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  basePath: "/closed-loop-admin",
  allowedDevOrigins: ["localhost", "127.0.0.1", "*.workstations.google.com", "*.cloudtop.corp.google.com", "*.google.com"],
  async redirects() {
    return [
      {
        source: "/",
        destination: "/closed-loop-admin",
        basePath: false,
        permanent: false,
      },
    ];
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/:path*",
      },
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/:path*",
        basePath: false,
      },
    ];
  },
};

export default nextConfig;
