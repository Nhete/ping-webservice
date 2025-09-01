import os
from flask import Flask, jsonify, request, render_template
import subprocess
import socket
import traceback

app = Flask(__name__)
ping_results = {}

# Load filtered hosts
def load_filtered_hosts():
    hosts = []
    try:
        with open("filtered_hosts.txt") as f:
            for line in f:
                line = line.strip()
                if line:
                    hosts.append(line)
    except FileNotFoundError:
        pass
    return hosts

filtered_hosts = load_filtered_hosts()

# TCP fallback check
def check_tcp(ip, port=5060, timeout=2):
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return 100
    except Exception:
        return 0

# Safe ICMP ping
def run_ping(ip, count=4, size=1400):
    try:
        result = subprocess.run(
            ["ping", "-c", str(count), "-s", str(size), "-M", "do", ip],
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
            return success_rate, output, "ICMP ping"
        else:
            return None, output, None
    except Exception as e:
        print(f"Ping subprocess error for {ip}: {e}")
        return None, f"Ping command failed: {e}", None

# Pre-populate overview with TCP fallback
for host in filtered_hosts:
    if host not in ping_results:
        success_rate = check_tcp(host)
        output = "Initial TCP check" if success_rate == 100 else "TCP check failed"
        ping_results[host] = {"success_rate": success_rate, "output": output, "status": "TCP fallback"}

@app.route("/", methods=["GET"])
def home():
    # Compute summary
    total_hosts = len(filtered_hosts)
    success_100 = [ip for ip, data in ping_results.items() if data["success_rate"] == 100]
    partial = [ip for ip, data in ping_results.items() if 0 < data["success_rate"] < 100]
    failed = [ip for ip, data in ping_results.items() if data["success_rate"] == 0]

    summary = {
        "total_hosts": total_hosts,
        "success_100": success_100,
        "partial": partial,
        "failed": failed
    }

    return render_template(
        "index.html",
        results=ping_results,
        hosts=filtered_hosts,
        summary=summary
    )

@app.route("/ping", methods=["POST"])
def ping_host():
    try:
        data = request.get_json()
        ip = data.get("ip")
        count = data.get("count", 4)
        size = data.get("size", 1400)

        if not ip:
            return jsonify({"error": "IP address is required"}), 400

        # Run ICMP ping
        success_rate, output, status = run_ping(ip, count, size)

        # TCP fallback if ICMP fails
        if success_rate is None:
            success_rate = check_tcp(ip)
            output = "Ping blocked or failed, used TCP fallback"
            status = "TCP fallback"

        ping_results[ip] = {"success_rate": success_rate, "output": output, "status": status}

        return jsonify({
            "ip": ip,
            "count": count,
            "size": size,
            "success_rate": success_rate,
            "output": output,
            "status": status
        })

    except Exception as e:
        print("ERROR in /ping:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
