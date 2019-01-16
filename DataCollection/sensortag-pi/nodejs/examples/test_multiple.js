// test_async.js
// Santiago Aragon
// 05.04.17
//
// This script connects to the tags with addresses: address1, address2
// and address3. For every tag it turns on
// and logs the following sensors in a request reading fashion:
// temperature, magnetometer, accelerometer, humidity, barometer,
// gyroscope and luxometer. The readings are requested every
// read_interval/1000 seconds.
//

var SensorTag = require('./lib/sensortag');
var async = require('async');
var address1 = "a0e6f8aef586";
var address2 = "247189078e06";
var address3 = "a0e6f8af4c83";
var tags = [];
var tags_status = [];



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
      tag.connectAndSetUp(function(callback){
          console.log("connected " + tag);
          tags_status[i] = true;
          async.series([
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
                setTimeout(callback, 4000);
              },
              ]);
     });

    });

},4000);


setInterval(function(){
  setTimeout(function(){

   tags.forEach(function(tag,i){
    console.log("Trying out sensor %s %s",tag,tags_status[i]);
    if (tags_status[i]) {
    async.series([
      function(callback){
        console.log("Reading from sensors %s",tags);
        tag.readSystemId(function(error, systemId) {
          console.log('\tsystem id = ' + systemId);
        });
        console.log("Attempting to read");
        //setInterval(function(){
        tag.readMagnetometer(function(error, x, y, z) {
          console.log('\tx = %d μT', x.toFixed(1));
          console.log('\ty = %d μT', y.toFixed(1));
          console.log('\tz = %d μT', z.toFixed(1));
        });
        tag.readIrTemperature(function(error, objectTemperature, ambientTemperature) {
          console.log('\tobject temperature = %d °C', objectTemperature.toFixed(1));
          console.log('\tambient temperature = %d °C', ambientTemperature.toFixed(1));
          });
        tag.readAccelerometer(function(error, x, y, z) {
          console.log('\tx = %d G', x.toFixed(1));
          console.log('\ty = %d G', y.toFixed(1));
          console.log('\tz = %d G', z.toFixed(1));
          });
        tag.readHumidity(function(error, temperature, humidity) {
          console.log('\ttemperature = %d °C', temperature.toFixed(1));
          console.log('\thumidity = %d %', humidity.toFixed(1));
          });
        tag.readBarometricPressure(function(error, pressure) {
          console.log('\tpressure = %d mBar', pressure.toFixed(1));
          });
        tag.readGyroscope(function(error, x, y, z) {
          console.log('\tx = %d °/s', x.toFixed(1));
          console.log('\ty = %d °/s', y.toFixed(1));
          console.log('\tz = %d °/s', z.toFixed(1));
          });
        tag.readLuxometer(function(error, lux) {
          console.log('\tlux = %d', lux.toFixed(1));
          });
      },
    ]);
    }else{
      console.log("Tag  not connected");
    }



    });
 },8000) // Should be at least 5000 since the last timeout is 5000
},read_interval); // Reading every second


