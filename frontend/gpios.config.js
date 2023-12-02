/**
 * Gpios config component
 * Handle gpios configuration
 */
angular
.module('Cleep')
.directive('gpiosConfigComponent', ['$rootScope', 'gpiosService', 'cleepService', 'toastService', 'confirmService', '$mdDialog',
function($rootScope, gpiosService, cleepService, toast, confirm, $mdDialog) {

    var gpiosConfigController = function() {
        var self = this;
        self.raspiGpios = [];
        self.devices = [];
        self.name = '';
        self.mode = 'input';
        self.keep = false;
        self.inverted = false;
        self.gpioUpdate = false;
        self.selectedGpios = [{gpio:null, 'label':'wire'}];

        self.$onInit = function() {
            cleepService.getModuleConfig('gpios')
                .then(function(config) {
                    self.raspiGpios = config.raspi_gpios;
                });

            // add module actions to fabButton
            var actions = [{
                icon: 'plus',
                callback: self.openAddDialog,
                tooltip: 'Add gpio'
            }];
            $rootScope.$broadcast('enableFab', actions);
        };

        self._resetValues = function() {
            self.name = '';
            self.selectedGpios = [{gpio:null, 'label':'wire'}];
            self.mode = 'input';
            self.keep = false;
            self.inverted = false;
        };

        self.closeDialog = function() {
            // check values
            if (self.name.length === 0) {
                toast.error('All fields are required');
            } else {
                $mdDialog.hide();
            }
        };

        self.cancelDialog = function() {
            $mdDialog.cancel();
        };

        self._openDialog = function() {
            return $mdDialog.show({
                controller: function() { return self; },
                controllerAs: '$ctrl',
                templateUrl: 'gpio.dialog.html',
                parent: angular.element(document.body),
                clickOutsideToClose: false,
                fullscreen: true
            });
        };
        
        self.openAddDialog = function() {
            self.gpioUpdate = false;
            self._openDialog()
                .then(function() {
                    return gpiosService.addGpio(self.name, self.selectedGpios[0].gpio, self.mode, self.keep, self.inverted);
                })
                .then(function() {
                    toast.success('Gpio added');
                })
                .finally(function() {
                    self._resetValues();
                });
        }; 

        self.openUpdateDialog = function(device) {
            // set editor's value
            self.name = device.name;
            self.selectedGpios = [{gpio:device.gpio, label:'gpio'}];
            self.mode = device.mode;
            self.keep = device.keep;
            self.inverted = device.inverted;

            // open dialog
            self.gpioUpdate = true;
            self._openDialog()
                .then(function() {
                    return gpiosService.updateGpio(device.uuid, self.name, self.keep, self.inverted);
                })
                .then(function() {
                    toast.success('Gpio updated');
                })
                .finally(function() {
                    self._resetValues();
                });
        };

        self.openDeleteDialog = function(device) {
            confirm.open('Delete gpio?', null, 'Delete')
                .then(function() {
                    return gpiosService.deleteGpio(device.uuid);
                })
                .then(function() {
                    toast.success('Gpio deleted');
                });
        };

        $rootScope.$watchCollection(
            () => cleepService.devices,
            (newDevices) => {
                if (Object.keys(newDevices || {}).length) {
                    self.devices = newDevices
                        .filter((device) => device.module === 'gpios')
                        .map((device) => ({
                            icon: 'video-input-component',
                            title: self.getDeviceTitle(device),
                            subtitle: self.getDeviceSubtitle(device),
                            clicks: [
                                {
                                    icon: 'pencil',
                                    tooltip: (device.owner === 'gpios' ? 'Edit' : 'Gpios app is not owner of the gpio'),
                                    disabled: device.owner !== 'gpios',
                                    click: self.openUpdateDialog,
                                    meta: { device },
                                },
                                {
                                    icon: 'delete',
                                    tooltip: (device.owner === 'gpios' ? 'Delete' : 'Gpios app is not owner of the gpio'),
                                    disabled: device.owner !== 'gpios',
                                    click: self.openDeleteDialog,
                                    meta: { device },
                                }
                            ],
                        }));
                }
            },
        );

        self.getDeviceTitle = function (device) {
            return '<strong>' + device.name + '</strong>: current value ' + (device.on ? 'ON' : 'OFF');
        };

        self.getDeviceSubtitle = function (device) {
            return 'Gpio: ' + device.gpio + ', mode: ' + device.mode + ', save state: ' + device.keep + ', inverted: ' + device.inverted;
        };
    };

    return {
        templateUrl: 'gpios.config.html',
        replace: true,
        scope: true,
        controller: gpiosConfigController,
        controllerAs: 'gpiosCtl',
    };
}]);

