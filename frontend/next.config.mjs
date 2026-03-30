/** @type {import('next').NextConfig} */
const nextConfig = {
  output: process.env.DOCKER_BUILD === "1" ? "standalone" : undefined,
  async rewrites() {
    // Production (Vercel): no rewrites — set NEXT_PUBLIC_API_URL to your API.
    if (process.env.NODE_ENV !== "development") return [];
    return [
      { source: "/api/:path*", destination: "http://127.0.0.1:8000/api/:path*" },
      { source: "/static/:path*", destination: "http://127.0.0.1:8000/static/:path*" },
    ];
  },
};

export default nextConfig;
