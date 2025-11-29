# Import necessary libraries
import re  # For regular expression matching
import customtkinter as ctk  # CustomTkinter for modern GUI
import asyncio  # For asynchronous BLE communication
from bleak import BleakClient  # For BLE client connection
from threading import Thread  # For threading operations
import matplotlib.pyplot as plt  # For plotting BPM graph
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # For embedding matplotlib in Tkinter
from collections import deque  # For efficient fixed-length data storage (sliding window)
import numpy as np  # For generating tone waveforms
import sounddevice as sd  # For playing sound alerts
import time  # For delays
import threading  # For creating and managing threads

# Bluetooth device info — replace with actual MAC address and UUIDs
BLUEFRUIT_DEVICE_ADDRESS = "D3:3F:CB:17:3C:EE"  # Adafruit Bluefruit MAC address
SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"  # BLE UART service UUID
CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"  # BLE characteristic UUID for receiving data

def generate_tone(frequency=1000, duration=0.5, sample_rate=44100):
    """Generate and play a tone with given frequency and duration."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = 0.5 * np.sin(2 * np.pi * frequency * t)  # Sine wave for beep
    sd.play(wave, samplerate=sample_rate)  # Play sound
    sd.wait()  # Wait until sound finishes

def low_bpm_alert(self):
    """Continuously play a warning beep when BPM is critically low."""
    def play_alert():
        while self.low_bpm_alert_active and self.monitoring:
            generate_tone(frequency=800, duration=0.3)  # Lower frequency beep
            time.sleep(2)  # Delay between beeps

    alert_thread = threading.Thread(target=play_alert, daemon=True)
    alert_thread.start()

def high_bpm_alert(self):
    """Continuously play a warning beep when BPM is critically high."""
    def play_alert():
        while self.high_bpm_alert_active and self.monitoring:
            generate_tone(frequency=1200, duration=0.5)  # Higher frequency beep
            time.sleep(1)  # Faster alert rate

    alert_thread = threading.Thread(target=play_alert, daemon=True)
    alert_thread.start()

# Main UI class for the home page
class HomePage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.ble_client = None
        self.monitoring = False  # Flag to check if monitoring is active
        self.low_bpm_alert_active = False
        self.high_bpm_alert_active = False
        self.low_bpm_started = False  # Prevents retriggering
        self.connected = False  # Connection state

        # UI Elements
        self.label_title = ctk.CTkLabel(self, text="CareBeat Monitor", font=("Arial", 18, "bold"))
        self.label_title.pack(pady=10)

        self.bpm_label = ctk.CTkLabel(self, text="BPM: --", font=("Arial", 16))
        self.bpm_label.pack(pady=10)

        self.graph_frame = ctk.CTkFrame(self, width=400, height=200)
        self.graph_frame.pack(pady=10)

        # Set up matplotlib chart
        self.fig, self.ax = plt.subplots(figsize=(5, 2))
        self.bpm_data = deque([0] * 30, maxlen=30)  # Store latest 30 BPM values
        self.line, = self.ax.plot(self.bpm_data, "g-", linewidth=2)
        self.ax.set_ylim(0, 150)
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("BPM")
        self.ax.set_title("Heart Rate Graph")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack()

        self.status_label = ctk.CTkLabel(self, text="Status: Not Connected", font=("Arial", 12))
        self.status_label.pack(pady=10)

        self.alert_label = ctk.CTkLabel(self, text="", font=("Arial", 14, "bold"), text_color="red")
        self.alert_label.pack(pady=5)

        self.start_button = ctk.CTkButton(self, text="Start Monitoring", command=self.start_monitoring)
        self.start_button.pack(pady=5)

        self.stop_button = ctk.CTkButton(self, text="Stop Monitoring", command=self.stop_monitoring)
        self.stop_button.pack(pady=5)

    def update_bpm(self, bpm):
        """Update UI with latest BPM reading and graph."""
        if not self.monitoring:
            return

        self.bpm_label.configure(text=f"BPM: {bpm}")
        try:
            bpm_value = float(bpm)
            self.bpm_data.append(bpm_value)
            self.line.set_ydata(self.bpm_data)
            self.line.set_xdata(range(len(self.bpm_data)))
            self.ax.set_ylim(0, 150)
            self.canvas.draw_idle()

            # Alert thresholds
            if bpm_value < 30:
                self.set_alert("⚠ LOW BPM ALERT: INFANT MEDICAL ATTENTION REQUIRED!", low_bpm_alert, "low")
            elif bpm_value > 50:
                self.set_alert("⚠ HIGH BPM ALERT: INFANT MEDICAL ATTENTION REQUIRED!", high_bpm_alert, "high")
            else:
                self.clear_alert()
        except ValueError:
            pass  # Ignore non-numeric input

    def set_alert(self, message, alert_function, alert_type):
        """Trigger visual and audio alerts based on BPM type."""
        if not self.monitoring:
            return
        if alert_type == "low" and not self.low_bpm_alert_active:
            self.low_bpm_alert_active = True
            self.alert_label.configure(text=message, text_color="red")
            alert_function(self)
        elif alert_type == "high" and not self.high_bpm_alert_active:
            self.high_bpm_alert_active = True
            self.alert_label.configure(text=message, text_color="red")
            alert_function(self)
        self.flash_alert()

    def flash_alert(self):
        """Blink the alert label to catch user’s attention."""
        if not self.monitoring:
            return
        if self.low_bpm_alert_active or self.high_bpm_alert_active:
            current_color = self.alert_label.cget("text_color")
            new_color = "black" if current_color == "red" else "red"
            self.alert_label.configure(text_color=new_color)
            self.after(500, self.flash_alert)

    def clear_alert(self):
        """Disable all active alerts and clear the label."""
        self.low_bpm_alert_active = False
        self.high_bpm_alert_active = False
        self.alert_label.configure(text="")

    def update_status(self, status):
        """Update the connection status label."""
        self.status_label.configure(text=f"Status: {status}")

    async def connect_ble(self):
        """Establish BLE connection and begin notification."""
        try:
            self.ble_client = BleakClient(BLUEFRUIT_DEVICE_ADDRESS)
            await self.ble_client.connect()
            self.connected = True
            self.update_status("Connected")
            await self.ble_client.start_notify(CHAR_UUID, self.notification_handler)
        except Exception as e:
            self.update_status(f"Error: {e}")

    async def notification_handler(self, sender, data):
        """Handle incoming BLE data packets from the device."""
        if not self.monitoring:
            return
        try:
            decoded_data = data.decode("utf-8").strip()  # Decode UTF-8 byte string
            bpm_match = re.search(r'\d+(\.\d+)?', decoded_data)  # Extract BPM number
            bpm_value = bpm_match.group(0) if bpm_match else "--"
            self.after(100, self.update_bpm, bpm_value)
        except Exception as e:
            print(f"Notification Handling Error: {e}")

    async def read_bpm(self):
        """Keep checking BLE connection and handle disconnections."""
        try:
            while self.monitoring:
                if self.ble_client and await self.ble_client.is_connected():
                    if not self.connected:
                        self.connected = True
                        self.update_status("Connected")
                    await asyncio.sleep(1)
                else:
                    if self.connected:
                        self.connected = False
                        self.update_status("Disconnected")
                    break
        except Exception as e:
            self.update_status(f"Error: {e}")

    def start_monitoring(self):
        """Trigger BLE communication and UI updates for monitoring."""
        if not self.monitoring:
            self.monitoring = True
            if not self.connected:
                self.update_status("Connecting...")
                self.low_bpm_started = False
                Thread(target=self.run_ble, daemon=True).start()
            else:
                self.update_status("Connected")

    def stop_monitoring(self):
        """Stop monitoring sensor without disconnecting."""
        if self.monitoring:
            self.monitoring = False
            self.clear_alert()
            self.update_status("Stopped")

    def run_ble(self):
        """Start the asyncio event loop for BLE communication."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.connect_ble())
        loop.run_until_complete(self.read_bpm())
        loop.run_forever()

# Start the application
if __name__ == "__main__":
    app = ctk.CTk()
    app.title("CareBeat Desktop App")
    app.geometry("700x450")
    HomePage(app, app).pack(fill="both", expand=True)
    app.mainloop()
