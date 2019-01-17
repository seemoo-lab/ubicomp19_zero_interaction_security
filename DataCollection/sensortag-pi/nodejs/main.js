/*
The code is used to fetch sensor data from the SensorTag via Bluetooth and store it in a file on the Raspberry Pi
*/

var util = require('util');
var async = require('async');
var SensorTag = require('./index');

// Easy to include/exclude sensors
var TMP_FLAG = false; // for now always false because a dedicated tmp sensor is disabled on the SensorTag itself
var LUX_FLAG = true;
var HUM_FLAG = true;
var BAR_FLAG = true;
var MAG_FLAG = true;
var GYR_FLAG = true;
var ACC_FLAG = true;

var AUD_FLAG = false;

// Timeout in milliseconds
var connectionTimeout = 5000;

// Timeout flag
var TIMEOUT_FLAG = true;

// Get timezone offest in milliseconds
var timezoneOffset = (new Date()).getTimezoneOffset() * 60000; 

// Files to store sensor data
var fs = require('fs');

// Path to sensor data
var path = '/home/pi/data/sensors/';

var tmpFileName = path + 'tmpData';
var luxFileName = path + 'luxData';
var humFileName = path + 'humData';
var barFileName = path + 'barData';
var magFileName = path + 'magData';
var gyrFileName = path + 'gyrData';
var accFileName = path + 'accData';

// SensorTag address and measurement timeout (provided as command line args) 
var tagAddress = ''
var measurementTimeout = ''; 

/********** MAIN BODY ************/

// Get command line arguments
const args = process.argv;

// Parse command line arguments
function parseCmdLineArgs() {
	
  // Check command line arguments
  if(args.length !=  4) {	  
    console.log('Usage: sudo node main.js <SensorTag_MAC_address> <uptime>' + '\n' +
	'<SensorTag_MAC_address> - no spaces and special characters: e.g. <ffffffffffff>' + '\n' + 
	'<uptime> - in sec, min, hours or days: e.g. <30s>, <10m>, <24h>, <5d>');
    process.exit(0);
  }
  
  // Regex to filter special characters
  var regexAddress = /^[a-z0-9]+$/;
  
  // Regex to filter anything apart from digits
  var regexUptime = /^[0-9]+$/;
  
  // To lower case
  tagAddress = args[2].toLowerCase();
  
  // Check if the provided MAC address has proper lenght
  if(tagAddress.length != 12) {
	console.log('Provided <SensorTag_MAC_address> has invalid length!');
	process.exit(0);
  } 
  
  // Check if the provided MAC address has no special characters
  if(regexAddress.test(tagAddress) != true) {
    console.log('Provided <SensorTag_MAC_address> must NOT contain special characters!');
	process.exit(0);  
  }
  
  // Split uptime into a time unit and actual value
  var uptime = args[3];
  var uptimeUnit = uptime.slice(-1);
  uptime = uptime.slice(0, -1);
  
  // Check if uptime contains only digits so it can be converted
  if(regexUptime.test(uptime) != true) {
	console.log('Incorrect value of <uptime>: ' + '<' + uptime + '>' + ' cannot be converted to int!');
	process.exit(0);
  }
  
  // Convert uptime to seconds
  if(uptimeUnit == 's') {
    uptime = parseInt(uptime);
  } else if(uptimeUnit == 'm') {
	uptime = parseInt(uptime)*60;
  } else if(uptimeUnit == 'h') {
	uptime = parseInt(uptime)*3600;
  } else if(uptimeUnit == 'd') {
	uptime = parseInt(uptime)*(3600*24); 
  } else {
	console.log('Incorrect time unit of <uptime>: ' + '<' + uptimeUnit + '>' + ' should be <s>, <m>, <h> or <d>!');
	process.exit(0);
  }
  
  //console.log('converted time: ' + uptime);
  
  // Measurement timeout in milliseconds
  measurementTimeout = uptime*1000;
};

// Calling function to parse arguments
parseCmdLineArgs();

