"""Post process collected WiFi / BT frames to anonymize MAC addresses.

MACs are replaced with a number which is identical for identical MACs in
different recordings.
"""
from glob import glob

# WiFi state variables
WIFI_MAC_MAP = {}
WIFI_MAC_CTR = 0
# BLE state variables
BLE_MAC_MAP = {}
BLE_MAC_CTR = 0

# Blind WiFi files
for wi_file in glob("Sensor-*/wifi/wifi.txt"):
    with open(wi_file, 'r') as fo, open(wi_file + ".blinded", "w") as fo2:
        for line in fo:
            # Parse out information from the line
            try:
                mac, rssi, date = line.strip().split(" ")
            except ValueError:
                fo2.write(line)
                continue 
            # Check if we have seen the MAC before - if not, assign unique ID
            if mac not in WIFI_MAC_MAP:
                WIFI_MAC_MAP[mac] = WIFI_MAC_CTR
                WIFI_MAC_CTR += 1
            # Retrieve unique ID of MAC
            mac_blinded = str(WIFI_MAC_MAP[mac])
            # Write blinded line to file
            fo2.write(mac_blinded + " " + rssi + " " + date + "\n")

# Blind BLE files
for ble_file in glob("Sensor-*/ble/ble.txt"):
    with open(ble_file, 'r') as fo, open(ble_file + ".blinded", "w") as fo2:
        for line in fo:
            # Parse out information from the line
            try:
                mac, rssi, date = line.strip().split(" ")
            except ValueError:
                fo2.write(line)
                continue
            # Check if we have seen the MAC before - if not, assign unique ID
            if mac not in BLE_MAC_MAP:
                BLE_MAC_MAP[mac] = BLE_MAC_CTR
                BLE_MAC_CTR += 1
            # Retrieve unique ID of MAC
            mac_blinded = str(BLE_MAC_MAP[mac])
            # Write blinded line to file
            fo2.write(mac_blinded + " " + rssi + " " + date + "\n")
