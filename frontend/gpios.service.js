/**
 * Gpios service
 * Handle gpios module requests
 */
angular
.module('Cleep')
.service('gpiosService', ['$q', '$rootScope', 'rpcService', 'raspiotService',
function($q, $rootScope, rpcService, raspiotService) {
    var self = this;
    
    /**
     * Init module devices
     */
    self.initDevices = function(devices) {
        for( var uuid in devices ) {
            // change current color if gpio is on
            if( devices[uuid].on ) {
                devices[uuid].__widget.mdcolors = '{background:"default-accent-400"}';
            }
        }

        return devices;
    };

    /**
     * Return raspi gpios (according to board version)
     */
    self.getRaspiGpios = function() {
        return rpcService.sendCommand('get_raspi_gpios', 'gpios');
    };

    /**
     * Return list of assigned gpios
     */
    self.getAssignedGpios = function() {
        return rpcService.sendCommand('get_assigned_gpios', 'gpios');
    };

    /**
     * Return gpios usage
     */
    self.getPinsUsage = function() {
        return rpcService.sendCommand('get_pins_usage', 'gpios');
    };

    /**
     * Add new gpio
     */
    self.addGpio = function(name, gpio, mode, keep, inverted) {
        return rpcService.sendCommand('add_gpio', 'gpios', {'name':name, 'gpio':gpio, 'mode':mode, 'keep':keep, 'inverted':inverted})
            .then(function(resp) {
                return $q.all(raspiotService.reloadModuleConfig('gpios'), raspiotService.reloadDevices());
            })
    };

    /**
     * Delete gpio
     */
    self.deleteGpio = function(uuid) {
        return rpcService.sendCommand('delete_gpio', 'gpios', {'uuid':uuid})
            .then(function(resp) {
                return $q.all(raspiotService.reloadModuleConfig('gpios'), raspiotService.reloadDevices());
            });
    };

    /**
     * Update device
     */
    self.updateGpio = function(uuid, name, keep, inverted) {
        return rpcService.sendCommand('update_gpio', 'gpios', {'uuid':uuid, 'name':name, 'keep':keep, 'inverted':inverted})
            .then(function(resp) {
                return $q.all(raspiotService.reloadModuleConfig('gpios'), raspiotService.reloadDevices());
            });
    };

    /**
     * Turn on specified gpio
     */
    self.turnOn = function(uuid) {
        return rpcService.sendCommand('turn_on', 'gpios', {'uuid':uuid});
    };

    /**
     * Turn off specified gpio
     */
    self.turnOff = function(uuid) {
        return rpcService.sendCommand('turn_off', 'gpios', {'uuid':uuid});
    };

    /**
     * Catch gpio on events
     */
    $rootScope.$on('gpios.gpio.on', function(event, uuid, params) {
        for( var i=0; i<raspiotService.devices.length; i++ ) {
            if( raspiotService.devices[i].uuid==uuid ) {
                if( raspiotService.devices[i].on===false ) {
                    raspiotService.devices[i].on = true;
                    raspiotService.devices[i].__widget.mdcolors = '{background:"default-accent-400"}';
                    break;
                }
            }
        }
    });

    /**
     * Catch gpio off events
     */
    $rootScope.$on('gpios.gpio.off', function(event, uuid, params) {
        for( var i=0; i<raspiotService.devices.length; i++ ) {
            if( raspiotService.devices[i].uuid==uuid ) {
                if( raspiotService.devices[i].on===true ) {
                    raspiotService.devices[i].on = false;
                    raspiotService.devices[i].__widget.mdcolors = '{background:"default-primary-300"}';
                    break;
                }
            }
        }
    });
}]);

