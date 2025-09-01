import os
from flask import Flask, jsonify, request, render_template
import subprocess
import socket

app = Flask(__name__)
ping_results = {}

# Load filtered hosts from file
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

# TCP fallback for Render
def check_tcp(ip, port=5060, timeout=2):
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return 100
    except Exception:
        return 0

@app.route("/", methods=["GET"])
def home():
    return render_template(
        "index.html",
        results=ping_results,
        hosts=filtered_hosts
    )

@app.route("/ping", methods=["POST"])
def ping_host():
    data = request.get_json()
    ip = data.get("ip")
    count = data.get("count", 4)
    size = data.get("size", 1400)

    if not ip:
        return jsonify({"error": "IP address is required"}), 400

    try:
        # Try ICMP ping
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

        # Fallback TCP check if ping fails
        if success_rate is None:
            success_rate = check_tcp(ip)
            output = "Ping blocked or failed, used TCP check instead"

        ping_results[ip] = {"success_rate": success_rate, "output": output}

        return jsonify({
            "ip": ip,
            "count": count,
            "size": size,
            "success_rate": success_rate,
            "output": output
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
