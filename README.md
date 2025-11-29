CareBeat Monitor

💡 Core Concept

Continuous respiration monitoring in many care settings requires expensive, complex, and invasive hardware. This project addresses that problem with a low-cost, non-invasive IoT alternative.

The onboard LIS3DH accelerometer on a Circuit Playground Bluefruit microcontroller detects chest movements. The raw data is processed on-device, and the resulting respiration rate is streamed over Bluetooth Low Energy (BLE). A Python desktop client, built with asyncio, threading, and bleak, subscribes to this data stream for real-time visualization, trend analysis, and immediate audio alerting.

🚀 Engineering Highlights

Asynchronous & Thread-Safe Client: Solves the core challenge of integrating asyncio (for bleak) with Tkinter (a synchronous framework). The asyncio event loop is run in a separate threading.Thread, guaranteeing a non-blocking connection. Data is then passed back to the main UI thread via the thread-safe tkinter.after() method, ensuring a smooth, responsive, and crash-free UI.

Embedded Signal Processing: The sensor-side CircuitPython logic performs real-time signal filtering using a weighted moving average and peak detection with an adaptive threshold. This converts raw accelerometer noise into a clean BPM integer on the device, minimizing payload size and offloading all compute from the client.

Efficient BLE Transport: Leverages the standard Nordic UART Service (NUS) for robust, low-latency data streaming (6E400001-...). This avoids the overhead of a custom protocol and relies on a battle-tested, standard implementation.

Real-Time Alerting: The desktop app parses the incoming data stream to trigger distinct, threaded audio alerts via sounddevice if the respiration rate falls outside a user-defined safe range.

🔬 Architecture & Tech Stack

This project is a monorepo containing two main components:

sensor-firmware/: Embedded CircuitPython code for the microcontroller.

desktop-app/: Python client application for the host machine.

Data Flow:
[LIS3DH (onboard)] → [Circuit Playground Bluefruit (nRF52840)] → [CircuitPython: Adaptive Filter] → [BLE (Nordic UART Service)] → [Client Thread: Bleak (asyncio)] → [Tkinter Main Thread: self.after] → [GUI: Matplotlib/Tkinter]

Component

Technology

Purpose

Concurrency

asyncio, threading

Manages BLE loop in a separate thread

Data Client

bleak

Asynchronous BLE data ingestion

GUI

customtkinter

Desktop user interface

Plotting

matplotlib, numpy

Real-time data visualization

Audio

sounddevice

Audible alert generation

Embedded System

Adafruit Circuit Playground Bluefruit

All-in-one MCU, BLE radio, & onboard LIS3DH

Firmware

CircuitPython, Adafruit BLE

Sensor-side logic & BLE service

📂 File Structure

.
├── .gitattributes     # Enforces consistent line endings (LF) for all OS
├── .gitignore         # Ignores junk files, logs, and venv
├── LICENSE            # MIT License
├── README.md          # You are here
├── requirements.txt   # Desktop app Python dependencies
├── desktop-app/       # Desktop Python application (GUI, plotting)
│   └── main.py
└── sensor-firmware/
    ├── code.py        # Main CircuitPython sensor logic
    ├── settings.toml  # Sensor settings
    └── lib/           # CircuitPython libraries (dependencies)


🏁 Setup & Execution

Prerequisites

Python 3.10+

Git

An Adafruit Circuit Playground Bluefruit

1. Sensor Firmware Setup

Clone this repository: git clone https://github.com/StillTyping1/The-CareBeat-Monitor.git

Plug in your board so it appears as a CIRCUITPY drive.

Copy the entire contents of the sensor-firmware/ folder (including code.py, settings.toml, and the lib folder) to the CIRCUITPY drive.

The sensor will restart and begin broadcasting BLE data.

2. Desktop Client Setup

Navigate to the project root: cd The-CareBeat-Monitor

Create and activate a virtual environment (Required):

# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
.\venv\Scripts\activate


Install all dependencies:

pip install -r requirements.txt


Run the application:

python desktop-app/main.py
