from flask import Flask, jsonify, request, render_template
import subprocess
import os

app = Flask(__name__)

FILTER_FILE = "filter_hosts.txt"  # file containing IPs for batch testing

# Simple GET endpoint for quick service check
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")  # Serve the UI page

# POST endpoint to run ping test on a single IP
@app.route("/ping", methods=["POST"])
def ping_host():
    data = request.get_json()
    ip = data.get("ip")
    count = data.get("count", 4)
    size = data.get("size", 1400)

    if not ip:
        return jsonify({"error": "IP address is required"}), 400

    try:
        result = subprocess.run(
            ["ping", "-c", str(count), "-s", str(size), "-M", "do", ip],
            capture_output=True,
            text=True,
            check=False
        )
        output = result.stdout
        success_rate, packet_loss = None, None
        for line in output.splitlines():
            if "packet loss" in line:
                packet_loss = float(line.split("%")[0].split()[-1])
                success_rate = 100 - packet_loss

        return jsonify({
            "ip": ip,
            "count": count,
            "size": size,
            "success_rate": success_rate,
            "packet_loss": packet_loss,
            "output": output
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# GET endpoint to ping all IPs from filter_hosts.txt
@app.route("/ping_all", methods=["GET"])
def ping_all():
    if not os.path.exists(FILTER_FILE):
        return jsonify({"error": f"{FILTER_FILE} not found"}), 400

    results = []
    with open(FILTER_FILE) as f:
        ips = [line.strip() for line in f if line.strip()]

    for ip in ips:
        try:
            result = subprocess.run(
                ["ping", "-c", "4", "-s", "1400", "-M", "do", ip],
                capture_output=True,
                text=True,
                check=False
            )
            output = result.stdout
            success_rate, packet_loss = None, None
            for line in output.splitlines():
                if "packet loss" in line:
                    packet_loss = float(line.split("%")[0].split()[-1])
                    success_rate = 100 - packet_loss

            results.append({
                "ip": ip,
                "count": 4,
                "size": 1400,
                "success_rate": success_rate,
                "packet_loss": packet_loss
            })
        except Exception as e:
            results.append({
                "ip": ip,
                "count": 4,
                "size": 1400,
                "success_rate": None,
                "packet_loss": None,
                "error": str(e)
            })

    return jsonify(results)


if __name__ == "__main__":
    # Use 0.0.0.0 so Render can access it
    app.run(host="0.0.0.0", port=10000)
