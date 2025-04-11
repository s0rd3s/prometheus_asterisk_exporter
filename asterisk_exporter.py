#!/usr/bin/env python3
import os
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import base64
import socket
from prometheus_client import Gauge, generate_latest, REGISTRY

# Configuration
PORT_NUMBER = 9255
METRICS_USERNAME = "usename"
METRICS_PASSWORD = "password"

# Create Prometheus metrics
host = socket.gethostname()

# Channel and call metrics
asterisk_total_active_channels = Gauge(
    "asterisk_total_active_channels",
    "Total current active channels",
    ['host', 'type']
)
asterisk_total_active_calls = Gauge(
    "asterisk_total_active_calls",
    "Total current active calls",
    ['host', 'type']
)
asterisk_total_calls_processed = Gauge(
    "asterisk_total_calls_processed",
    "Total current calls processed",
    ['host', 'type']
)

# System metrics
asterisk_system_uptime_seconds = Gauge(
    "asterisk_system_uptime_seconds",
    "System uptime in seconds",
    ['host', 'type']
)
asterisk_last_reload_seconds = Gauge(
    "asterisk_last_reload_seconds",
    "Seconds since last reload",
    ['host', 'type']
)

# SIP metrics (aggregate)
asterisk_total_sip_peers = Gauge(
    "asterisk_total_sip_peers",
    "Total SIP peers",
    ['host', 'type']
)
asterisk_total_monitored_online = Gauge(
    "asterisk_total_monitored_online",
    "Total monitored online peers",
    ['host', 'type']
)
asterisk_total_monitored_offline = Gauge(
    "asterisk_total_monitored_offline",
    "Total monitored offline peers",
    ['host', 'type']
)
asterisk_total_unmonitored_online = Gauge(
    "asterisk_total_unmonitored_online",
    "Total unmonitored online peers",
    ['host', 'type']
)
asterisk_total_unmonitored_offline = Gauge(
    "asterisk_total_unmonitored_offline",
    "Total unmonitored offline peers",
    ['host', 'type']
)

# Thread and status metrics
asterisk_total_threads = Gauge(
    "asterisk_total_threads",
    "Total threads listed",
    ['host', 'type']
)
asterisk_total_sip_status_unknown = Gauge(
    "asterisk_total_sip_status_unknown",
    "Total SIP peers with unknown status",
    ['host', 'type']
)
asterisk_total_sip_status_qualified = Gauge(
    "asterisk_total_sip_status_qualified",
    "Total SIP peers with qualified status",
    ['host', 'type']
)

# Individual SIP peer metrics
asterisk_sip_peer_status = Gauge(
    "asterisk_sip_peer_status",
    "Status of SIP peer (1=OK, 0=not OK)",
    ['host', 'peer_name', 'peer_host']
)
asterisk_sip_peer_latency = Gauge(
    "asterisk_sip_peer_latency_ms",
    "SIP peer latency in milliseconds",
    ['host', 'peer_name', 'peer_host']
)
asterisk_sip_peer_port = Gauge(
    "asterisk_sip_peer_port",
    "SIP peer port number",
    ['host', 'peer_name', 'peer_host']
)

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            # Check for basic auth
            auth_header = self.headers.get('Authorization')
            if not auth_header or not self.check_auth(auth_header):
                self.send_response(401)
                self.send_header('WWW-Authenticate', 'Basic realm=\"Asterisk Metrics\"')
                self.end_headers()
                return
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4')
            self.end_headers()
            self.wfile.write(generate_latest(REGISTRY))
        else:
            self.send_response(404)
            self.end_headers()

    def check_auth(self, auth_header):
        try:
            auth_type, auth_string = auth_header.split(' ')
            if auth_type.lower() != 'basic':
                return False
            
            decoded = base64.b64decode(auth_string).decode('utf-8')
            username, password = decoded.split(':')
            return username == METRICS_USERNAME and password == METRICS_PASSWORD
        except:
            return False

    def log_message(self, format, *args):
        # Disable logging to stdout
        return

def safe_parse_sip_peers(output):
    """Safely parse the sip show peers output, returning default values if parsing fails"""
    try:
        numbers = re.findall("\d+", output)
        if len(numbers) >= 5:
            return [int(n) for n in numbers[:5]]
    except:
        pass
    return [0, 0, 0, 0, 0]

def parse_sip_peer_line(line):
    """Parse a single SIP peer line and return relevant information"""
    # Skip header lines
    if 'Name/username' in line or '--------' in line:
        return None
    
    # Normalize whitespace - replace multiple spaces with single space
    normalized = ' '.join(line.strip().split())
    parts = normalized.split()
    
    if len(parts) < 6:  # Minimum required fields
        return None
    
    try:
        # Find where the status begins (either OK or UNKNOWN)
        status_index = next((i for i, part in enumerate(parts) 
                           if part in ('OK', 'UNKNOWN')), None)
        
        if status_index is None:
            return None
            
        peer_info = {
            'name': parts[0].split('/')[0],
            'host': parts[1],
            'status': parts[status_index],
            'latency': 0,
            'port': 0
        }
        
        # Try to find port number - it should be before the status
        for i in range(status_index - 1, max(0, status_index - 3), -1):
            if parts[i].isdigit():
                peer_info['port'] = int(parts[i])
                break
        
        # Extract latency if available
        if peer_info['status'] == 'OK' and len(parts) > status_index + 1:
            latency_match = re.search(r'\((\d+)\s*ms\)', ' '.join(parts[status_index:]))
            if latency_match:
                peer_info['latency'] = int(latency_match.group(1))
        
        return peer_info
        
    except Exception:
        return None

