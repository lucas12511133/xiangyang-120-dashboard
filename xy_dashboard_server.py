#!/usr/bin/env python3
"""启动 v3 仪表盘服务器: python v3_dashboard_server.py"""
import http.server, json, os, sys, webbrowser, urllib.parse, urllib.request
from pathlib import Path

PORT = 8088
DIR = Path(__file__).parent / 'xy_data'

# 腾讯地图 POI 搜索 Key (代理转发用, 不暴露给前端)
TENCENT_KEY = os.environ.get("TENCENT_MAP_KEY", "").strip()

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIR), **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        # 代理腾讯地图 POI 搜索: /geocode?q=关键词
        if parsed.path == '/geocode':
            if not TENCENT_KEY:
                self.send_response(503)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 503, 'message': '请在服务器设置TENCENT_MAP_KEY后使用地名搜索'}, ensure_ascii=False).encode('utf-8'))
                return
            qs = urllib.parse.parse_qs(parsed.query)
            keyword = qs.get('q', [''])[0].strip()
            if not keyword:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({'status': 400, 'message': '缺少q参数'}).encode('utf-8'))
                return
            try:
                url = ('https://apis.map.qq.com/ws/place/v1/search?'
                       + urllib.parse.urlencode({
                           'keyword': keyword,
                           'key': TENCENT_KEY,
                           'boundary': 'region(襄阳,0)',
                           'page_size': 8,
                       }))
                req = urllib.request.Request(url, headers={'User-Agent': 'WorkBuddy/1.0'})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = resp.read().decode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(data.encode('utf-8'))
                return
            except Exception as e:
                self.send_response(502)
                self.end_headers()
                self.wfile.write(json.dumps({'status': 502, 'message': str(e)}).encode('utf-8'))
                return
        # 普通静态文件
        super().do_GET()

print(f"\n[襄阳] 仪表盘服务器启动: http://localhost:{PORT}/dashboard.html")
print(f"[v3] 按 Ctrl+C 停止\n")
webbrowser.open(f'http://localhost:{PORT}/dashboard.html')
http.server.HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
