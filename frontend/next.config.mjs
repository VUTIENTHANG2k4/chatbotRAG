/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  async rewrites() {
    // BACKEND_URL is a server-only env var (no NEXT_PUBLIC_ prefix so it works
    // correctly at runtime in standalone mode).
    // Fallback order:
    //   1. BACKEND_URL  (set in docker-compose for container-to-container)
    //   2. NEXT_PUBLIC_API_URL  (legacy / local dev)
    //   3. http://127.0.0.1:8000 (safe default for local Windows dev)
    const apiBase =
      process.env.BACKEND_URL ??
      process.env.NEXT_PUBLIC_API_URL ??
      "http://127.0.0.1:8000";
    return {
      beforeFiles: [
        {
          source: "/api/backend/:path*",
          destination: `${apiBase}/api/v1/:path*`,
        },
      ],
    };
  },
};

export default nextConfig;
