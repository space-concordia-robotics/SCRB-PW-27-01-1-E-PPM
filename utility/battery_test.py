
import pyvisa
import csv
import time
from datetime import datetime

rm = pyvisa.ResourceManager()
print(rm.list_resources())

# Replace with your DL3021 USB resource
dl = rm.open_resource("USB0::0x1AB1::0x0E11::DL3A212100335::INSTR")
dl.timeout = 5000

print("Connected:", dl.query("*IDN?").strip())

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filename = f"battery_discharge_{timestamp}.csv"
sample_interval = 10  # seconds

capacity_Ah = 0.0
energy_Wh = 0.0

with open(filename, "w", newline="") as f:
    writer = csv.writer(f)

    writer.writerow([
        "Timestamp",
        "Elapsed_s",
        "Voltage_V",
        "Current_A",
        "Power_W",
        "Capacity_Ah",
        "Energy_Wh"
    ])

    start = time.monotonic()
    previous_time = start
    previous_current = None
    previous_power = None

    try:
        while True:
            voltage = float(dl.query(":MEAS:VOLT?"))
            current = float(dl.query(":MEAS:CURR?"))
            power = float(dl.query(":MEAS:POW?"))

            now = time.monotonic()
            elapsed = now - start
            dt = now - previous_time

            # Trapezoidal integration
            if previous_current is not None:
                capacity_Ah += (
                    (previous_current + current) / 2
                ) * dt / 3600

                energy_Wh += (
                    (previous_power + power) / 2
                ) * dt / 3600

            writer.writerow([
                datetime.now().isoformat(),
                round(elapsed, 2),
                voltage,
                current,
                power,
                capacity_Ah,
                energy_Wh
            ])

            f.flush()

            print(
                f"{elapsed:8.1f}s | "
                f"{voltage:7.3f} V | "
                f"{current:7.3f} A | "
                f"{capacity_Ah:.4f} Ah | "
                f"{energy_Wh:.4f} Wh"
            )

            previous_time = now
            previous_current = current
            previous_power = power

            time.sleep(max(0, sample_interval - (time.monotonic() - now)))

    except KeyboardInterrupt:
        print("\nLogging stopped.")

    finally:
        dl.close()
        rm.close()

print(f"Data saved to {filename}")
