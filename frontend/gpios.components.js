angular
.module('Cleep')
.component('configGpiosPins', {
    template: `
    <div layout="column" layout-align="start stretch" id="{{ $ctrl.clId }}" class="config-item">
        <config-item-desc
            layout="row" layout-align="start-center"
            cl-icon="$ctrl.clIcon" cl-icon-class="$ctrl.clIconClass"
            cl-title="$ctrl.clTitle" cl-subtitle="$ctrl.clSubtitle"
        ></config-item-desc>
        <div layout="column" layout-align="center end">
            <div layout="column" layout-align="center start" layout-padding>
                <div>
                    <span ng-if="!$ctrl.readonly && $ctrl.countPins!==$ctrl.maxPins" class="gpios-board-text">
                        Click on the pin on which you have connected "{{ $ctrl.currentLabel }}":
                    </span>
                    <span ng-if="!$ctrl.readonly && $ctrl.countPins===$ctrl.maxPins" class="gpios-board-text">
                        All pins are configured.
                    </span>
                    <span ng-if="$ctrl.readonly" class="gpios-board-text gpios-board-text-readonly">
                        Readonly: update disabled
                    </span>
                </div>

                <div class="gpios-board-rev{{ $ctrl.boardRevision }}">
                    <div class="gpios-pin-board-rev{{ $ctrl.boardRevision }}">
                        <div
                            ng-click="$ctrl.onClick(pin)" style="background-color: {{ pin.color }} !important;"
                            class="gpios-default-pin"
                            ng-repeat="pin in $ctrl.odds"
                            ng-class="{'gpios-pin-dnc':pin.dnc, 'gpios-pin-5v':pin.v5, 'gpios-pin-33v':pin.v33, 'gpios-pin-gnd':pin.gnd, 'gpios-pin-assigned':pin.assigned, 'gpios-pin-selected':pin.selected, 'gpios-pin-gpio':pin.gpio}"
                        >
                            <md-tooltip ng-if="pin.v33" md-direction="top">Pin#{{ pin.pin }} +3.3v</md-tooltip>
                            <md-tooltip ng-if="pin.v5" md-direction="top">Pin#{{ pin.pin }} +5.0v</md-tooltip>
                            <md-tooltip ng-if="pin.gnd" md-direction="top">Pin#{{ pin.pin }} Ground</md-tooltip>
                            <md-tooltip ng-if="pin.gpio && pin.owner" md-direction="top">Pin#{{ pin.pin }} {{ pin.name }} - Assigned by {{ pin.owner }}</md-tooltip>
                            <md-tooltip ng-if="pin.gpio && !pin.owner" md-direction="top">Pin#{{ pin.pin }} {{ pin.name }}</md-tooltip>
                            <md-tooltip ng-if="pin.dnc" md-direction="top">Pin#{{ pin.pin }} Do not use</md-tooltip>
                            <span ng-if="pin.v33">3.3</span>
                            <span ng-if="pin.v5">5</span>
                        </div>
                        <div
                            ng-click="$ctrl.onClick(pin)"
                            style="background-color: {{pin.color}} !important;"
                            class="gpios-default-pin"
                            ng-repeat="pin in $ctrl.evens"
                            ng-class="{'gpios-pin-dnc':pin.dnc, 'gpios-pin-5v':pin.v5, 'gpios-pin-33v':pin.v33, 'gpios-pin-gnd':pin.gnd, 'gpios-pin-assigned':pin.assigned, 'gpios-pin-selected':pin.selected, 'gpios-pin-gpio':pin.gpio}"
                        >
                            <md-tooltip ng-if="pin.v33" md-direction="bottom">Pin#{{ pin.pin }} +3.3v</md-tooltip>
                            <md-tooltip ng-if="pin.v5" md-direction="bottom">Pin#{{ pin.pin }} +5.0v</md-tooltip>
                            <md-tooltip ng-if="pin.gnd" md-direction="bottom">Pin#{{ pin.pin }} Ground</md-tooltip>
                            <md-tooltip ng-if="pin.gpio && pin.owner" md-direction="bottom">Pin#{{ pin.pin }} {{ pin.name }} - Assigned by {{ pin.owner }}</md-tooltip>
                            <md-tooltip ng-if="pin.gpio && !pin.owner" md-direction="bottom">Pin#{{ pin.pin }} {{ pin.name }}</md-tooltip>
                            <md-tooltip ng-if="pin.dnc" md-direction="bottom">Pin#{{ pin.pin }} Do not use</md-tooltip>
                            <span ng-if="pin.v33">3.3</span>
                            <span ng-if="pin.v5">5</span>
                        </div>
                    </div>
                </div>
    
                <div layout="row">
                    <div ng-repeat="info in $ctrl.pinInfos" layout="row">
                        <div style="background-color:{{ info.color }}; width:15px; height:15px; border-radius:50%; margin-right:5px;"></div>
                        <div>
                            <span class="gpios-board-text" ng-class="{'gpios-board-text-readonly': $ctrl.readonly}">{{ info.label }}</span>
                        </div>
                        <div style="width:15px;"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `,
    bindings: {
        clTitle: '@',
        clSubtitle: '@?',
        clId: '@?',
        clIcon: '@?',
        clIconClass: '@?',
        selectedGpios: '<',
        readonly: '<?',
    },
    controller: function (gpiosService, cleepService) {
        const ctrl = this;
        ctrl.countPins = 0;
        ctrl.selectedPins = {};
        ctrl.pinInfos = [];
        ctrl.evens = [];
        ctrl.odds = [];
        ctrl.maxPins = 0;
        // Yellow-Blue-Green-Lime-DeepOrange-BlueGrey-Brown-Cyan-Pink-Teal
        ctrl.colors = ['#FFEB3B', '#2196F3', '#4CAF50', '#CDDC39', '#FF5722', '#607D8B', '#795548', '#00BCD4', '#FF80AB', '#009688'];
        ctrl.boardRevision = 3;
        ctrl.currentIndex = -1;

        ctrl.$onInit = function () {
            cleepService.getModuleConfig('gpios')
                .then((config)=> {
                    console.log('config', config);
                    ctrl.boardRevision = config.revision;
                });
            gpiosService.getPinsUsage()
                .then(function(pins) {
                    for( pinNumber in pins.data ) {
                        if( pinNumber % 2 ) {
                            ctrl.__fillOdds(pinNumber, pins.data[pinNumber]);
                        } else {
                            ctrl.__fillEvens(pinNumber, pins.data[pinNumber]);
                        }
                    }
                    ctrl.evens.reverse();
                    ctrl.odds.reverse();
                });
        };

        ctrl.$onChanges = function (changes) {
            if (changes.selectedGpios?.currentValue) {
                ctrl.maxPins = changes.selectedGpios.currentValue.length;
                ctrl.prepareComponent();
            }
        };

        ctrl.prepareComponent = function () {
            for (const [index, selectedGpio] of ctrl.selectedGpios.entries()) {
                if (selectedGpio.gpio) {
                    // set pin is already attributed to
                    ctrl.selectedPins[selectedGpio.gpio] = null;
                    ctrl.countPins++;
                }

                // add infos for pin
                ctrl.pinInfos.push({
                    label: selectedGpio.label,
                    color: ctrl.colors[index],
                });
            }
            ctrl.searchNextGpioToConfigure();
        };

        ctrl.onClick = function(pin) {
            if (ctrl.readonly) { 
                return;
            }   

            if (pin.gpio && !pin.assigned) { 
                if (pin.selected) { 
                    // unselect pin
    
                    // delete entry in selected pin list
                    if (pin.pin in ctrl.selectedPins) { 
                        delete ctrl.selectedPins[pin.pin];
                    }   

                    // remove configuration in component parameter
                    for (let i=0; i<ctrl.selectedGpios.length; i++) { 
                        if (ctrl.selectedGpios[i].gpio === pin.name) { 
                            ctrl.selectedGpios[i].gpio = null;
                            break;
                        }   
                    }   

                    // unselect pin in widget
                    pin.selected = !pin.selected;

                    // and remove selected color
                    pin.color = null;

                    // finally decrease number of selected pins
                    ctrl.countPins--;
                } else {
                    // select pin
    
                    // is max number of selected pins already reached?
                    if (ctrl.countPins < ctrl.maxPins) { 
                        // max not reached yet
                        // add new entry in selected pin list
                        ctrl.selectedPins[pin.pin] = null;

                        // add configuration in component parameter
                        ctrl.selectedGpios[ctrl.currentIndex].gpio = pin.name;

                        // select pin and update color
                        pin.selected = !pin.selected;
                        pin.color = ctrl.pinInfos[ctrl.currentIndex].color;

                        // finally incrase number of selected pins
                        ctrl.countPins++;
                    }
                }

                // search next gpio to configure
                ctrl.searchNextGpioToConfigure();
            }
        };

        /**
         * Return pin data structure
         * (internal use)
         */
        ctrl.__getPinData = function(pin, gpio, v5, v33, dnc, gnd, assigned, owner, name) {
            var selected = false;
            var color = null;

            if (name) {
                let found = -1;
                // it's a gpio search if it's current specified configuration
                for (let i=0; i<ctrl.selectedGpios.length; i++) {
                    if (ctrl.selectedGpios[i].gpio === name) {
                        found = i;
                        break;
                    }
                }

                if (found >= 0) {
                    // current pin is part of current configuration, so disabled assignment
                    // but enable selected flag
                    assigned = false;
                    selected = true;
                    color = ctrl.pinInfos[found].color;
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
        };

        /**
         * Fill odd pins line
         * @param pin: pin number
         * @param pinDesc: pin description (gpio name if pin is a gpio)
         * @param gpios: list of raspberry pi gpios
         */
        ctrl.__fillOdds = function(pinNumber, pinData) {
            if (pinData.label.startsWith('GPIO')) {
                // save gpio configuration
                const data = ctrl.__getPinData(pinNumber, true, false, false, false, false, pinData.gpio.assigned, pinData.gpio.owner, pinData.label);
                ctrl.odds.push(data);
            } else if (pinData.label==='5V') {
                // save 5v pin
                const data = ctrl.__getPinData(pinNumber, false, true, false, false, false, null, null, null);
                ctrl.odds.push(data);
            } else if (pinData.label==='3.3V') {
                // save 3.3v pin
                const data = ctrl.__getPinData(pinNumber, false, false, true, false, false, null, null, null);
                ctrl.odds.push(data);
            } else if (pinData.label==='DNC') {
                // save do not connect pin
                const data = ctrl.__getPinData(pinNumber, false, false, false, true, false, null, null, null);
                ctrl.odds.push(data);
            } else if (pinData.label==='GND') {
                // save gnd pin
                const data = ctrl.__getPinData(pinNumber, false, false, false, false, true, null, null, null);
                ctrl.odds.push(data);
            }
        };

       /**
         * Fill even pins line
         * @param pin: pin number
         * @param pinDesc: pin description (gpio name if pin is a gpio)
         * @param gpios: list of raspberry pi gpios
         */
        ctrl.__fillEvens = function(pinNumber, pinData) {
            if (pinData.label.startsWith('GPIO')) {
                // save gpio configuration
                const data = ctrl.__getPinData(pinNumber, true, false, false, false, false, pinData.gpio.assigned, pinData.gpio.owner, pinData.label);
                ctrl.evens.push(data);
            } else if (pinData.label==='5V') {
                // save 5v pin
                const data = ctrl.__getPinData(pinNumber, false, true, false, false, false, null, null, null);
                ctrl.evens.push(data);
            } else if (pinData.label==='3.3V') {
                // save 3.3v pin
                const data = ctrl.__getPinData(pinNumber, false, false, true, false, false, null, null, null);
                ctrl.evens.push(data);
            } else if (pinData.label==='DNC') {
                // save do not connect pin
                const data = ctrl.__getPinData(pinNumber, false, false, false, true, false, null, null, null);
                ctrl.evens.push(data);
            } else if (pinData.label==='GND') {
                // save gnd pin
                const data = ctrl.__getPinData(pinNumber, false, false, false, false, true, null, null, null);
                ctrl.evens.push(data);
            }
        };

        /**
         * Search next gpio to configure
         * Set current label (current gpio name) and current index (of component parameter)
         */
        ctrl.searchNextGpioToConfigure = function() {
            var found = false;
            for (let i=0; i<ctrl.selectedGpios.length; i++) {
                if (ctrl.selectedGpios[i].gpio === null) {
                    ctrl.currentIndex = i;
                    ctrl.currentLabel = ctrl.selectedGpios[ctrl.currentIndex].label;
                    found = true;
                    break;
                }
            }

            if (!found) {
                ctrl.currentLabel = 'All GPIOs are configured';
            }
        }

    },
});

