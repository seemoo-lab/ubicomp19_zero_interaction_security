var SensorTag = require('./index');

function sensorTagDisovered(sensorTag) {
  console.log('discovered: ' + sensorTag);

  sensorTag.once('disconnect', function() {
    console.log('disconnected');
  });

  sensorTag.connectAndSetUp(function(err) {
    // restart discovery
 //   SensorTag.discover(sensorTagDisovered);

    if (err) {
      console.log('error occurred on connect or set up!');
      return;
    }

    console.log('connected');

    // do some stuff with the sensorTag ...
  });
}

// start discovery of a SensorTag
console.log('looking for tag 247189078e06');
SensorTag.discoverByAddress("247189078e06",sensorTagDisovered);
console.log('looking for tag a0e6f8aef586');
SensorTag.discoverByAddress("a0e6f8aef586",sensorTagDisovered);
