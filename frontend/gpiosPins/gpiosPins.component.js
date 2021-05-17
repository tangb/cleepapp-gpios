/**
 * GPIOS pins component
 * Display graphical representation of raspi gpios
 * Allow interaction by clicking on pins
 */
angular
.module('Cleep')
.directive('gpiosPinsComponent', ['gpiosService', 'toastService', 'confirmService',
function(gpiosService, toast, confirm) {

    var gpiosPinsController = ['$scope', function($scope) {
        var self = this;
        self.revision = 3;
        self.evens = [];
        self.odds = [];
        self.maxPins = 1;
        // it's an object for performance (faster than array's indexOf function)
        self.selectedPins = {};
        self.countPins = 0;
        self.currentIndex = -1;
        self.currentLabel = '';
        self.pinInfos = [];
        self.configuredGpio = {};
        // Yellow-Blue-Green-Lime-DeepOrange-BlueGrey-Brown-Cyan-Pink-Teal
        self.colors = ['#FFEB3B', '#2196F3', '#4CAF50', '#CDDC39', '#FF5722', '#607D8B', '#795548', '#00BCD4', '#FF80AB', '#009688'];
        self.readonly = false;

        /**
         * User clicks on pin
         */
        self.click = function(pin) {
            if( self.readonly ) {
                //readonly no modification possible
                return;
            }

            if( pin.gpio && !pin.assigned ) {
                if( pin.selected ) {
                    // unselect pin
                    
                    // delete entry in selected pin list
                    if( pin.pin in self.selectedPins ) {
                        delete self.selectedPins[pin.pin];
                    }

                    // remove configuration in component parameter
                    for( var i=0; i<$scope.selectedGpios.length; i++ ) {
                        if( $scope.selectedGpios[i].gpio===pin.name ) {
                            $scope.selectedGpios[i].gpio = null;
                            break;
                        }
                    }

                    // unselect pin in widget
                    pin.selected = !pin.selected;

                    // and remove selected color
                    pin.color = null;

                    // finally decrease number of selected pins
                    self.countPins--;
                } else {
                    // select pin
                    
                    // is max number of selected pins already reached?
                    if( self.countPins<self.maxPins ) {
                        // max not reached yet
                        // add new entry in selected pin list
                        self.selectedPins[pin.pin] = null;

                        // add configuration in component parameter
                        $scope.selectedGpios[self.currentIndex].gpio = pin.name;

                        // select pin and update color
                        pin.selected = !pin.selected;
                        pin.color = self.pinInfos[self.currentIndex].color;

                        // finally incrase number of selected pins
                        self.countPins++;
                    }
                    /*else {
                        toast.info('Selection is limited to '+ self.maxPins + ' gpio(s)');
                    }*/
                }

                // search next gpio to configure
                self.searchNextGpioToConfigure();
            }
            /*else if( pin.gpio && pin.assigned ) {
                toast.info('Gpio already assigned by ' + pin.owner +' module' );
            }*/
        };

        /**
         * Return pin data structure
         * (internal use)
         */
        self.__getPinData = function(pin, gpio, v5, v33, dnc, gnd, assigned, owner, name) {
            var selected = false;
            var color = null;

            if( name ) {
                var found = -1;
                // it's a gpio search if it's current specified configuration
                for( var i=0; i<$scope.selectedGpios.length; i++ ) {
                    if( $scope.selectedGpios[i].gpio===name ) {
                        found = i;
                        break;
                    }
                }

                if( found>=0 ) {
                    // current pin is part of current configuration, so disabled assignment
                    // but enable selected flag
                    assigned = false;
                    selected = true;
                    color = self.pinInfos[found].color;
                } else {
                    // pin is really already assigned else where, keep parameter assigned value
                    // and disable selected flag
                    selected = false;
                }
            }

            return {
                pin: pin,
                name: name,
                gpio: gpio,
                v5: v5,
                v33: v33,
                dnc: dnc,
                gnd: gnd,
                assigned: assigned,
                owner: owner,
                selected: selected,
                color: color
            };
        }

        /**
         * Fill odd pins line
         * @param pin: pin number
         * @param pinDesc: pin description (gpio name if pin is a gpio)
         * @param gpios: list of raspberry pi gpios
         */
        self.__fillOdds = function(pinNumber, pinData) {
            if( pinData.label.startsWith('GPIO') ) {
                // save gpio configuration
                self.odds.push(self.__getPinData(pinNumber, true, false, false, false, false, pinData.gpio.assigned, pinData.gpio.owner, pinData.label));
            } else if( pinData.label==='5V' ) {
                // save 5v pin
                self.odds.push(self.__getPinData(pinNumber, false, true, false, false, false, null, null, null));
            } else if( pinData.label==='3.3V' ) {
                // save 3.3v pin
                self.odds.push(self.__getPinData(pinNumber, false, false, true, false, false, null, null, null));
            } else if( pinData.label==='DNC' ) {
                // save do not connect pin
                self.odds.push(self.__getPinData(pinNumber, false, false, false, true, false, null, null, null));
            } else if( pinData.label==='GND' ) {
                // save gnd pin
                self.odds.push(self.__getPinData(pinNumber, false, false, false, false, true, null, null, null));
            }
        };

        /**
         * Fill even pins line
         * @param pin: pin number
         * @param pinDesc: pin description (gpio name if pin is a gpio)
         * @param gpios: list of raspberry pi gpios
         */
        self.__fillEvens = function(pinNumber, pinData) {
            if( pinData.label.startsWith('GPIO') ) {
                // save gpio configuration
                self.evens.push(self.__getPinData(pinNumber, true, false, false, false, false, pinData.gpio.assigned, pinData.gpio.owner, pinData.label));
            } else if( pinData.label==='5V' ) {
                // save 5v pin
                self.evens.push(self.__getPinData(pinNumber, false, true, false, false, false, null, null, null));
            } else if( pinData.label==='3.3V' ) {
                // save 3.3v pin
                self.evens.push(self.__getPinData(pinNumber, false, false, true, false, false, null, null, null));
            } else if( pinData.label==='DNC' ) {
                // save do not connect pin
                self.evens.push(self.__getPinData(pinNumber, false, false, false, true, false, null, null, null));
            } else if( pinData.label==='GND' ) {
                // save gnd pin
                self.evens.push(self.__getPinData(pinNumber, false, false, false, false, true, null, null, null));
            }
        };

        /**
         * Search next gpio to configure
         * Set current label (current gpio name) and current index (of component parameter)
         */
        self.searchNextGpioToConfigure = function() {
            var found = false;
            for( var i=0; i<$scope.selectedGpios.length; i++ ) {
                if( $scope.selectedGpios[i].gpio===null ) {
                    self.currentIndex = i;
                    self.currentLabel = $scope.selectedGpios[self.currentIndex].label;
                    found = true;
                    break;
                }
            }

            if( !found ) {
                self.currentLabel = 'All GPIOs are configured';
            }
        }

        /**
         * Controller init
         */
        self.init = function() {
            // reset
            self.countPins = 0;
            self.selectedPins = {};
            self.pinInfos = [];
            self.evens = [];
            self.odds = [];
            self.maxPins = $scope.selectedGpios.length;

            // prepare internal data
            for( var i=0; i<$scope.selectedGpios.length; i++ ) {
                if( $scope.selectedGpios[i].gpio!==null ) {
                    // select already configured pin
                    self.selectedPins[$scope.selectedGpios[i].gpio] = null;

                    // increase counter of configured pins
                    self.countPins++;
                }

                // add new infos for pin
                self.pinInfos.push({
                    label: $scope.selectedGpios[i].label,
                    color: self.colors[i]
                });
            }
            self.searchNextGpioToConfigure();

            // fill pins
            return gpiosService.getPinsUsage()
                .then(function(pins) {
                    for( pinNumber in pins.data ) {
                        if( pinNumber % 2 ) {
                            self.__fillOdds(pinNumber, pins.data[pinNumber]);
                        } else {
                            self.__fillEvens(pinNumber, pins.data[pinNumber]);
                        }
                    }
                    self.evens.reverse();
                    self.odds.reverse();
                });
        };

        $scope.$watch('selectedGpios', function(newValue, oldValue) {
            if( newValue!=oldValue && newValue ) {
                self.init();
            }
        });

    }];

    var gpiosPinsLink = function(scope, element, attrs, controller) {
        if( !angular.isArray(scope.selectedGpios) ) {
            scope.selectedGpios = [];
        }
        controller.maxPins = scope.selectedGpios.length;
        controller.readonly = scope.readonly; //.parseBool();
        controller.init();
    };

    return {
        restrict: 'AE',
        templateUrl: 'gpiosPins/gpiosPins.component.html',
        replace: true,
        scope: {
            selectedGpios: '=',
            readonly: '='
        },
        controller: gpiosPinsController,
        controllerAs: 'pinsCtl',
        link: gpiosPinsLink
    };

}]);

