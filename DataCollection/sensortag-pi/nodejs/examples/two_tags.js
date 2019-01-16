var util = require('util');
var async = require('async');
var SensorTag = require('./index');

var address1 = "a0e6f8aef586";
var address2 = "a0e6f8af4c83";
var address3 = "247189078e06";

var tags = [];
var tags_status = [];

SensorTag.discoverByUuid(address1, function(tag){
	console.log("found " + tag.uuid);
    tags.push(tag);
    tags_status.push(false);
});

SensorTag.discoverByUuid(address2, function(tag){
    console.log("found " + tag.uuid);
    tags.push(tag);
    tags_status.push(false);

});

SensorTag.discoverByUuid(address3, function(tag){
    console.log("found " + tag.uuid);
    tags.push(tag);
    tags_status.push(false);

});

setTimeout(function(){
	console.log("Trying to connect to sensors %s", tags);
	
	tags.forEach(function(tag, i) {
		tag.on('disconnect', function(callback) {
			console.log('disconnected!');
			process.exit(0);
		});
		tag.connectAndSetUp(function(callback) {
			console.log("connected " + tag);
			tags_status[i] = true;
			
			async.series([ 
			
				function(callback) {
					console.log('TAG:#%s\tnotifyAudioConfig',tag.uuid);
					tag.notifyAudioConfig(callback);
                },
                function(callback) {
					setTimeout(callback, 2000);
                },
				
			    /*
				function(callback) {
				  console.log('TAG:#%s\treadAudio',tag.uuid);
				  tag.on('AudioChange', function(audio) {
				  });
				
				  console.log('TAG:#%s\tnotifyAudioStream',tag.uuid);
				  tag.notifyAudioStream(function(error) {
			        setTimeout(function() {
			          console.log('TAG:#%s\tunnotifyAudioStream',tag.uuid);
                      tag.unnotifyAudioStream(callback);
                    }, 32000);
                  });
				},
	  
				function(callback) {
				  setTimeout(callback, 2000);
				},
	  
				function(callback) {
				  console.log('TAG:#%s\tunnotifyAudioConfig',tag.uuid);
				  tag.unnotifyAudioConfig(callback);
				},
	  
				function(callback) {
				  setTimeout(callback, 2000);
				},
				//*/
				
                function(callback) {
					console.log('TAG:#%s\tnotifyAudioStream',tag.uuid);
					tag.notifyAudioStream(callback);
                },
                function(callback) {
					setTimeout(callback, 2000);
                },
				
				/*
				function(callback) {
				  tag.setAudioFlag(callback);
				},
				*/
				
				function(callback) {
					console.log('readAudio');
					tag.on('AudioChange', function(audio) {
					  if(!audio) {
					     callback();
					  }					 
					});
				},
				
				function(callback) {
				  console.log('TAG:#%s\tunnotifyAudioStream',tag.uuid);
				  tag.unnotifyAudioStream(callback);
				},
				
				function(callback) {
				  setTimeout(callback, 2000);
				},
	  
				function(callback) {
				  console.log('TAG:#%s\tunnotifyAudioConfig',tag.uuid);
				  tag.unnotifyAudioConfig(callback);
				},
				
				function(callback) {
				  setTimeout(callback, 2000);
				},
				
				/*
				function(callback) {
					console.log('readSimpleRead - waiting for button press ...');
					tag.on('simpleKeyChange', function(left, right, reedRelay) {
						console.log('left: ' + left);
						console.log('right: ' + right);
						if (tag.type === 'cc2650') {
							console.log('reed relay: ' + reedRelay);
						}

						if (left || right) {
							tag.notifySimpleKey(callback);
						}
					});

					tag.notifySimpleKey();
				},
				*/
				
				function(callback) {
					console.log('disconnect', tag.uuid);
					tag.disconnect(callback);
				}
				
			]);
		});
	});
	
},4000);