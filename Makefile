zia: test
	python ble_wifi_truong.py
	python lux_miettinen.py
	python temp_hum_press_shrestha.py

test:
	nosetests *.py
