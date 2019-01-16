"""
Compute uptime in seconds

:param str uptime: Uptime (how long the script must run) in a human readable form, e.g., 10s
:return int: uptime
"""

import sys

# Get uptime
uptime = sys.argv[1]

# Get uptime unit
uptime_unit = uptime[len(uptime)-1]

# Get uptime value
uptime = uptime[:-1]

# Check if uptime value can be converted to a number
if not uptime.isdigit():
    print('Incorrect value of <uptime>: ' + '<' + uptime + '>' + ' cannot be converted to int!')
    exit(1)

# Compute uptime in seconds
if uptime_unit == 's':
    print(int(uptime))
elif uptime_unit == 'm':
    print(int(uptime)*60)
elif uptime_unit == 'h':
    print(int(uptime)*3600)
elif uptime_unit == 'd':
    print(int(uptime)*(3600*24))
else:
    print('Incorrect time unit of <uptime>: ' + '<' + uptime_unit + '>' + ' should be <s>, <m>, <h> or <d>!')
    exit(1)
