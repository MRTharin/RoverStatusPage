# run.py – FINAL, NO RLOCK WARNING, PERFECT STARTUP
import eventlet
eventlet.monkey_patch(all=True)   # <-- FULL PATCH FIRST

from app import app, socketio, udp_listener, wifi_check, camera_check, watchdog, broadcaster
import threading, time

if __name__ == "__main__":
    # Start background threads
    threading.Thread(target=udp_listener, daemon=True).start()
    threading.Thread(target=wifi_check,   daemon=True).start()
    threading.Thread(target=camera_check, daemon=True).start()
    threading.Thread(target=watchdog,     daemon=True).start()
    threading.Thread(target=broadcaster,  daemon=True).start()

    # Tiny delay so UDP listener is ready before browser connects
    time.sleep(1)

    print("Open http://127.0.0.1:5000")
    socketio.run(app, host="0.0.0.0", port=5000)