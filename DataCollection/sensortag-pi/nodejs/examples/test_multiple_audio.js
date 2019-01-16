// test_async.js
// Santiago Aragon
// 05.04.17
//
// This script connects to the tags with addresses: address1, address2
// and address3. For every tag it turns on
// and logs the following sensors in a notification fashion: audio,
// magnetometer, accelerometer, humidity, barometer,
// gyroscope and luxometer.
// The notifications are turned off after timeout/1000 seconds.
//
var SensorTag = require('./lib/sensortag');
var async = require('async');
var address1 = "a0e6f8aef586";
var address2 = "247189078e06";
var address3 = "a0e6f8af4c83";
var tags = [];
var tags_status = [];
var now = new Date().toISOString().slice(0,-14);
var timeout = 60000;


var read_interval = 500; // Read interval in ms
SensorTag.discoverByUuid(address1,function(tag){
    console.log("found " + tag.uuid);
    tags.push(tag);
    tags_status.push(false);
});

SensorTag.discoverByUuid(address2,function(tag){
    console.log("found " + tag.uuid);
    tags.push(tag);
    tags_status.push(false);

});

SensorTag.discoverByUuid(address3,function(tag){
    console.log("found " + tag.uuid);
    tags.push(tag);
    tags_status.push(false);

});

 setTimeout(function(){
   console.log("Trying to connect to sensors %s",tags);

   tags.forEach(function(tag,i){
      tag.on('disconnect', function(callback) {
        console.log('disconnected!');
        process.exit(0);
      });
      tag.connectAndSetUp(function(callback){
          console.log("connected " + tag);
          tags_status[i] = true;
          async.series([
                  function(callback) {
                    console.log('TAG:#%s\tnotify config',tag.uuid);
                    tag.notifyAudioConfig(callback);
                  },
                  function(callback) {
                    setTimeout(callback, 2000);
                  },

                function(callback) {
                    console.log('TAG:#%s\tnotify stream',tag.uuid);
                    tag.notifyAudioStream(callback);
                  },
                  function(callback) {
                    setTimeout(callback, 2000);
                  },
                  function(callback) {
                    console.log('TAG:#%s\treadAudio',tag.uuid);
                    tag.on('AudioChange', function(audioData) {
                      if (audioData == null) {
                        console.log('\No data');
                      } else {
                        console.log('\audio data = %s', audioData.toString('hex'));
                        tag.saveAudio(audioData,'audiodata_'+now, callback);
                      }
                    });
                  },
                  ]);
          async.series([
            // function(callback) {
            //   console.log('TAG:#%s\tenableIrTemperature',tag.uuid);
            //   tag.enableIrTemperature(callback);
            // },
            function(callback) {
              setTimeout(callback, 2000);
            },
            function(callback) {
              console.log('TAG:#%s\tenableMagnetometer',tag.uuid);
              tag.enableMagnetometer(callback);
            },
            function(callback) {
              setTimeout(callback, 2000);
            },
            function(callback) {
              console.log('TAG:#%s\tenableAcceleromenter',tag.uuid);
              tag.enableAccelerometer(callback);
            },
            function(callback) {
              setTimeout(callback, 2000);
            },
            function(callback) {
              console.log('TAG:#%s\tenableHumidity',tag.uuid);
              tag.enableHumidity(callback);
            },
            function(callback) {
              setTimeout(callback, 2000);
            },
            function(callback) {
              console.log('TAG:#%s\tenableBarometricPressure',tag.uuid);
              tag.enableBarometricPressure(callback);
            },
            function(callback) {
              setTimeout(callback, 2000);
            },
            function(callback) {
              console.log('TAG:#%s\tenableGyroscope',tag.uuid);
              tag.enableGyroscope(callback);
            },
            function(callback) {
              setTimeout(callback, 2000);
            },
            function(callback) {
              console.log('TAG:#%s\tenableLuxometer',tag.uuid);
              tag.enableLuxometer(callback);
            },
            function(callback) {
              setTimeout(callback, 5000);
            },
            function(callback) {
                // tag.on('irTemperatureChange', function(objectTemperature, ambientTemperature) {
                //   console.log('TAG:#%s\tobject temperature = %d °C', tag.uuid, objectTemperature.toFixed(1));
                //   console.log('TAG:#%s\tambient temperature = %d °C',tag.uuid,  ambientTemperature.toFixed(1))
                // });
                // console.log('setIrTemperaturePeriod');
                // tag.setIrTemperaturePeriod(500, function(error) {
                //   console.log('notifyIrTemperature');
                //   tag.notifyIrTemperature();
                // });
                tag.on('magnetometerChange', function(x, y, z) {
                  console.log('TAG:#%s\tx = %d μT', tag.uuid, x);
                  console.log('TAG:#%s\ty = %d μT', tag.uuid, y);
                  console.log('TAG:#%s\tz = %d μT', tag.uuid, z);
                });
                tag.setMagnetometerPeriod(500, function(error) {
                  tag.notifyMagnetometer();
                });
                tag.on('accelerometerChange', function( x, y, z) {
                  console.log('TAG:#%s\tx = %d G', tag.uuid, x);
                  console.log('TAG:#%s\ty = %d G', tag.uuid, y);
                  console.log('TAG:#%s\tz = %d G', tag.uuid, z);
                  });
                tag.setAccelerometerPeriod(500, function(error) {
                  tag.notifyAccelerometer();
                });
                tag.on('humidityChange', function(temperature, humidity) {
                  console.log('TAG:#%s\ttemperature = %d °C', tag.uuid, temperature);
                  console.log('TAG:#%s\thumidity = %d %', tag.uuid, humidity);
                  });
                tag.setHumidityPeriod(500, function(error) {
                  tag.notifyHumidity();
                });
                tag.on('barometricPressureChange', function( pressure) {
                  console.log('TAG:#%s\tpressure = %d mBar', tag.uuid, pressure);
                  });
                tag.setBarometricPressurePeriod(500, function(error) {
                  tag.notifyBarometricPressure();
                });
                tag.on('gyroscopeChange', function(x, y, z) {
                  console.log('TAG:#%s\tx = %d °/s', tag.uuid, x);
                  console.log('TAG:#%s\ty = %d °/s', tag.uuid, y);
                  console.log('TAG:#%s\tz = %d °/s', tag.uuid, z);
                });
                tag.setGyroscopePeriod(500, function(error) {
                  tag.notifyGyroscope();
                });
                tag.on('luxometerChange', function(lux) {
                  console.log('TAG:#%s\tlux = %d', tag.uuid, lux);
                });
                tag.setLuxometerPeriod(500, function(error) {
                  tag.notifyLuxometer(callback);
                });
            },
            function(callback) {
              setTimeout(function() {
                      console.log('Turning off');
                      // tag.unnotifyIrTemperature();
                      // tag.disableIrTemperature();
                      tag.unnotifyMagnetometer();
                      tag.disableMagnetometer(callback);
                      tag.unnotifyAccelerometer()
                      tag.disableAccelerometer();
                      tag.unnotifyHumidity();
                      tag.disableHumidity();
                      tag.unnotifyBarometricPressure();
                      tag.disableBarometricPressure();
                      tag.unnotifyGyroscope();
                      tag.disableGyroscope();
                      tag.unnotifyLuxometer();
                      tag.disableLuxometer();
                    }, timeout);
            },
            function(callback) {
              setTimeout(callback, 2000);
            },
            function(callback) {
              console.log('disconnect');
              tag.disconnect(callback);
            }
    ]
  );
     });

    });

},4000);





