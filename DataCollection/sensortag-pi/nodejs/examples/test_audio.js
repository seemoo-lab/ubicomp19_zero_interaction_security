// test_audio.js
// Santiago Aragon
// 05.04.17
//
// This script connects to the tag with address = address3 and turns on
// the audio notifications, streams, and stores audio data from the
// sensor in a file named with the present day and time.
var counter = 0;
var util = require('util');
var async = require('async');
var SensorTag = require('./index');
//var date = new Date();
//now = date.toISOString();
var USE_READ = false;

// Easy to include/exclude sensors
var TMP_FLAG = false; // for now always false because dedicated tmp sensor is disabled
var LUX_FLAG = true;
var HUM_FLAG = true;
var BAR_FLAG = true;
var MAG_FLAG = true;
var GYR_FLAG = true;
var ACC_FLAG = true;

var AUD_FLAG = true;

//var address3 = "a0e6f8af4c83";
var address3 = "a0e6f8aef586";
var timeout = 15000; // time in ms

var fs = require('fs');
var tmpFileName = 'data/tmpData';
var luxFileName = 'data/luxData';
var humFileName = 'data/humData';
var barFileName = 'data/barData';
var magFileName = 'data/magData';
var gyrFileName = 'data/gyrData';
var accFileName = 'data/accData';

SensorTag.discoverByUuid(address3,function(sensorTag){
  console.log('discovered: ' + sensorTag);

  sensorTag.on('disconnect', function() {
    console.log('disconnected!');
    process.exit(0);
  });

  async.series([
      function(callback) {
        console.log('connectAndSetUp');
        sensorTag.connectAndSetUp(callback);

      },
	  
      function(callback) {
		console.log('readDeviceName');
        sensorTag.readDeviceName(function(error, deviceName) {
          console.log('\tdevice name = ' + deviceName);
          callback();
        });
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
            //console.log('\tobject temperature = %d °C', objectTemperature.toFixed(1));
            //console.log('\tambient temperature = %d °C', ambientTemperature.toFixed(1))
			var date = new Date();
		    var tempValue = ambientTemperature.toFixed(1).toString() + ' ' + date.toISOString() + '\r\n';
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
            //console.log('\tlux = %d', lux.toFixed(1));
			var date = new Date();
		    var luxValue = lux.toFixed(1).toString() + ' ' + date.toISOString() + '\r\n';
		    fs.appendFile(luxFileName, luxValue, function (err) {
		      if(err) throw err;
	        });
          });
		  sensorTag.setLuxometerPeriod(300, function(error) { // Min period is 100 ms
            console.log('notifyLuxometer');
            sensorTag.notifyLuxometer();
          });
        }
		
	    if(HUM_FLAG) {
          sensorTag.on('humidityChange', function(temperature, humidity) {
            //console.log('\ttemperature = %d °C', temperature.toFixed(1));
            //console.log('\thumidity = %d %', humidity.toFixed(1));
			var date = new Date();
		    var tempValue = temperature.toFixed(1).toString() + ' ' + date.toISOString() + '\r\n';
		    fs.appendFile(tmpFileName, tempValue, function (err) {
		      if(err) throw err;
	        });
			date = new Date();
		    var humValue = humidity.toFixed(1).toString() + ' ' + date.toISOString() + '\r\n';
		    fs.appendFile(humFileName, humValue, function (err) {
		      if(err) throw err;
	        });
          });
		  sensorTag.setHumidityPeriod(300, function(error) { // Min period is 100 ms
            console.log('notifyHumidity');
            sensorTag.notifyHumidity();
          });
	    }
		  
		if(BAR_FLAG) {
	      sensorTag.on('barometricPressureChange', function(pressure) {
            //console.log('\tpressure = %d mBar', pressure.toFixed(1));
			var date = new Date();
		    var barValue = pressure.toFixed(1).toString() + ' ' + date.toISOString() + '\r\n';
		    fs.appendFile(barFileName, barValue, function (err) {
		      if(err) throw err;
	        });
          });
		  sensorTag.setBarometricPressurePeriod(300, function(error) { // Min period is 100 ms
            console.log('notifyBarometricPressure');
            sensorTag.notifyBarometricPressure();
          });	
	    } 
		
		if(MAG_FLAG) {
		  sensorTag.on('magnetometerChange', function(x, y, z) {
            //console.log('\tx = %d μT', x.toFixed(1));
            //console.log('\ty = %d μT', y.toFixed(1));
            //console.log('\tz = %d μT', z.toFixed(1));
			var date = new Date();
	        var magValues = x.toFixed(1).toString() + ' ' + y.toFixed(1).toString() + ' ' + z.toFixed(1).toString() + 
			' ' + date.toISOString() + '\r\n';
		    fs.appendFile(magFileName, magValues, function (err) {
		      if(err) throw err;
	        });
          });
		  sensorTag.setMagnetometerPeriod(300, function(error) { // Min period is 100 ms
            console.log('notifyMagnetometer');
            sensorTag.notifyMagnetometer();
          });
	    }
			
        if(GYR_FLAG) {
	      sensorTag.on('gyroscopeChange', function(x, y, z) {
            //console.log('\tx = %d °/s', x.toFixed(1));
            //console.log('\ty = %d °/s', y.toFixed(1));
            //console.log('\tz = %d °/s', z.toFixed(1));
			var date = new Date();
	        var gyrValues = x.toFixed(1).toString() + ' ' + y.toFixed(1).toString() + ' ' + z.toFixed(1).toString() + 
			' ' + date.toISOString() + '\r\n';
		    fs.appendFile(gyrFileName, gyrValues, function (err) {
		      if(err) throw err;
	        });
          });
		  sensorTag.setGyroscopePeriod(300, function(error) { // Min period is 100 ms
            console.log('notifyGyroscope');
            sensorTag.notifyGyroscope();
          });	
	    }
		
		if(ACC_FLAG) {
		  sensorTag.on('accelerometerChange', function(x, y, z) {
            //console.log('\tx = %d G', x.toFixed(1));
            //console.log('\ty = %d G', y.toFixed(1));
            //console.log('\tz = %d G', z.toFixed(1));
			var date = new Date();
		    var accValues = x.toFixed(1).toString() + ' ' + y.toFixed(1).toString() + ' ' + z.toFixed(1).toString() + 
			' ' + date.toISOString() + '\r\n';
		    fs.appendFile(accFileName, accValues, function (err) {
		      if(err) throw err;
	        });
          });
		  sensorTag.setAccelerometerPeriod(300, function(error) { // Min period is 100 ms
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
			/*
            sensorTag.on('AudioChange', function(audio) {
		      if(!audio) {
			    callback();
			  }			
            });
			*/
			callback();
          }, timeout);
		} else {
		  callback();
		}		
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
	
	 /*
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
	  */
	  
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
	  
	/*
      function(callback) {
        console.log('readSimpleRead - waiting for button press ...');
        sensorTag.on('simpleKeyChange', function(left, right, reedRelay) {
          console.log('left: ' + left);
          console.log('right: ' + right);
          if (sensorTag.type === 'cc2650') {
            console.log('reed relay: ' + reedRelay);
          }

          if (left || right) {
            sensorTag.notifySimpleKey(callback);
          }
        });

        sensorTag.notifySimpleKey();
      },*/
	  
      function(callback) {
        console.log('disconnect');
        sensorTag.disconnect(callback);
      }
    ]);
});
