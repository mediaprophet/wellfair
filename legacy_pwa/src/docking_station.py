# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Docking Station RPC Server.

Acts as a local desktop gateway. Receives offloaded federated jobs (like LLM 
inference, Sleep Analytics, N3 Reasoning) from the Phone Vault via the 
WebRTC Connector, processes them locally using heavy desktop resources, and 
returns the stateless JSON results. 

NO health data is permanently saved to disk here.
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import pandas as pd
from urllib.parse import urlparse, parse_qs

# Import the desktop-bound extensions
from src.sleep_analytics import SleepMetrics
from extensions.local_llm import LocalLLMExtension

# Ephemeral Proxy State (Flushed on restart)
in_memory_vault = {
    "linked": False,
    "last_sync": None,
    "data": {}
}

class DockingStationHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        # Serve the ephemeral vault state to Streamlit
        self.send_response(200)
        self._set_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(in_memory_vault).encode())

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            req = json.loads(post_data)
            job_type = req.get('job_type')
            payload = req.get('payload', {})
            
            result = None
            
            if job_type == 'vault.sync':
                # The phone connector is pushing live data to the proxy
                section = payload.get('section')
                if section:
                    in_memory_vault['data'][section] = payload.get('data')
                    in_memory_vault['linked'] = True
                    result = {"status": "ok", "synced": section}
                else:
                    result = {"error": "No section provided"}
                    
            elif job_type == 'vault.disconnect':
                in_memory_vault['linked'] = False
                in_memory_vault['data'] = {}
                result = {"status": "flushed"}

            elif job_type == 'sleep.analyze':
                # Reconstruct DataFrame from payload and run heavy pandas analytics
                df = pd.DataFrame(payload.get('sleep_data', []))
                # Generalised sleep analysis (no Samsung specific keys here)
                if not df.empty:
                    durations = df.get('sleep_duration', pd.Series([420])).mean()
                    efficiencies = df.get('efficiency', pd.Series([85])).mean()
                    score = SleepMetrics.calculate_sleep_score(durations, efficiencies)
                    result = {"sleep_score": score, "average_duration_mins": durations, "average_efficiency": efficiencies}
                else:
                    result = {"error": "Empty sleep data provided"}
                    
            elif job_type == 'llm.extract':
                # Run local Ollama extraction
                text = payload.get('text', '')
                llm = LocalLLMExtension()
                if llm.is_available():
                    result = llm.extract_health_data(text)
                else:
                    result = {"error": "Local LLM daemon not running"}
                    
            else:
                result = {"skipped": True, "reason": f"Unknown docking station job: {job_type}"}

            self.send_response(200)
            self._set_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self.send_response(500)
            self._set_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

def run(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, DockingStationHandler)
    print(f"[Docking Station] Running federated RPC server on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
