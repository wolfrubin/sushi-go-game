// The UI is exported as static files and served by Caddy, so no Node server
// is needed in production. Set SUGO_BASE_PATH (e.g. /sushi) to serve it from
// a sub path.
/** @type {import('next').NextConfig} */
module.exports = {
  reactStrictMode: true,
  output: 'export',
  basePath: process.env.SUGO_BASE_PATH || '',
  images: { unoptimized: true },
};
