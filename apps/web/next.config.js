/** @type {import('next').NextConfig} */
const isGithubPages = process.env.GITHUB_PAGES === 'true';
const repoName = 'masterqatool';

const nextConfig = {
  reactStrictMode: false,
  ...(isGithubPages
    ? {
        output: 'export',
        basePath: `/${repoName}`,
        assetPrefix: `/${repoName}/`,
        trailingSlash: true,
        images: {
          unoptimized: true,
        },
      }
    : {
        async rewrites() {
          const backendUrl = process.env.INTERNAL_API_URL || 'http://127.0.0.1:8000';
          return [
            {
              source: '/api/v1/:path*',
              destination: `${backendUrl}/api/v1/:path*`,
            },
          ];
        },
      }),
};

module.exports = nextConfig;
