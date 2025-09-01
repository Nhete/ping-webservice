import os
import socket
import subprocess
import traceback
from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)
ping_results = {}

# Load hosts from file
def load_hosts(filename="filtered_hosts.txt"):
    hosts = []
    try:
        with open(filename) as f:
            for line in f:
                host = line.strip()
                if host:
                    hosts.append(host)
    except FileNotFoundError:
        pass
    return hosts

hosts = load_hosts()

# ICMP ping (works locally)
def icmp_ping(host, count=4, size=1400):
    try:
        result = subprocess.run(
            ["ping", "-c", str(count), "-s", str(size), "-M", "do", host],
            capture_output=True,
            text=True,
            check=False
        )
        output = result.stdout
        success_rate = None
        for line in output.splitlines():
            if "packet loss" in line:
                success_rate = 100 - float(line.split("%")[0].split()[-1])
        if success_rate is not None:
            return success_rate, "ICMP ping"
    except Exception as e:
        pass
    return None, None

# TCP multi-port check
def tcp_check(host, ports=[22, 80, 443], timeout=2):
    for port in ports:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return 100, f"TCP reachable on port {port}"
        except Exception:
            continue
    return 0, "TCP check failed"

# HTTP GET fallback
def http_check(host):
    try:
        url = host if host.startswith("http") else f"http://{host}"
        r = requests.get(url, timeout=2)
        if r.status_code < 400:
            return 100, f"HTTP reachable ({r.status_code})"
    except Exception:
        pass
    return 0, "HTTP check failed"

# Full host check: ICMP -> TCP -> HTTP
def check_host(host):
    # ICMP ping first
    success, status = icmp_ping(host)
    if success is not None:
        return success, status

    # TCP fallback
    success, status = tcp_check(host)
    if success:
        return success, status

    # HTTP fallback
    success, status = http_check(host)
    return success, status

# Prepopulate ping_results for overview
for host in hosts:
    success_rate, status = check_host(host)
    ping_results[host] = {"success_rate": success_rate, "status": status}

# Home page
@app.route("/")
def home():
    total_hosts = len(hosts)
    success_100 = [h for h, d in ping_results.items() if d["success_rate"] == 100]
    partial = [h for h, d in ping_results.items() if 0 < d["success_rate"] < 100]
    failed = [h for h, d in ping_results.items() if d["success_rate"] == 0]

    summary = {
        "total": total_hosts,
        "success_100": success_100,
        "partial": partial,
        "failed": failed
    }

    return render_template("index.html", results=ping_results, summary=summary)

# Ping endpoint for live checks
@app.route("/ping", methods=["POST"])
def ping_host():
    try:
        data = request.get_json()
        host = data.get("host")
        if not host:
            return jsonify({"error": "Host is required"}), 400

        success, status = check_host(host)
        ping_results[host] = {"success_rate": success, "status": status}

        return jsonify({
            "host": host,
            "success_rate": success,
            "status": status
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
