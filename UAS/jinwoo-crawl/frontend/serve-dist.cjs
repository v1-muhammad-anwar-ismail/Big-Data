/**
 * Zero-dependency production static & SPA server for JinwooCrawl frontend/dist.
 * Built with Node.js core modules only so ARM Linux STBs need no node_modules at runtime.
 */
const http = require("http");
const fs = require("fs");
const path = require("path");

const HOST = process.env.HOST || "0.0.0.0";
const PORT = Number(process.env.PORT || 5001);
const DIST_DIR = path.resolve(__dirname, "dist");
const INDEX_FILE = path.join(DIST_DIR, "index.html");

const MIME_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".mjs": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".ico": "image/x-icon",
  ".txt": "text/plain; charset=utf-8",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
};

function sendFile(res, filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const contentType = MIME_TYPES[ext] || "application/octet-stream";
  const cacheControl = filePath.includes(`${path.sep}assets${path.sep}`)
    ? "public, max-age=31536000, immutable"
    : "no-cache";

  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("Internal Server Error");
      return;
    }
    res.writeHead(200, {
      "Content-Type": contentType,
      "Cache-Control": cacheControl,
    });
    res.end(data);
  });
}

const server = http.createServer((req, res) => {
  const urlPath = decodeURIComponent((req.url || "/").split("?")[0]);
  const safeRel = urlPath.replace(/^\/+/, "");
  const targetPath = path.resolve(DIST_DIR, safeRel || "index.html");

  if (!targetPath.startsWith(DIST_DIR)) {
    res.writeHead(403, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Forbidden");
    return;
  }

  fs.stat(targetPath, (err, stat) => {
    if (!err && stat.isFile()) {
      sendFile(res, targetPath);
      return;
    }
    if (urlPath.startsWith("/assets/")) {
      res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("Not Found");
      return;
    }
    sendFile(res, INDEX_FILE);
  });
});

server.listen(PORT, HOST, () => {
  console.log(`[JinwooCrawl Frontend] Serving dist/ on http://${HOST}:${PORT}`);
});
