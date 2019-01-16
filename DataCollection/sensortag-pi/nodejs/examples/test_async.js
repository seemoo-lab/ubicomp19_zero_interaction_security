// test_async.js
// Santiago Aragon
//
//
// This scripts connect to the first tag that is found and turns on
// and logs the following sensors in a notification fashion:
// temperature, magnetometer, accelerometer, humidity, barometer,
// gyroscope and luxometer.
// The notifications are turned off after timeout/10000 seconds.
//
var util = require('util');
var async = require('async');
var tag = require('./index');

var timeout = 10000;

tag.discover(function(tag) {
  console.log('discovered: ' + tag);

  tag.on('disconnect', function() {
    console.log('disconnected!');
    process.exit(0);
  });

  async.series([
      function(callback) {
        console.log('connectAndSetUp');
        tag.connectAndSetUp(callback);
      },
      function(callback) {
        console.log('enableIrTemperature');
        tag.enableIrTemperature(callback);
      },
      function(callback) {
        setTimeout(callback, 2000);
      },
      function(callback) {
        console.log('enableMagnetometer');
        tag.enableMagnetometer(callback);
      },
      function(callback) {
        setTimeout(callback, 2000);
      },
      function(callback) {
        console.log('enableAcceleromenter');
        tag.enableAccelerometer(callback);
      },
      function(callback) {
        setTimeout(callback, 2000);
      },
      function(callback) {
        console.log('enableHumidity');
        tag.enableHumidity(callback);
      },
      function(callback) {
        setTimeout(callback, 2000);
      },
      function(callback) {
        console.log('enableBarometricPressure');
        tag.enableBarometricPressure(callback);
      },
      function(callback) {
        setTimeout(callback, 2000);
      },
      function(callback) {
        console.log('enableGyroscope');
        tag.enableGyroscope(callback);
      },
      function(callback) {
        setTimeout(callback, 2000);
      },
      function(callback) {
        console.log('enableLuxometer');
        tag.enableLuxometer(callback);
      },
      function(callback) {
        setTimeout(callback, 5000);
      },
      function(callback) {
          tag.on('irTemperatureChange', function(objectTemperature, ambientTemperature) {
            console.log('\tobject temperature = %d °C', objectTemperature.toFixed(1));
            console.log('\tambient temperature = %d °C', ambientTemperature.toFixed(1))
          });
          console.log('setIrTemperaturePeriod');
          tag.setIrTemperaturePeriod(500, function(error) {
            console.log('notifyIrTemperature');
            tag.notifyIrTemperature();
          });
          tag.on('magnetometerChange', function(x, y, z) {
            console.log('\tx = %d μT', x);
            console.log('\ty = %d μT', y);
            console.log('\tz = %d μT', z);
          });
          tag.setMagnetometerPeriod(500, function(error) {
            tag.notifyMagnetometer();
          });
          tag.on('accelerometerChange', function(error, x, y, z) {
            console.log('\tx = %d G', x);
            console.log('\ty = %d G', y);
            console.log('\tz = %d G', z);
            });
          tag.setAccelerometerPeriod(500, function(error) {
            tag.notifyAccelerometer();
          });
          tag.on('humidityChange', function(error, temperature, humidity) {
            console.log('\ttemperature = %d °C', temperature);
            console.log('\thumidity = %d %', humidity);
            });
          tag.setHumidityPeriod(500, function(error) {
            tag.notifyHumidity();
          });
          tag.on('barometricPressureChange', function(error, pressure) {
            console.log('\tpressure = %d mBar', pressure);
            });
          tag.setBarometricPressurePeriod(500, function(error) {
            tag.notifyBarometricPressure();
          });
          tag.on('gyroscopeChange', function(error, x, y, z) {
            console.log('\tx = %d °/s', x);
            console.log('\ty = %d °/s', y);
            console.log('\tz = %d °/s', z);
          });
          tag.setGyroscopePeriod(500, function(error) {
            tag.notifyGyroscope();
          });
          tag.on('luxometerChange', function(error, lux) {
            console.log('\tlux = %d', lux);
          });
          tag.setLuxometerPeriod(500, function(error) {
            tag.notifyLuxometer(callback);
          });
      },
      function(callback) {
        setTimeout(function() {
                console.log('Turning off');
                tag.unnotifyIrTemperature();
                tag.disableIrTemperature();
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
