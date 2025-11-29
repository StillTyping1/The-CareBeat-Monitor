import time  # Used for tracking and controlling time-based operations
import array  # Provides array data structures for efficient numeric storage
import math  # Provides mathematical functions
import board  # Accesses board-specific hardware pin mappings
import busio  # Enables communication with devices via I2C, SPI, or UART
import adafruit_lis3dh  # Library for the LIS3DH accelerometer
import neopixel  # Controls the onboard NeoPixel LEDs
import adafruit_ble  # Main BLE (Bluetooth Low Energy) support library
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement  # Allows BLE advertising for services
from adafruit_ble.services.nordic import UARTService  # Enables sending data over BLE using UART
from adafruit_ble import BLERadio  # Handles Bluetooth radio functions
import digitalio  # Used to control GPIO pins

# Setup Bluetooth
ble = BLERadio()  # Initialize the BLE radio
uart = UARTService()  # Set up a UART BLE service
advertisement = ProvideServicesAdvertisement(uart)  # Create a BLE advertisement for the UART service

print("Waiting for Bluetooth connection...")
ble.start_advertising(advertisement)  # Begin advertising for a BLE connection
while not ble.connected:  # Wait until a Bluetooth connection is made
    pass
print("Bluetooth connected!")  # Notify when connected

# Setup I2C communication for the LIS3DH accelerometer
i2c = busio.I2C(board.ACCELEROMETER_SCL, board.ACCELEROMETER_SDA)  # Set up I2C using accelerometer pins
accelerometer = adafruit_lis3dh.LIS3DH_I2C(i2c, address=0x19)  # Connect to the LIS3DH accelerometer at address 0x19

# Setup NeoPixels
pixels = neopixel.NeoPixel(board.NEOPIXEL, 10, brightness=0.3, auto_write=True)  # Initialize 10 NeoPixels with brightness and auto update

# Constants
THRESHOLD = 0.06  # Sensitivity threshold to detect a breath
NORMAL_BPM_RANGE = (30, 50)  # Expected normal range for infant breathing rate
DEBOUNCE_TIME = 0.8  # Minimum time between breaths to avoid false detection
ROLLING_WINDOW = 6  # Number of recent breaths to use for smoothing
BPM_DECAY_RATE = 5  # Rate to decrease BPM if no breath is detected
NO_BREATH_TIMEOUT = 2  # Seconds to wait before reducing BPM when no breath is detected
NO_BREATH_ALERT_TIME = 5  # Time without breath before flashing red light
ALERT_DURATION = 5  # Time before beeping starts (not used here but defined)

# Variables
breath_times = []  # Stores timestamps of recent breaths
previous_z_readings = []  # Stores previous Z-axis values for smoothing
last_breath_time = None  # Timestamp of last detected breath
previous_bpm = 0  # Stores last calculated BPM
alert_active = False  # Tracks if alert mode is active
alert_start_time = None  # Tracks when alert started (not used here)

print("Real-Time Infant Respiration Monitoring Active...")
previous_x, previous_y, previous_z = accelerometer.acceleration  # Get initial accelerometer readings

def flash_red_light():
    """Flash the red light in sync with a beep (not implemented here)."""
    if int(time.monotonic() * 2) % 2 == 0:  # Alternate every 0.5s
        pixels.fill((255, 0, 0))  # Turn red light on
    else:
        pixels.fill((0, 0, 0))  # Turn light off

while True:
    current_time = time.monotonic()  # Get current time in seconds
    breath_detected = False  # Flag to track breath detection

    try:
        current_x, current_y, current_z = accelerometer.acceleration  # Read current accelerometer data
    except RuntimeError:
        print("Lost connection to accelerometer!")  # Print error if sensor fails
        continue  # Skip this loop iteration

    # Smooth Z-axis signal using weighted moving average
    smoothed_z = (
        0.1 * current_z +
        0.2 * previous_z_readings[-1] if previous_z_readings else current_z  # Use previous value if available
    )

    previous_z_readings.append(smoothed_z)  # Store the smoothed value
    if len(previous_z_readings) > ROLLING_WINDOW:  # Limit stored values
        previous_z_readings.pop(0)  # Remove oldest value

    # Calculate how much Z-axis values are changing to detect movement
    if len(previous_z_readings) >= 2:
        z_deltas = [abs(previous_z_readings[i] - previous_z_readings[i - 1]) for i in range(1, len(previous_z_readings))]  # Calculate deltas
        avg_delta = sum(z_deltas) / len(z_deltas)  # Average of those deltas
        adaptive_threshold = max(THRESHOLD * 0.5, avg_delta * 0.8)  # Adjust threshold dynamically
    else:
        adaptive_threshold = THRESHOLD  # Use default if not enough data

    # Check if current Z change exceeds adaptive threshold
    if abs(smoothed_z - previous_z) > adaptive_threshold:
        if not breath_times or (current_time - breath_times[-1]) > DEBOUNCE_TIME:  # Debounce logic
            breath_times.append(current_time)  # Log breath timestamp
            last_breath_time = current_time  # Update last breath time
            breath_detected = True  # Mark breath detected
            print(f"Breath detected! ΔZ: {abs(smoothed_z - previous_z):.3f}, Threshold: {adaptive_threshold:.3f}")
            alert_active = False  # Reset alert

    previous_x, previous_y, previous_z = current_x, current_y, smoothed_z  # Update previous readings
    breath_times = breath_times[-ROLLING_WINDOW:]  # Keep only recent breath times

    # Calculate BPM from recent breath intervals
    if len(breath_times) > 1:
        time_differences = [breath_times[i] - breath_times[i - 1] for i in range(1, len(breath_times))]  # Intervals between breaths
        avg_breath_time = sum(time_differences) / len(time_differences)  # Average time per breath
        target_bpm = 60 / avg_breath_time  # Convert to BPM
    else:
        target_bpm = 0  # Not enough data to calculate BPM

    # If no breath for a while, gradually reduce BPM
    if last_breath_time and (current_time - last_breath_time) > NO_BREATH_TIMEOUT:
        target_bpm -= BPM_DECAY_RATE * (current_time - last_breath_time)  # Decrease BPM
        target_bpm = max(0, target_bpm)  # Don't go below 0

    previous_bpm += (target_bpm - previous_bpm) * 0.1  # Smooth transition in BPM value
    print(f"{previous_bpm:.1f}")  # Print the smoothed BPM

    if ble.connected:
        try:
            uart.write(f"{previous_bpm:.1f}\n")  # Send BPM over Bluetooth
        except Exception as e:
            print(f"BLE send error: {e}")  # Print error if transmission fails
    else:
        print("Disconnected! Waiting for Bluetooth reconnection...")
        ble.start_advertising(advertisement)  # Restart BLE advertising if disconnected

    # LED display based on BPM range
    if NORMAL_BPM_RANGE[0] <= previous_bpm <= NORMAL_BPM_RANGE[1]:
        pixels.fill((0, 255, 0))  # Green light for normal BPM
    else:
        pixels.fill((255, 0, 0))  # Red light for abnormal BPM
        flash_red_light()  # Flash red light

    # Flash red if no breath detected for a long time
    if last_breath_time and (current_time - last_breath_time) > NO_BREATH_ALERT_TIME:
        print(f"No breath detected for {current_time - last_breath_time:.2f} seconds.")
        flash_red_light()  # Flash red light in alert

    time.sleep(0.1)  # Small delay before next reading
