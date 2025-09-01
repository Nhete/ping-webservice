from flask import Flask, jsonify, request
import subprocess

app = Flask(__name__)

@app.route("/ping", methods=["POST"])
def ping_host():
    """
    Expects JSON payload:
    {
        "ip": "41.57.66.41",
        "count": 4,
        "size": 1400
    }
    Returns JSON with success rate.
    """
    data = request.get_json()
    ip = data.get("ip")
    count = data.get("count", 4)
    size = data.get("size", 1400)

    if not ip:
        return jsonify({"error": "IP address is required"}), 400

    try:
        # Run ping safely without requiring root privileges
        result = subprocess.run(
            ["ping", "-c", str(count), "-s", str(size), "-M", "do", ip],
            capture_output=True,
            text=True,
            check=False
        )
        output = result.stdout
        # Parse success rate from ping output
        success_line = [line for line in output.splitlines() if "packet loss" in line]
        success_rate = None
        if success_line:
            success_rate = 100 - float(success_line[0].split("%")[0].split()[-1])

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
    # Use 0.0.0.0 so Render can access it
    app.run(host="0.0.0.0", port=10000)
