💨 CareBeat: Low-Latency Respiratory Telemetry

A Resource-Constrained, Non-Invasive Continuous Respiration Monitor

The Core Engineering Challenge

Continuous, high-fidelity physiological monitoring in many care settings is often gated by the cost and complexity of specialized, invasive hardware. This project engineers a low-cost, non-invasive alternative by leveraging commodity IoT hardware ($\text{nRF52840}$) to process and stream respiration data with a deterministic, low-latency pipeline.

The solution addresses the critical systems integration challenge of reliably uniting an asynchronous, event-driven Bluetooth Low Energy ($\text{BLE}$) data source with a synchronous, resource-intensive Graphical User Interface ($\text{GUI}$) on the host machine.

⚙️ Engineering Highlights & Systems Design

This project is defined by elegant solutions in resource-constrained embedded processing, multi-threaded host concurrency, and robust inter-system communication.

1. Asynchronous Client with Deterministic Data Pipeline

A fundamental challenge arises from coupling the $\text{asyncio}$ event loop (required for the $\text{bleak}$ BLE client) with $\text{Tkinter}$ (a synchronous, main-thread-bound GUI framework).

Inter-Thread Communications (ITC) Strategy: The $\text{asyncio}$ event loop is intentionally delegated to a dedicated $\text{threading.Thread}$. This guarantees a non-blocking BLE connection and isolates I/O from the GUI.

Thread-Safe Data Handoff: Processed data is passed back to the main GUI thread using the thread-safe $\text{tkinter.after()}$ method, ensuring all UI updates are executed safely on the main thread, thus maintaining a smooth, responsive, and crash-free user experience.

2. Embedded Real-Time Signal Processing

To minimize latency and optimize the BLE payload, all signal processing is performed on the $\text{nRF52840}$ device, offloading compute from the client and reducing transmission size.

Adaptive Filtering: The CircuitPython logic applies a Weighted Moving Average (WMA) filter to the raw $\text{LIS3DH}$ accelerometer data to smooth noise and isolate the primary respiratory waveform.

On-Device Feature Extraction: A peak detection algorithm with an adaptive, window-normalized threshold is implemented to convert the filtered signal directly into a clean Breaths Per Minute ($\text{BPM}$) integer before transmission, minimizing payload size.

3. Robust & Efficient BLE Transport

The project avoids the overhead of custom Generic Attribute Profile ($\text{GATT}$) Service definitions.

Nordic UART Service (NUS): We rely on the battle-tested, standard Nordic UART Service ($\text{6E400001-B5A3-F393-E0A9-E50E24DCCA9E}$) for simple, robust, and low-latency data streaming. This choice bypasses repeated $\text{GATT}$ Service Discovery on every connection, significantly improving connection establishment time and reliability.

4. Event-Driven Alerting

The host application performs real-time validation of the incoming telemetry. If the BPM falls outside a user-defined safe range, a distinct, threaded audio alert ($\text{sounddevice}$) is generated immediately, ensuring prompt intervention capability.

🏗️ Architecture & Tech Stack

This project is structured as a monorepo containing decoupled embedded firmware and host client components.

Data Flow Pipeline

$$\text{LIS3DH Accelerometer} \xrightarrow{\text{Raw Data}} \text{nRF52840 (CircuitPython)} \xrightarrow{\text{WMA Filter \& Peak Detect}}$$

$$\xrightarrow{\text{BPM Integer}} \text{BLE (NUS)} \xrightarrow{\text{asyncio/bleak Thread}} \text{Tkinter Main Thread} \xrightarrow{\text{Real-Time Plot}} \text{GUI}$$

Component

Technology

Purpose & Rationale

Concurrency

$\text{asyncio, threading}$

Isolated, non-blocking $\text{I/O}$ loop for high-availability BLE.

Data Client

$\text{bleak}$

Modern, asynchronous, cross-platform BLE client library.

GUI

$\text{customtkinter, matplotlib}$

High-fidelity, real-time visualization with a native aesthetic.

Embedded

$\text{Adafruit Circuit Playground Bluefruit}$

All-in-one MCU, BLE radio, and onboard $\text{LIS3DH}$ sensor.

Firmware

$\text{CircuitPython, Adafruit BLE}$

Simplifies peripheral access for rapid prototyping and deployment.

Alerting

$\text{sounddevice}$

Direct, low-latency audio playback for critical alerting.

📁 Repository Structure

A clean, minimal, and convention-following structure for immediate clarity.

.
├── .gitattributes
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt         # Host machine Python dependencies
├── desktop-app/             # Host Python application (GUI, plotting, alerting)
│   └── main.py
└── sensor-firmware/         # Embedded CircuitPython code
    ├── code.py              # Main sensor logic
    ├── settings.toml        # Device-side configuration
    └── lib/                 # CircuitPython dependencies


🚀 Setup & Execution

Prerequisites

Python 3.10+

Git

An Adafruit Circuit Playground Bluefruit (CPB)

1. Sensor Firmware Deployment

Clone Repository:

git clone [https://github.com/StillTyping1/The-CareBeat-Monitor.git](https://github.com/StillTyping1/The-CareBeat-Monitor.git)


Mount CPB: Plug in your board so the $\text{CIRCUITPY}$ drive mounts to your host machine.

Copy Firmware: Copy the entire contents of the $\text{sensor-firmware/}$ folder (including $\text{code.py}$, $\text{settings.toml}$, and $\text{lib/}$) to the $\text{CIRCUITPY}$ drive.

The sensor will automatically restart and begin broadcasting BLE data.

2. Desktop Client Execution

Navigate & Setup Virtual Environment:

cd The-CareBeat-Monitor

# Create & Activate venv
python3 -m venv venv
source venv/bin/activate # Linux / macOS
# python -m venv venv; .\venv\Scripts\activate # Windows


Install Dependencies:

pip install -r requirements.txt


Run Application:

python desktop-app/main.py
