
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import time
import math
import queue
import urllib.request
import urllib.error

# ==========================================
# UNIVERSAL AXIS X
# TECHNOLOGY INTEGRATION PLATFORM
# ==========================================

CONFIG = {
    "name": "UNIVERSAL AXIS X",
    "width_ft": 1000,
    "length_ft": 1000,
    "color": "BLUE",
    "axis": "EARTH",
    "mqtt_host": "localhost",
    "mqtt_port": 1883,
    "mqtt_topic": "universal_axis/telemetry",
    "serial_port": "",
    "serial_baud": 115200,
    "api_url": "",
    "simulation": True,
    "actuators_enabled": False
}


class DeviceManager:
    """Optional external technology connections."""

    def __init__(self, events):
        self.events = events
        self.connections = {}

    def log(self, message):
        self.events.put(message)

    def connect_mqtt(self, host, port, topic):

        def worker():
            try:
                import paho.mqtt.client as mqtt

                client = mqtt.Client(
                    callback_api_version=
                    mqtt.CallbackAPIVersion.VERSION2
                )

                def on_connect(client, userdata, flags,
                               reason_code, properties):
                    if reason_code == 0:
                        client.subscribe(topic)
                        self.log("MQTT CONNECTED")
                    else:
                        self.log("MQTT CONNECTION FAILED")

                def on_message(client, userdata, message):
                    self.events.put(
                        "MQTT: " +
                        message.payload.decode(
                            "utf-8", errors="replace"
                        )[:500]
                    )

                client.on_connect = on_connect
                client.on_message = on_message
                client.connect(host, port, 60)
                client.loop_forever()

            except Exception as error:
                self.log(f"MQTT ERROR: {error}")

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    def connect_serial(self, port, baud):

        def worker():
            try:
                import serial

                device = serial.Serial(
                    port,
                    baud,
                    timeout=1
                )

                self.log("SERIAL CONNECTED")

                while True:
                    data = device.readline()

                    if data:
                        self.events.put(
                            "SERIAL: " +
                            data.decode(
                                "utf-8",
                                errors="replace"
                            ).strip()[:500]
                        )

            except Exception as error:
                self.log(f"SERIAL ERROR: {error}")

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    def connect_api(self, url):

        def worker():
            try:
                request = urllib.request.Request(
                    url,
                    headers={
                        "Accept": "application/json"
                    }
                )

                with urllib.request.urlopen(
                    request, timeout=5
                ) as response:

                    data = json.loads(
                        response.read().decode("utf-8")
                    )

                self.events.put(
                    "API: " + json.dumps(data)[:500]
                )

            except Exception as error:
                self.log(f"API ERROR: {error}")

        threading.Thread(
            target=worker,
            daemon=True
        ).start()


class PlatformSystem:

    def __init__(self):

        self.color = "BLUE"
        self.axis = "EARTH"
        self.energy = 0
        self.height = 0
        self.rotation = 0

        self.active = True
        self.simulation = True

        self.started = time.monotonic()

    def update(self):

        if not self.active:
            return

        elapsed = time.monotonic() - self.started

        self.energy = (
            50 + 50 * math.sin(elapsed)
        )

        self.rotation += 0.2

    def change_color(self, color):
        if color in ("BLUE", "YELLOW"):
            self.color = color

    def change_axis(self, axis):
        if axis in (
            "EARTH",
            "SPACE",
            "UNIVERSAL"
        ):
            self.axis = axis

    def emergency_stop(self):
        self.active = False


