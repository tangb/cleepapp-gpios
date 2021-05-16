/**
 * Gpio widget
 * Display gpio dashboard widget
 */
angular
.module('Cleep')
.directive('gpioWidget', [
function() {

    var widgetGpioController = ['$scope', function($scope) {
        var self = this;
        self.device = $scope.device;
    }];

    return {
        restrict: 'EA',
        templateUrl: 'gpio.widget.html',
        replace: true,
        scope: {
            'device': '='
        },
        controller: widgetGpioController,
        controllerAs: 'widgetCtl'
    };
}]);

