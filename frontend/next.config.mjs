/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Изоляция от внешних трекеров вне РФ — конфигурируется на проде (NFR-1).
  poweredByHeader: false,
};

export default nextConfig;
