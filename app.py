# app.py – ONLY APP LOGIC (NO __main__)
from flask import Flask, render_template
from flask_socketio import SocketIO
import time, json, socket, platform

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

status = {
    "Camera":   {"val": "N/A",     "last": time.time(), "extra": "Pi only"},
    "TOF":      {"val": "OK",      "last": time.time(), "extra": "No error"},
    "MotorESP": {"val": "OK",      "last": time.time(), "extra": "Enc: 0,0"},
    "WiFi":     {"val": "N/A",     "last": time.time(), "extra": "Windows"},
    "UWB":      {"val": "No data", "last": time.time(), "extra": "x: -, y: -"},
}

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
                status[node]["val"]   = msg.get("status", "OK")
                status[node]["extra"] = msg.get("extra", "")
                status[node]["last"]  = time.time()
        except:
            pass

def wifi_check():
    while True:
        if platform.system() != "Windows":
            try:
                import netifaces, subprocess
                iface = netifaces.gateways()['default'][netifaces.AF_INET][1]
                out = subprocess.check_output(["iwconfig", iface]).decode()
                rssi = out.split("Signal level=")[1].split(" dBm")[0].strip()
                status["WiFi"]["val"]   = "OK"
                status["WiFi"]["extra"] = f"{rssi} dBm"
            except:
                status["WiFi"]["val"]   = "FAIL"
                status["WiFi"]["extra"] = "No AP"
        else:
            status["WiFi"]["val"]   = "N/A"
            status["WiFi"]["extra"] = "Windows"
        status["WiFi"]["last"] = time.time()
        time.sleep(5)

def camera_check():
    while True:
        if platform.system() != "Windows":
            try:
                from picamera2 import Picamera2
                cam = Picamera2()
                cam.start_preview()
                cam.capture_file("/dev/null")
                cam.stop_preview()
                status["Camera"]["val"] = "OK"
                status["Camera"]["extra"] = ""
            except Exception as e:
                status["Camera"]["val"] = "FAIL"
                status["Camera"]["extra"] = str(e)[:30]
        else:
            status["Camera"]["val"] = "N/A"
            status["Camera"]["extra"] = "Pi only"
        status["Camera"]["last"] = time.time()
        time.sleep(5)

def watchdog():
    while True:
        now = time.time()
        for key in status:
            if now - status[key]["last"] > 15 and key != "Camera":
                status[key]["val"] = "Crash"
        time.sleep(5)

def broadcaster():
    while True:
        socketio.emit("update", status)
        time.sleep(2)

@app.route("/")
def index():
    return render_template("index.html")