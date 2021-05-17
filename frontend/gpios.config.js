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
        self.devices = cleepService.devices;
        self.name = '';
        self.mode = 'input';
        self.keep = false;
        self.inverted = false;
        self.updateDevice = false;
        self.selectedGpios = [{gpio:null, 'label':'wire'}];

        /**
         * Reset editor's values
         */
        self._resetValues = function() {
            self.name = '';
            self.selectedGpios = [{gpio:null, 'label':'wire'}];
            self.mode = 'input';
            self.keep = false;
            self.inverted = false;
        };

        /**
         * Close dialog
         */
        self.closeDialog = function() {
            // check values
            if( self.name.length===0 ) {
                toast.error('All fields are required');
            } else {
                $mdDialog.hide();
            }
        };

        /**
         * Cancel dialog
         */
        self.cancelDialog = function() {
            $mdDialog.cancel();
        };

        /**
         * Open dialog (internal use)
         */
        self._openDialog = function() {
            return $mdDialog.show({
                controller: function() { return self; },
                controllerAs: 'gpiosCtl',
                templateUrl: 'addGpio.dialog.html',
                parent: angular.element(document.body),
                clickOutsideToClose: false,
                fullscreen: true
            });
        };
        
        /**
         * Add device
         */
        self.openAddDialog = function() {
            self.updateDevice = false;
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

        /**
         * Update device
         */
        self.openUpdateDialog = function(device) {
            // set editor's value
            self.name = device.name;
            self.selectedGpios = [{gpio:device.gpio, label:'gpio'}];
            self.mode = device.mode;
            self.keep = device.keep;
            self.inverted = device.inverted;

            // open dialog
            self.updateDevice = true;
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

        /**
         * Delete device
         */
        self.openDeleteDialog = function(device) {
            confirm.open('Delete gpio?', null, 'Delete')
                .then(function() {
                    return gpiosService.deleteGpio(device.uuid);
                })
                .then(function() {
                    toast.success('Gpio deleted');
                });
        };

        /**
         * Init controller
         */
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
    };

    return {
        templateUrl: 'gpios.config.html',
        replace: true,
        scope: true,
        controller: gpiosConfigController,
        controllerAs: 'gpiosCtl',
    };
}]);

