"""Post process luminosity values to remove outliers

There is a bug with the SensorTag firmware that leads to the Luminosity sensor
sometimes reading values of 13.6 where none should exist. This script removes
these values from the dataset and replaces them with the previous value.
This is acceptable because luminosity usually does not change very rapidly, and
values are collected every 100 ms, making it very unlikely that this will cause
any issues with the accuracy of the data.
"""
from glob import glob

# Blind WiFi files
for lux_file in glob("Sensor-*/sensors/luxData*"):
    print(lux_file)
    values = []
    with open(lux_file, 'r') as fo:
        for line in fo:
            val, time = line.strip().split(" ")
            if val == "13.6":
                prev = values[-1]
                val = float(val)
                oldval = float(prev.split(" ")[0])
                if abs(oldval - val) > 1:
                    values.append(prev)
                else:
                    values.append(line)
            else:
                values.append(line)
    with open(lux_file + ".clean", "w") as fo:
        for val in values:
            fo.write(val)
