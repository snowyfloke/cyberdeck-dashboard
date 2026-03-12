from flask import jsonify
import psutil
import platform
from flask import Flask

app = Flask(__name__)

@app.route("/stats")
def stats():
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\" if platform.system() == "Windows" else "/")
    return jsonify({
        "cpu_percent":      psutil.cpu_percent(interval=0.5),
        "ram_percent":      ram.percent,
        "ram_used_gb":      round(ram.used   / 1024**3, 1),
        "ram_total_gb":     round(ram.total  / 1024**3, 1),
        "disk_percent":     disk.percent,
        "disk_used_gb":     round(disk.used  / 1024**3, 1),
        "disk_total_gb":    round(disk.total / 1024**3, 1),
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

