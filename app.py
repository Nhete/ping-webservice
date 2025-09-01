from flask import Flask, jsonify, request, render_template
import subprocess
import socket

app = Flask(__name__)

# In-memory storage for all ping results
ping_results = {}

# TCP check fallback for Render
def check_tcp(ip, port=5060, timeout=2):
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return 100  # reachable
    except Exception:
        return 0  # unreachable

# Home page
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html", results=ping_results)

# Ping endpoint
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
        
        # Fallback for Render
        if success_rate is None:
            success_rate = check_tcp(ip)
            output = "Ping blocked, used TCP check instead"

        # Save in memory
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
    app.run(host="0.0.0.0", port=10000)