// Main sensorTag routine
SensorTag.discoverByUuid(tagAddress, function(sensorTag){
  console.log('discovered: ' + sensorTag.uuid);
  
  // On disconnect listener
  sensorTag.on('disconnect', function() {
	console.log('disconnected!');
    process.exit(0);
  });
  
  // Async series
  async.series([
    // Connect to the SensorTag
	function(callback) {
      console.log('connectAndSetUp');
      sensorTag.connectAndSetUp(callback);
    },
	
	// We are connected -> Disable timeout flag
	function(callback) {
      TIMEOUT_FLAG = false;
	  callback();
	},
	
	// Enable sensors 
	function(callback) {
	  if(TMP_FLAG) {
	    console.log('enableIrTemperature');
        sensorTag.enableIrTemperature(callback);
	  } else {
	    callback();
	  }
	},
	function(callback) {
	  if(TMP_FLAG) {
	    setTimeout(callback, 2000);
	  } else {
	    callback();
	  }
	},

	function(callback) {
	  if(LUX_FLAG) {
	    console.log('enableLuxometer');
	    sensorTag.enableLuxometer(callback);
	  } else {
	    callback();
	  }
	},
	  function(callback) {
	  if(LUX_FLAG) {
	    setTimeout(callback, 2000);
	  } else {
	    callback();
	  }
    },
	  
	function(callback) {
	  if(HUM_FLAG) {
	    console.log('enableHumidity');
	    sensorTag.enableHumidity(callback);
	  } else {
	    callback();
	  }
	},
	function(callback) {
	  if(HUM_FLAG) {
	    setTimeout(callback, 2000);
	  } else {
	    callback();
	  }
	},
	  
    function(callback) {
	  if(BAR_FLAG) {
	    console.log('enableBarometricPressure');
	    sensorTag.enableBarometricPressure(callback);
	  } else {
	    callback();
	  }
    },
    function(callback) {
	  if(BAR_FLAG) {
	    setTimeout(callback, 2000);
	  } else {
	    callback();
	  }
    },
	  
    function(callback) {
	  if(MAG_FLAG) {
	    console.log('enableMagnetometer');
	    sensorTag.enableMagnetometer(callback);
	  } else {
	    callback();
	  }
    },
    function(callback) {
	  if(MAG_FLAG) {
	    setTimeout(callback, 2000);
	  } else {
	    callback();
	  }  
    },
	  
    function(callback) {
	  if(GYR_FLAG) {
	    console.log('enableGyroscope');
	    sensorTag.enableGyroscope(callback);
	  } else {
	    callback();
	  }
    },
    function(callback) {
	  if(GYR_FLAG) {
	    setTimeout(callback, 2000);
	  } else {
	    callback();
	  }
    },
	  
    function(callback) {
	if(ACC_FLAG) {
	  console.log('enableAccelerometer');
	  sensorTag.enableAccelerometer(callback);
	} else {
	  callback();
	}
    },
    function(callback) {
	  if(ACC_FLAG) {
	    setTimeout(callback, 2000);
	  } else {
	    callback();
	  }
    },
	
    // Enable audio notifications
	function(callback) {
	  if(AUD_FLAG) {
	    console.log('notifyAudioConfig');
	    sensorTag.notifyAudioConfig(callback);
	  } else {
	    callback();
	  }
	},
    function(callback) {
	  if(AUD_FLAG) {
	    setTimeout(callback, 1000);
	  } else {
	    callback();
	  }
    },

	function(callback) {
	  if(AUD_FLAG) {
	    console.log('notifyAudioStream');
	    sensorTag.notifyAudioStream(callback);
	  } else {
	    callback();
	  }
	},
	function(callback) {
	  if(AUD_FLAG) {
	    setTimeout(callback, 1000);
	  } else {
	    callback();
	  }
    },
	
	// Fetch sensor data (set a notification period, enable notifications)
	function(callback) {
	  if(TMP_FLAG) {
	    sensorTag.on('irTemperatureChange', function(objectTemperature, ambientTemperature) {
		  var timestamp = (new Date(Date.now() - timezoneOffset)).toISOString().slice(0,-1);
		  var tempValue = ambientTemperature.toFixed(1).toString() + ' ' + timestamp + '\r\n';
		  fs.appendFile(tmpFileName, tempValue, function (err) {
			if(err) throw err;
		  });
	    });
	    sensorTag.setIrTemperaturePeriod(300, function(error) { // Min period is 300 ms
		  console.log('notifyIrTemperature');
		  sensorTag.notifyIrTemperature();
	    });	
	  }
	  
	  if(LUX_FLAG) {
	    sensorTag.on('luxometerChange', function(lux) {
		  var timestamp = (new Date(Date.now() - timezoneOffset)).toISOString().slice(0,-1);
		  var luxValue = lux.toFixed(1).toString() + ' ' + timestamp + '\r\n';
		  fs.appendFile(luxFileName, luxValue, function (err) {
			if(err) throw err;
		  });
		});
	    sensorTag.setLuxometerPeriod(100, function(error) { // Min period is 100 ms
		  console.log('notifyLuxometer');
		  sensorTag.notifyLuxometer();
	    });
	  }
	
	  if(HUM_FLAG) {
	    sensorTag.on('humidityChange', function(temperature, humidity) {
		  var timestamp = (new Date(Date.now() - timezoneOffset)).toISOString().slice(0,-1);
		  var tempValue = temperature.toFixed(1).toString() + ' ' + timestamp + '\r\n';
		  fs.appendFile(tmpFileName, tempValue, function (err) {
			if(err) throw err;
		  });

		  timestamp = (new Date(Date.now() - timezoneOffset)).toISOString().slice(0,-1);
		  var humValue = humidity.toFixed(1).toString() + ' ' + timestamp + '\r\n';
		  fs.appendFile(humFileName, humValue, function (err) {
			if(err) throw err;
		  });
	    });
	    sensorTag.setHumidityPeriod(100, function(error) { // Min period is 100 ms
		  console.log('notifyHumidity');
		  sensorTag.notifyHumidity();
	    });
	  }
	  
	  if(BAR_FLAG) {
	    sensorTag.on('barometricPressureChange', function(pressure) {
		  var timestamp = (new Date(Date.now() - timezoneOffset)).toISOString().slice(0,-1);
		  var barValue = pressure.toFixed(1).toString() + ' ' + timestamp + '\r\n';
		  fs.appendFile(barFileName, barValue, function (err) {
			if(err) throw err;
		  });
	    });
	    sensorTag.setBarometricPressurePeriod(100, function(error) { // Min period is 100 ms
		  console.log('notifyBarometricPressure');
		  sensorTag.notifyBarometricPressure();
	    });	
	  } 
	
	  if(MAG_FLAG) {
	    sensorTag.on('magnetometerChange', function(x, y, z) {
		  var timestamp = (new Date(Date.now() - timezoneOffset)).toISOString().slice(0,-1);
		  var magValues = x.toFixed(1).toString() + ' ' + y.toFixed(1).toString() + ' ' + z.toFixed(1).toString() 
		  + ' ' + timestamp + '\r\n';
		  fs.appendFile(magFileName, magValues, function (err) {
			if(err) throw err;
		  });
	    });
	    sensorTag.setMagnetometerPeriod(100, function(error) { // Min period is 100 ms
		  console.log('notifyMagnetometer');
		  sensorTag.notifyMagnetometer();
	    });
	  }
		
	  if(GYR_FLAG) {
	    sensorTag.on('gyroscopeChange', function(x, y, z) {
		  var timestamp = (new Date(Date.now() - timezoneOffset)).toISOString().slice(0,-1);
		  var gyrValues = x.toFixed(1).toString() + ' ' + y.toFixed(1).toString() + ' ' + z.toFixed(1).toString() 
		  + ' ' + timestamp + '\r\n';
		  fs.appendFile(gyrFileName, gyrValues, function (err) {
			if(err) throw err;
		  });
	    });
	    sensorTag.setGyroscopePeriod(100, function(error) { // Min period is 100 ms
		  console.log('notifyGyroscope');
		  sensorTag.notifyGyroscope();
	    });	
	  }
	
	  if(ACC_FLAG) {
	    sensorTag.on('accelerometerChange', function(x, y, z) {
		  var timestamp = (new Date(Date.now() - timezoneOffset)).toISOString().slice(0,-1);
		  var accValues = x.toFixed(1).toString() + ' ' + y.toFixed(1).toString() + ' ' + z.toFixed(1).toString() 
		  + ' ' + timestamp + '\r\n';
		  fs.appendFile(accFileName, accValues, function (err) {
			if(err) throw err;
		  });
	    });
	    sensorTag.setAccelerometerPeriod(100, function(error) { // Min period is 100 ms
		  console.log('notifyAccelerometer');
		  sensorTag.notifyAccelerometer();
	    });
	  }
	
	  callback();
    },
	
	// Fetch audio
    function(callback) {
	  if(AUD_FLAG) {
	    console.log('readAudio');
	    setTimeout(function() {
		  callback();
	    }, measurementTimeout);
	  } else {
	    callback();
	  }		
    },
	
	// Measurement loop without audio
	function(callback) {
		console.log('Measuring...');
	    setTimeout(function() {
		  callback();
		  //sensorTag.disconnect(callback);
	    }, measurementTimeout);
	},
	
    // Disable audio notifications
    function(callback) {
	  if(AUD_FLAG) {
	    console.log('unnotifyAudioStream');
	    sensorTag.unnotifyAudioStream();
	
	    console.log('unnotifyAudioConfig');
	    sensorTag.unnotifyAudioConfig();
	  }
	  callback();
    },
	
	// Disable sensor notifications
    function(callback) {
	  if(TMP_FLAG) {
	    console.log('unnotifyIrTemperature');
	    sensorTag.unnotifyIrTemperature();
	  }
  
	  if(LUX_FLAG) {
	    console.log('unnotifyLuxometer');
	    sensorTag.unnotifyLuxometer();
	  }
  
	  if(HUM_FLAG) {
	    console.log('unnotifyHumidity');
	    sensorTag.unnotifyHumidity();
	  }
  
	  if(BAR_FLAG) {
	    console.log('unnotifyBarometricPressure');
	    sensorTag.unnotifyBarometricPressure();
	  }
  
	  if(MAG_FLAG) {
	    console.log('unnotifyMagnetometer');
	    sensorTag.unnotifyMagnetometer();
	  }
  
	  if(GYR_FLAG) {
	    console.log('unnotifyGyroscope');
	    sensorTag.unnotifyGyroscope();
	  }
  
	  if(ACC_FLAG) {
	    console.log('unnotifyAccelerometer');
	    sensorTag.unnotifyAccelerometer();
	  }
	  
	  callback();  
    },
  
    // Pause
    function(callback) {
	  setTimeout(callback, 2000);
    },
	
	// Disable sensors
    function(callback) {
	  if(TMP_FLAG) {
	    console.log('disableIrTemperature');
	    sensorTag.disableIrTemperature(callback);
	  } else {
	    callback();
	  }
    },
    function(callback) {
	  if(TMP_FLAG) {
	    setTimeout(callback, 1000);
	  } else {
	    callback();
	  }
    },
  
    function(callback) {
	  if(LUX_FLAG) {
	    console.log('disableLuxometer');
	    sensorTag.disableLuxometer(callback);
	  } else {
	    callback();
	  }
    },
    function(callback) {
	  if(LUX_FLAG) {
	    setTimeout(callback, 1000);
	  } else {
	    callback();
	  }
    },
  
    function(callback) {
	  if(HUM_FLAG) {
	    console.log('disableHumidity');
	    sensorTag.disableHumidity(callback);
	  } else {
	    callback();
	  }
    },
    function(callback) {
	  if(HUM_FLAG) {
	    setTimeout(callback, 1000);
	  } else {
	    callback();
	  }
    },
  
    function(callback) {
	  if(BAR_FLAG) {
	    console.log('disableBarometricPressure');
	    sensorTag.disableBarometricPressure(callback);
	  } else {
	    callback();
	  }
    },
    function(callback) {
	  if(BAR_FLAG) {
	    setTimeout(callback, 1000);
	  } else {
	    callback();
	  }
    },
  
    function(callback) {
	  if(MAG_FLAG) {
	    console.log('disableMagnetometer');
	    sensorTag.disableMagnetometer(callback);
	  } else {
	    callback();
	  }
    },
    function(callback) {
	  if(MAG_FLAG) {
	    setTimeout(callback, 1000);
	  } else {
	    callback();
	  }
    },
  
    function(callback) {
	  if(GYR_FLAG) {
	    console.log('disableGyroscope');
	    sensorTag.disableGyroscope(callback);
	  } else {
	    callback();
	  }
    },
    function(callback) {
	  if(GYR_FLAG) {
	    setTimeout(callback, 1000);
	  } else {
	    callback();
	  }
    },
  
    function(callback) {
	  if(ACC_FLAG) {
	    console.log('disableAccelerometer');
	    sensorTag.disableAccelerometer(callback);
	  } else {
	    callback();
	  }
    },
    function(callback) {
	  if(ACC_FLAG) {
	    setTimeout(callback, 1000);
	  } else {
	    callback();
	  }
    },

	// Disconnect
	function(callback) {
      sensorTag.disconnect(callback);
    }
  ]);
});

// Trigger connection timeout
setTimeout(function(){
  if(TIMEOUT_FLAG) {
    console.log('Connection timeout elapsed, exiting...');
    process.exit(0);  
  }
},connectionTimeout);