class UniversalAxisApp:

    def __init__(self, root):

        self.root = root
        self.root.title("UNIVERSAL AXIS X")
        self.root.geometry("1100x800")
        self.root.configure(bg="#061329")

        self.events = queue.Queue()

        self.devices = DeviceManager(self.events)
        self.platform = PlatformSystem()

        self.create_dashboard()

        self.root.after(100, self.refresh)
        self.root.after(100, self.read_events)

    # ======================================
    # DASHBOARD
    # ======================================

    def create_dashboard(self):

        tk.Label(
            self.root,
            text="UNIVERSAL AXIS X",
            bg="#061329",
            fg="#168BFF",
            font=("Arial", 28, "bold")
        ).pack(pady=15)

        tk.Label(
            self.root,
            text="1000 FT x 1000 FT TECHNOLOGY PLATFORM",
            bg="#061329",
            fg="white",
            font=("Arial", 12)
        ).pack()

        self.canvas = tk.Canvas(
            self.root,
            width=850,
            height=360,
            bg="#091D3C",
            highlightthickness=1,
            highlightbackground="#168BFF"
        )

        self.canvas.pack(pady=15)

        self.status = tk.Label(
            self.root,
            text="SYSTEM ONLINE - SIMULATION",
            bg="#061329",
            fg="#00E5FF",
            font=("Arial", 13, "bold")
        )

        self.status.pack()

        self.energy_label = tk.Label(
            self.root,
            text="ENERGY: 0%",
            bg="#061329",
            fg="white"
        )

        self.energy_label.pack(pady=5)

        controls = tk.Frame(
            self.root,
            bg="#061329"
        )

        controls.pack(pady=10)

        self.button(
            controls, "BLUE",
            lambda: self.platform.change_color("BLUE")
        )

        self.button(
            controls, "YELLOW",
            lambda: self.platform.change_color("YELLOW")
        )

        self.button(
            controls, "EARTH",
            lambda: self.platform.change_axis("EARTH")
        )

        self.button(
            controls, "SPACE",
            lambda: self.platform.change_axis("SPACE")
        )

        self.button(
            controls, "UNIVERSAL AXIS",
            lambda: self.platform.change_axis("UNIVERSAL")
        )

        self.button(
            controls, "STOP",
            self.stop
        )

        # Connection panel

        panel = tk.LabelFrame(
            self.root,
            text="TECHNOLOGY CONNECTIONS",
            bg="#061329",
            fg="#00BFFF",
            padx=10,
            pady=10
        )

        panel.pack(fill="x", padx=35, pady=10)

        self.mqtt_host = self.entry(
            panel, "MQTT host", "localhost"
        )

        self.mqtt_topic = self.entry(
            panel, "MQTT topic",
            "universal_axis/telemetry"
        )

        self.serial_port = self.entry(
            panel, "Serial port", ""
        )

        self.api_url = self.entry(
            panel, "Telemetry API URL", ""
        )

        self.button(
            panel,
            "CONNECT MQTT",
            self.mqtt_connect
        )

        self.button(
            panel,
            "CONNECT SERIAL",
            self.serial_connect
        )

        self.button(
            panel,
            "READ API",
            self.api_connect
        )

        # Event log

        self.log = tk.Text(
            self.root,
            height=7,
            bg="#020914",
            fg="#00E5FF",
            font=("Consolas", 10)
        )

        self.log.pack(
            fill="both",
            expand=True,
            padx=35,
            pady=10
        )

    def button(self, parent, label, action):

        tk.Button(
            parent,
            text=label,
            command=action,
            bg="#123B70",
            fg="white",
            activebackground="#168BFF",
            activeforeground="white",
            relief="flat",
            padx=10,
            pady=8
        ).pack(side="left", padx=4, pady=4)

    def entry(self, parent, label, default):

        frame = tk.Frame(
            parent,
            bg="#061329"
        )

        frame.pack(side="left", padx=5)

        tk.Label(
            frame,
            text=label,
            bg="#061329",
            fg="white"
        ).pack()

        field = tk.Entry(frame, width=18)
        field.insert(0, default)
        field.pack()

        return field

    # ======================================
    # CONNECTION CONTROLS
    # ======================================

    def mqtt_connect(self):

        self.devices.connect_mqtt(
            self.mqtt_host.get(),
            1883,
            self.mqtt_topic.get()
        )

    def serial_connect(self):

        port = self.serial_port.get().strip()

        if not port:
            messagebox.showwarning(
                "Serial",
                "Enter a serial port first."
            )
            return

        self.devices.connect_serial(
            port, 115200
        )

    def api_connect(self):

        url = self.api_url.get().strip()

        if not url.startswith("https://"):
            messagebox.showwarning(
                "API",
                "Use a trusted HTTPS telemetry endpoint."
            )
            return

        self.devices.connect_api(url)

    # ======================================
    # PLATFORM VISUALIZATION
    # ======================================

    def draw(self):

        self.canvas.delete("all")

        color = (
            "#087BFF"
            if self.platform.color == "BLUE"
            else "#FFD500"
        )

        x = 425
        y = 180

        # Platform surface

        self.canvas.create_polygon(
            x - 230, y - 65,
            x + 230, y - 65,
            x + 230, y + 65,
            x - 230, y + 65,
            fill="#102D59",
            outline=color,
            width=4
        )

        # Simulated energy flow

        for i in range(12):

            px = (
                x - 210 +
                (i * 39 + self.platform.rotation * 2)
                % 420
            )

            py = y + math.sin(
                i + self.platform.rotation / 20
            ) * 35

            self.canvas.create_oval(
                px - 4, py - 4,
                px + 4, py + 4,
                fill=color,
                outline=""
            )

        # Coordinate axes

        self.canvas.create_line(
            x, 330, x, 255,
            fill="#00FF99", width=3
        )

        self.canvas.create_line(
            x, 330, x + 150, 330,
            fill="#FF5555", width=3
        )

        self.canvas.create_line(
            x, 330, x - 90, 355,
            fill="#5599FF", width=3
        )

        self.canvas.create_text(
            x, 25,
            text="1000 FT x 1000 FT",
            fill="white",
            font=("Arial", 15, "bold")
        )

        self.canvas.create_text(
            425, 225,
            text="SIMULATED LEVITATION",
            fill=color,
            font=("Arial", 12, "bold")
        )

    # ======================================
    # EVENT LOG
    # ======================================

    def read_events(self):

        while not self.events.empty():

            event = self.events.get_nowait()

            self.log.insert(
                "end",
                str(event) + "\n"
            )

            self.log.see("end")

        self.root.after(200, self.read_events)

    # ======================================
    # LIVE REFRESH
    # ======================================

    def refresh(self):

        if not self.platform.active:
            return

        self.platform.update()
        self.draw()

        self.status.config(
            text=(
                f"ONLINE | COLOR: {self.platform.color}"
                f" | AXIS: {self.platform.axis}"
                " | OUTPUTS DISABLED"
            )
        )

        self.energy_label.config(
            text=(
                f"SIMULATED ENERGY FLOW: "
                f"{self.platform.energy:.1f}%"
            )
        )

        self.root.after(40, self.refresh)

    # ======================================
    # SHUTDOWN
    # ======================================

    def stop(self):

        self.platform.emergency_stop()

        self.status.config(
            text="SIMULATION HALTED"
        )

        self.canvas.delete("all")

        self.log.insert(
            "end",
            "SYSTEM STOP REQUESTED\n"
        )


# ==========================================
# START
# ==========================================

if __name__ == "__main__":

    root = tk.Tk()

    app = UniversalAxisApp(root)

    root.mainloop()
