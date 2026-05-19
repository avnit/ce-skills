#!/bin/bash
apt-get update && apt-get install -y python3
mkdir -p /var/www
cat << "EOF2" > /var/www/index.py
import http.server
import urllib.request
import json

class MetadataHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Fetch Metadata details
        req_name = urllib.request.Request("http://metadata.google.internal/computeMetadata/v1/instance/name")
        req_name.add_header("Metadata-Flavor", "Google")
        name = urllib.request.urlopen(req_name).read().decode("utf-8")

        req_zone = urllib.request.Request("http://metadata.google.internal/computeMetadata/v1/instance/zone")
        req_zone.add_header("Metadata-Flavor", "Google")
        zone = urllib.request.urlopen(req_zone).read().decode("utf-8").split("/")[-1]
        region = "-".join(zone.split("-")[:-1])

        # Serve Premium Dark Mode page
        html = f"""<!DOCTYPE html>
<html>
<head>
  <title>Global Load Balancer Demo</title>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
  <style>
    body {{
      margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh;
      background: radial-gradient(circle at center, #0f172a, #020617); font-family: "Outfit", sans-serif; color: #f8fafc;
    }}
    .card {{
      padding: 40px; border-radius: 24px; background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.08); box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4); text-align: center; max-width: 500px; width: 100%;
    }}
    h1 {{
      font-size: 32px; font-weight: 800; background: linear-gradient(to right, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 24px;
    }}
    .stat {{
      margin: 16px 0; padding: 16px; border-radius: 12px; background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.04); transition: transform 0.3s ease;
    }}
    .stat:hover {{
      transform: translateY(-2px); background: rgba(255, 255, 255, 0.04);
    }}
    .label {{ font-size: 12px; text-transform: uppercase; letter-spacing: 1.5px; color: #94a3b8; margin-bottom: 4px; }}
    .value {{ font-size: 20px; font-weight: 600; color: #f1f5f9; }}
    .badge {{
      display: inline-block; padding: 6px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; background: #0284c7; color: #e0f2fe; margin-top: 20px;
    }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Global HTTP Load Balancer</h1>
    <div class="stat">
      <div class="label">Served by Server</div>
      <div class="value">{name}</div>
    </div>
    <div class="stat">
      <div class="label">Hosting Region / Zone</div>
      <div class="value">{zone} ({region})</div>
    </div>
    <span class="badge">Active Routing</span>
  </div>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

server = http.server.HTTPServer(("", 80), MetadataHandler)
server.serve_forever()
EOF2
python3 /var/www/index.py >/dev/null 2>&1 &
