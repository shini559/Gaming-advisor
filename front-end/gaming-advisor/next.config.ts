import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    serverActions: {
      bodySizeLimit: '10mb', // On augmente la limite à 10 Mo
    },
  },
};

export default nextConfig;