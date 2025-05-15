const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:5000',
      changeOrigin: true,
      secure: false,
      logLevel: 'debug', // Add this to see detailed logs
      onProxyReq: (proxyReq, req, res) => {
        console.log(`Proxying request to: ${req.url}`);
      },
      onProxyRes: (proxyRes, req, res) => {
        console.log(`Received response from proxy: ${proxyRes.statusCode}`);
      },
      onError: (err, req, res) => {
        console.error('Proxy error:', err);
        res.writeHead(500, {
          'Content-Type': 'text/plain',
        });
        res.end(`Proxy error: ${err.message}`);
      }
    })
  );
};