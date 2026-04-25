#!/usr/bin/env node
// Node.js ESM bridge server
// リバースプロキシとして difitへのリクエストを中継しつつ、
// HTML レスポンスに JavaScript を注入してコメント送信を監視

import { createServer } from 'http';
import { request as httpRequest } from 'http';
import { execFile } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// コマンドライン引数パース
let difitPort = 4966;
let bridgePort = 4967;

for (let i = 2; i < process.argv.length; i++) {
  if (process.argv[i] === '--difit-port' && i + 1 < process.argv.length) {
    difitPort = parseInt(process.argv[i + 1], 10);
    i++;
  } else if (process.argv[i] === '--bridge-port' && i + 1 < process.argv.length) {
    bridgePort = parseInt(process.argv[i + 1], 10);
    i++;
  }
}

// リバースプロキシハンドラー
const proxyServer = createServer((req, res) => {
  // /bridge/send-to-claude エンドポイント
  if (req.url === '/bridge/send-to-claude' && req.method === 'POST') {
    handleSendToClaude(req, res);
    return;
  }

  // その他のリクエストは difit に中継
  proxyToDifit(req, res);
});

function proxyToDifit(req, res) {
  const options = {
    hostname: 'localhost',
    port: difitPort,
    path: req.url,
    method: req.method,
    headers: req.headers,
  };

  const proxyReq = httpRequest(options, (proxyRes) => {
    // レスポンスヘッダーをコピー
    const contentType = proxyRes.headers['content-type'] || '';
    const isHtml = contentType.includes('text/html');

    if (isHtml) {
      // HTMLの場合、バッファリングしてscriptを注入
      let body = '';

      proxyRes.on('data', (chunk) => {
        body += chunk.toString();
      });

      proxyRes.on('end', () => {
        // </body> の直前に script を挿入
        const injectedScript = getInjectionScript();
        const injected = body.replace(
          '</body>',
          `${injectedScript}</body>`
        );

        // レスポンスを返す
        Object.keys(proxyRes.headers).forEach((key) => {
          res.setHeader(key, proxyRes.headers[key]);
        });
        res.writeHead(proxyRes.statusCode || 200);
        res.end(injected);
      });
    } else {
      // HTML以外はそのまま中継
      Object.keys(proxyRes.headers).forEach((key) => {
        res.setHeader(key, proxyRes.headers[key]);
      });
      res.writeHead(proxyRes.statusCode || 200);
      proxyRes.pipe(res);
    }
  });

  proxyReq.on('error', (err) => {
    console.error('Proxy error:', err);
    res.writeHead(502);
    res.end('Bad Gateway');
  });

  req.pipe(proxyReq);
}

function handleSendToClaude(req, res) {
  // CORS対応
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  let body = '';

  req.on('data', (chunk) => {
    body += chunk.toString();
  });

  req.on('end', () => {
    try {
      const data = JSON.parse(body);
      const text = data.text || '';

      // cmux-send-claude を実行（親プロセスの環境変数を継承）
      const cmdPath = path.join(__dirname, 'cmux-send-claude.sh');
      execFile(cmdPath, [text], { env: { ...process.env } }, (error, stdout, stderr) => {
        if (error) {
          console.error('cmux-send-claude error:', error, stderr);
        } else {
          console.log('Sent to Claude:', text.substring(0, 50) + '...');
        }
      });

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'ok' }));
    } catch (err) {
      console.error('Failed to parse request body:', err);
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'error', message: 'Invalid JSON' }));
    }
  });
}

function getInjectionScript() {
  return `<script>
(function() {
  const originalFetch = window.fetch;

  window.fetch = function(...args) {
    const [resource, config] = args;
    const url = typeof resource === 'string' ? resource : resource.url;

    // POST /api/comments をインターセプト
    if (url && url.includes('/api/comments') && config && config.method === 'POST') {
      // 元のfetchを実行（元のリクエスト本体を取得）
      const fetchPromise = originalFetch.apply(this, args);

      // リクエスト本体を取得
      let requestBody = config.body;
      if (typeof requestBody === 'string') {
        try {
          requestBody = JSON.parse(requestBody);
        } catch {
          // JSONパースに失敗した場合はそのまま
        }
      }

      // コメント送信を非同期で実行（元のfetchには影響しない）
      if (requestBody && requestBody.comments && Array.isArray(requestBody.comments)) {
        const comments = requestBody.comments;
        const lines = comments.map(comment => {
          const file = comment.file || '';
          const line = Array.isArray(comment.line)
            ? comment.line.join('-')
            : (comment.line || '?');
          const body = comment.body || '';
          return \`\${file}:L\${line}\\n\${body}\`;
        });
        const text = lines.join('\\n\\n');

        // ブリッジサーバーに送信（originalFetchでmonkey-patch再帰を回避）
        const bridgeUrl = \`http://localhost:\${window.location.port}/bridge/send-to-claude\`;
        originalFetch(bridgeUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text })
        }).catch(err => {
          console.error('Failed to send to Claude bridge:', err);
        });
      }

      return fetchPromise;
    }

    return originalFetch.apply(this, args);
  };
})();
</script>`;
}

proxyServer.listen(bridgePort, 'localhost', () => {
  console.log(`Bridge server listening on http://localhost:${bridgePort}`);
  console.log(`Proxying to difit at http://localhost:${difitPort}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('Bridge server shutting down...');
  proxyServer.close();
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('Bridge server interrupted...');
  proxyServer.close();
  process.exit(0);
});
