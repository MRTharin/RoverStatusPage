# app.py – FINAL: TOF, MotorESP, UWB behave like Camera/WiFi (NO auto‑crash)
from flask import Flask, render_template
from flask_socketio import SocketIO
import time, json, socket, platform

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# Everything starts OK and stays OK unless explicitly told otherwise
status = {
    "Camera":   {"val": "OK", "last": time.time(), "extra": "Pi only"},
    "TOF":      {"val": "OK", "last": time.time(), "extra": "No error"},
    "MotorESP": {"val": "OK", "last": time.time(), "extra": "Enc: 0,0"},
    "WiFi":     {"val": "OK", "last": time.time(), "extra": "Connected"},
    "UWB":      {"val": "OK", "last": time.time(), "extra": "x: -, y: -"},
}

# -------------------------------------------------
# 1. UDP Listener – ONLY source of truth for TOF/MotorESP/UWB
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
                new_val   = msg.get("status", "OK")      # "OK", "FAIL", "ERROR", etc.
                new_extra = msg.get("extra", "")
                # Update ONLY if something changed
                if (status[node]["val"] != new_val or 
                    status[node]["extra"] != new_extra):
                    status[node]["val"]   = new_val
                    status[node]["extra"] = new_extra
                    status[node]["last"]  = time.time()
                    socketio.emit("update", status)
                else:
                    # Even if nothing changed, refresh timestamp so it never looks dead
                    status[node]["last"] = time.time()
        except:
            pass

# -------------------------------------------------
# 2. Camera check – stable, only updates on real change
# -------------------------------------------------
def camera_check():
    while True:
        if platform.system() != "Windows":
            try:
                from picamera2 import Picamera2
                cam = Picamera2()
                cam.start_preview()
                cam.capture_file("/dev/null")
                cam.stop_preview()
                if status["Camera"]["val"] != "OK":
                    status["Camera"]["val"] = "OK"
                    status["Camera"]["extra"] = ""
                    status["Camera"]["last"] = time.time()
                    socketio.emit("update", status)
            except Exception as e:
                if status["Camera"]["val"] != "FAIL":
                    status["Camera"]["val"] = "FAIL"
                    status["Camera"]["extra"] = "Cam error"
                    status["Camera"]["last"] = time.time()
                    socketio.emit("update", status)
        else:
            status["Camera"]["extra"] = "Pi only"
        time.sleep(5)

# -------------------------------------------------
# 3. WiFi check – stable, only updates on real change
# -------------------------------------------------
def wifi_check():
    while True:
        if platform.system() != "Windows":
            try:
                import netifaces, subprocess
                iface = netifaces.gateways()["default"][netifaces.AF_INET][1]
                out = subprocess.check_output(["iwconfig", iface]).decode()
                rssi = out.split("Signal level=")[1].split(" dBm")[0].strip()
                new_extra = f"{rssi} dBm"
                if status["WiFi"]["val"] != "OK" or status["WiFi"]["extra"] != new_extra:
                    status["WiFi"]["val"] = "OK"
                    status["WiFi"]["extra"] = new_extra
                    status["WiFi"]["last"] = time.time()
                    socketio.emit("update", status)
            except:
                if status["WiFi"]["val"] != "FAIL":
                    status["WiFi"]["val"] = "FAIL"
                    status["WiFi"]["extra"] = "No signal"
                    status["WiFi"]["last"] = time.time()
                    socketio.emit("update", status)
        time.sleep(5)

# -------------------------------------------------
# 4. Broadcaster – keeps browser alive
# -------------------------------------------------
def broadcaster():
    while True:
        socketio.emit("update", status)
        time.sleep(2)

# -------------------------------------------------
# Web route
# -------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")