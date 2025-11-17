# app.py – AUTO RECOVER TO "OK" after 10 seconds of silence
from flask import Flask, render_template
from flask_socketio import SocketIO
import time, json, socket, platform

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

status = {
    "Camera":   {"val": "OK", "last": time.time(), "extra": "Pi only"},
    "TOF":      {"val": "OK", "last": time.time(), "extra": "No error"},
    "MotorESP": {"val": "OK", "last": time.time(), "extra": "Enc: 0,0"},
    "WiFi":     {"val": "OK", "last": time.time(), "extra": "Connected"},
    "UWB":      {"val": "OK", "last": time.time(), "extra": "x: -, y: -"},
}

# -------------------------------------------------
# 1. UDP Listener – accepts ALL nodes
# -------------------------------------------------
def udp_listener():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", 5005))
    s.settimeout(1.0)
    print("UDP listener running on port 5005")
    while True:
        try:
            data, _ = s.recvfrom(1024)
            msg = json.loads(data.decode())
            node = msg.get("node")
            if node in status:
                new_val   = msg.get("status", "OK")
                new_extra = msg.get("extra", "")

                # Always refresh timestamp
                status[node]["last"] = time.time()

                # Update only if changed
                if status[node]["val"] != new_val or status[node]["extra"] != new_extra:
                    status[node]["val"]   = new_val
                    status[node]["extra"] = new_extra
                    socketio.emit("update", status)
        except:
            pass

# -------------------------------------------------
# 2. Auto‑recovery watchdog – back to OK after 10 sec silence
# -------------------------------------------------
def auto_recovery():
    while True:
        now = time.time()
        changed = False
        for node in status:
            if now - status[node]["last"] > 10:           # 10 seconds no packet
                if status[node]["val"] != "OK":           # only if it was FAIL/Crash
                    status[node]["val"] = "OK"
                    status[node]["extra"] = "Recovered"
                    changed = True
        if changed:
            socketio.emit("update", status)
        time.sleep(2)

# -------------------------------------------------
# (Camera / WiFi / broadcaster stay exactly the same)
# -------------------------------------------------
def camera_check(): ...   # ← keep your existing code
def wifi_check():   ...   # ← keep your existing code
def broadcaster():
    while True:
        socketio.emit("update", status)
        time.sleep(2)

@app.route("/")
def index():
    return render_template("index.html")