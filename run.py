import eventlet
eventlet.monkey_patch(all=True)

# Import everything we need from app.py
from app import (app, socketio, udp_listener, 
                 camera_check, wifi_check, 
                 broadcaster, auto_recovery)   # ← THIS LINE ADDED

import threading, time, socket

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]
    except: ip = "127.0.0.1"
    finally: s.close()
    return ip

if __name__ == "__main__":
    threading.Thread(target=udp_listener, daemon=True).start()
    threading.Thread(target=camera_check, daemon=True).start()
    threading.Thread(target=wifi_check,   daemon=True).start()
    threading.Thread(target=auto_recovery, daemon=True).start()   # ← NOW WORKS!
    threading.Thread(target=broadcaster,  daemon=True).start()

    time.sleep(1)
    ip = get_local_ip()
    print(f"\nOPEN ON ANY DEVICE → http://{ip}:5000\n")
    socketio.run(app, host="0.0.0.0", port=5000)