def gather_data():
    """Gathers the metrics from Asterisk"""
    while True:
        try:
            # Get channel and call information
            command_core_show_channels = "/usr/sbin/asterisk -rx 'core show channels' | awk '{print $1}'"
            array_core_show_channels = os.popen(command_core_show_channels).readlines()

            if len(array_core_show_channels) >= 4:
                active_channels = array_core_show_channels[1].rstrip()
                active_calls = array_core_show_channels[2].rstrip()
                calls_processed = array_core_show_channels[3].rstrip()

                asterisk_total_active_channels.labels(host=host, type="active channels").set(int(active_channels))
                asterisk_total_active_calls.labels(host=host, type="active calls").set(int(active_calls))
                asterisk_total_calls_processed.labels(host=host, type="calls processed").set(int(calls_processed))

            # Get uptime information
            command_core_show_uptime = "/usr/sbin/asterisk -rx 'core show uptime seconds' | awk '{print $3}'"
            array_core_show_uptime = os.popen(command_core_show_uptime).readlines()

            if len(array_core_show_uptime) >= 2:
                system_uptime = array_core_show_uptime[0].rstrip()
                last_reload = array_core_show_uptime[1].rstrip()

                asterisk_system_uptime_seconds.labels(host=host, type="system uptime seconds").set(int(system_uptime))
                asterisk_last_reload_seconds.labels(host=host, type="last reload seconds").set(int(last_reload))

            # Get SIP peers summary information
            command_sip_show_peers = "/usr/sbin/asterisk -rx 'sip show peers' | grep 'sip peers' | grep 'Monitored' | grep 'Unmonitored'"
            sip_show_peers = os.popen(command_sip_show_peers).read()
            
            sip_peers, monitored_online, monitored_offline, unmonitored_online, unmonitored_offline = safe_parse_sip_peers(sip_show_peers)
            
            asterisk_total_sip_peers.labels(host=host, type="total sip peers").set(sip_peers)
            asterisk_total_monitored_online.labels(host=host, type="total monitored online").set(monitored_online)
            asterisk_total_monitored_offline.labels(host=host, type="total monitored_offline").set(monitored_offline)
            asterisk_total_unmonitored_online.labels(host=host, type="total unmonitored_online").set(unmonitored_online)
            asterisk_total_unmonitored_offline.labels(host=host, type="total unmonitored offline").set(unmonitored_offline)

            # Get thread count
            command_core_show_threads = "/usr/sbin/asterisk -rx 'core show threads' | tail -1 | cut -d' ' -f1"
            core_show_threads = os.popen(command_core_show_threads).read().strip()
            if core_show_threads.isdigit():
                asterisk_total_threads.labels(host=host, type="total threads listed").set(int(core_show_threads))

            # Get SIP status counts
            command_sip_show_peers_status_unknown = "/usr/sbin/asterisk -rx 'sip show peers' | grep -P '^\\d{3,}.*UNKNOWN\\s' | wc -l"
            sip_show_peers_status_unknown = os.popen(command_sip_show_peers_status_unknown).read().strip()
            if sip_show_peers_status_unknown.isdigit():
                asterisk_total_sip_status_unknown.labels(host=host, type="total sip status unknown").set(int(sip_show_peers_status_unknown))

            command_sip_show_peers_status_qualified = "/usr/sbin/asterisk -rx 'sip show peers' | grep -P '^\\d{3,}.*OK\\s\\(\\d+' | wc -l"
            sip_show_peers_status_qualified = os.popen(command_sip_show_peers_status_qualified).read().strip()
            if sip_show_peers_status_qualified.isdigit():
                asterisk_total_sip_status_qualified.labels(host=host, type="total sip status qualified").set(int(sip_show_peers_status_qualified))

            # Get detailed SIP peers information
            command_sip_show_peers_detailed = "/usr/sbin/asterisk -rx 'sip show peers'"
            sip_show_peers_detailed = os.popen(command_sip_show_peers_detailed).read().splitlines()
            
            # Clear previous peer metrics
            asterisk_sip_peer_status.clear()
            asterisk_sip_peer_latency.clear()
            asterisk_sip_peer_port.clear()
            
            for line in sip_show_peers_detailed:
                # Skip header and summary lines
                if not line.strip() or 'sip peers' in line:
                    continue
                
                peer_info = parse_sip_peer_line(line)
                if not peer_info:
                    continue
                
                status_value = 1 if peer_info['status'] == 'OK' else 0
                
                # Set metrics
                asterisk_sip_peer_status.labels(
                    host=host,
                    peer_name=peer_info['name'],
                    peer_host=peer_info['host']
                ).set(status_value)
                
                asterisk_sip_peer_latency.labels(
                    host=host,
                    peer_name=peer_info['name'],
                    peer_host=peer_info['host']
                ).set(peer_info['latency'])
                
                asterisk_sip_peer_port.labels(
                    host=host,
                    peer_name=peer_info['name'],
                    peer_host=peer_info['host']
                ).set(int(peer_info['port']))

        except Exception as e:
            print(f"Error gathering metrics: {e}")

        time.sleep(1)

if __name__ == "__main__":
    # Start the metrics gathering thread
    thread = threading.Thread(target=gather_data)
    thread.daemon = True
    thread.start()

    # Start the HTTP server
    server = ThreadedHTTPServer(('', PORT_NUMBER), MetricsHandler)
    print(f"Starting server on port {PORT_NUMBER}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        thread.join()