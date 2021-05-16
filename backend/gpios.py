#!/usr/bin/env python
# -*- coding: utf-8 -*-

from threading import Thread
import logging
import time
import uptime
# pylint: disable=no-name-in-module
from RPi.GPIO import (
    LOW as GPIO_LOW,
    HIGH as GPIO_HIGH,
    BOARD as GPIO_BOARD,
    OUT as GPIO_OUT,
    IN as GPIO_IN,
    PUD_DOWN as GPIO_PUD_DOWN,
    RPI_INFO as GPIO_RPI_INFO,
)
# pylint: disable=no-name-in-module
from RPi.GPIO import (
    cleanup as GPIO_cleanup,
    setup as GPIO_setup,
    input as GPIO_input,
    output as GPIO_output,
    setmode as GPIO_setmode,
    setwarnings as GPIO_setwarnings,
)
from cleep.exception import InvalidParameter, Unauthorized, MissingParameter, CommandError
from cleep.core import CleepModule

__all__ = ['Gpios']

class GpioInputWatcher(Thread):
    """
    Class that watches for changes on specified input pin
    We don't use GPIO lib implemented threaded callback due to a bug when executing a timer within callback function.

    Note:
        This object doesn't configure pin!
    """

    DEBOUNCE = 0.20

    def __init__(self, pin, uuid, on_callback, off_callback, level=GPIO_LOW):
        """
        Constructor

        Args:
            pin (int): gpio pin number
            uuid (string): device uuid
            on_callback (function): on callback
            off_callback (function): off callback
            level (RPi.GPIO.LOW|RPi.GPIO.HIGH): triggered level
        """
        #init
        Thread.__init__(self)
        Thread.daemon = True
        self.logger = logging.getLogger('Gpios')
        #self.logger.setLevel(logging.DEBUG)
        self.uuid = uuid

        #members
        self.continu = True
        self.pin = pin
        self.level = level
        self.debounce = GpioInputWatcher.DEBOUNCE
        self.on_callback = on_callback
        self.off_callback = off_callback

    def stop(self):
        """
        Stop process
        """
        self.continu = False

    def _get_input_level(self): # pragma: no cover
        """
        Return input value

        Returns:
            (RPi.GPIO.HIGH | RPi.GPIO.LOW): input level
        """
        return GPIO_input(self.pin)

    def run(self):
        """
        Run watcher
        """
        last_level = None
        time_on = 0

        #send current level

        try:
            while self.continu:
                #get level
                level = self._get_input_level()

                if last_level is None:
                    #first iteration, send initial value
                    if self.level == GPIO_LOW:
                        self.off_callback(self.uuid, 0)
                    else:
                        self.on_callback(self.uuid)

                elif level != last_level and level == self.level:
                    self.logger.trace('Input %s on' % str(self.pin))
                    time_on = uptime.uptime()
                    self.on_callback(self.uuid)
                    time.sleep(self.debounce)

                elif level != last_level:
                    self.logger.trace('Input %s off' % str(self.pin))
                    self.off_callback(self.uuid, uptime.uptime()-time_on)
                    time.sleep(self.debounce)

                else:
                    time.sleep(0.125)

                #update last level
                last_level = level
        except Exception: # pragma: no cover
            self.logger.exception('Exception in GpioInputWatcher:')



# RASPI GPIO numbering scheme:
# @see http://raspi.tv/2013/rpi-gpio-basics-4-setting-up-rpi-gpio-numbering-systems-and-inputs
# GPIO#   Pin#  Dedicated I/O
# --------A/B----------------
# GPIO2   3
# GPIO3   5
# GPIO4   7     *
# GPIO14  8
# GPIO15  10
# GPIO17  11    *
# GPIO18  12    *
# GPIO27  13    *
# GPIO22  15    *
# GPIO23  16    *
# GPIO24  18    *
# GPIO10  19
# GPIO9   21
# GPIO25  22    *
# GPIO11  23
# GPIO8   24
# GPIO7   26
# -------A+/B+/B2/Zero/B3--------
# GPIO0   27
# GPIO1   28
# GPIO5   29    *
# GPIO6   31    *
# GPIO12  32    *
# GPIO13  33    *
# GPIO19  35
# GPIO16  36
# GPIO26  37    *
# GPIO20  38
# GPIO21  40
class Gpios(CleepModule):
    """
    Raspberry pi gpios class
    """
    MODULE_AUTHOR = 'Cleep'
    MODULE_VERSION = '1.1.0'
    MODULE_PRICE = 0
    MODULE_DEPS = []
    MODULE_DESCRIPTION = 'Configure your raspberry pins'
    MODULE_LONGDESCRIPTION = 'Gives you access to raspberry pins to configure your inputs/ouputs as you wish quickly and easily.'
    MODULE_TAGS = ['gpios', 'inputs', 'outputs']
    MODULE_CATEGORY = 'DRIVER'
    MODULE_COUNTRY = None
    MODULE_URLINFO = 'https://github.com/tangb/cleepmod-gpios'
    MODULE_URLHELP = 'https://github.com/tangb/cleepmod-gpios/wiki'
    MODULE_URLSITE = None
    MODULE_URLBUGS = 'https://github.com/tangb/cleepmod-gpios/issues'

    MODULE_CONFIG_FILE = 'gpios.conf'

    GPIOS_REV1 = {'GPIO0' : 3,
                  'GPIO1' : 5,
                  'GPIO4' : 7,
                  'GPIO14': 8,
                  'GPIO15': 10,
                  'GPIO17': 11,
                  'GPIO18': 12,
                  'GPIO21': 13,
                  'GPIO22': 15,
                  'GPIO23': 16,
                  'GPIO24': 18,
                  'GPIO10': 19,
                  'GPIO9' : 21,
                  'GPIO25': 22,
                  'GPIO11': 23,
                  'GPIO8' : 24,
                  'GPIO7' : 26
    }
    GPIOS_REV2 = {'GPIO4' : 7,
                  'GPIO17': 11,
                  'GPIO18': 12,
                  'GPIO22': 15,
                  'GPIO23': 16,
                  'GPIO24': 18,
                  'GPIO25': 22,
                  'GPIO27': 13,
                  'GPIO2' : 3,
                  'GPIO3' : 5,
                  'GPIO7' : 26,
                  'GPIO8' : 24,
                  'GPIO9' : 21,
                  'GPIO10': 19,
                  'GPIO11': 23,
                  'GPIO14': 8,
                  'GPIO15': 10
    }
    GPIOS_REV3 = {'GPIO5' : 29,
                  'GPIO6' : 31,
                  'GPIO12': 32,
                  'GPIO13': 33,
                  'GPIO26': 37,
                  'GPIO0' : 27,
                  'GPIO1' : 28,
                  'GPIO19': 35,
                  'GPIO16': 36,
                  'GPIO20': 38,
                  'GPIO21': 40
    }
    PINS_REV1 = {1 : '3.3V',
                 2 : '5V',
                 3 : 'GPIO0',
                 4 : '5V',
                 5 : 'GPIO1',
                 6 : 'GND',
                 7 : 'GPIO4',
                 8 : 'GPIO14',
                 9 : 'GND',
                 10: 'GPIO15',
                 11: 'GPIO17',
                 12: 'GPIO18',
                 13: 'GPIO21',
                 14: 'GND',
                 15: 'GPIO22',
                 16: 'GPIO23',
                 17: '3.3V',
                 18: 'GPIO24',
                 19: 'GPIO10',
                 20: 'GND',
                 21: 'GPIO9',
                 22: 'GPIO25',
                 23: 'GPIO11',
                 24: 'GPIO8',
                 25: 'GND',
                 26: 'GPIO7'
    }
    PINS_REV2 = {1 : '3.3V',
                 2 : '5V',
                 3 : 'GPIO2',
                 4 : '5V',
                 5 : 'GPIO3',
                 6 : 'GND',
                 7 : 'GPIO4',
                 8 : 'GPIO14',
                 9 : 'GND',
                 10: 'GPIO15',
                 11: 'GPIO17',
                 12: 'GPIO18',
                 13: 'GPIO27',
                 14: 'GND',
                 15: 'GPIO22',
                 16: 'GPIO23',
                 17: '3.3V',
                 18: 'GPIO24',
                 19: 'GPIO10',
                 20: 'GND',
                 21: 'GPIO9',
                 22: 'GPIO25',
                 23: 'GPIO11',
                 24: 'GPIO8',
                 25: 'GND',
                 26: 'GPIO7'
    }
    PINS_REV3 = {1: '3.3V',
                 2: '5V',
                 3: 'GPIO2',
                 4: '5V',
                 5: 'GPIO3',
                 6: 'GND',
                 7: 'GPIO4',
                 8: 'GPIO14',
                 9: 'GND',
                 10: 'GPIO15',
                 11: 'GPIO17',
                 12: 'GPIO18',
                 13: 'GPIO27',
                 14: 'GND',
                 15: 'GPIO22',
                 16: 'GPIO23',
                 17: '3.3V',
                 18: 'GPIO24',
                 19: 'GPIO10',
                 20: 'GND',
                 21: 'GPIO9',
                 22: 'GPIO25',
                 23: 'GPIO11',
                 24: 'GPIO8',
                 25: 'GND',
                 26: 'GPIO7',
                 27: 'DNC',
                 28: 'DNC',
                 29: 'GPIO5',
                 30: 'GND',
                 31: 'GPIO6',
                 32: 'GPIO12',
                 33: 'GPIO13',
                 34: 'GND',
                 35: 'GPIO19',
                 36: 'GPIO16',
                 37: 'GPIO26',
                 38: 'GPIO20',
                 39: 'GND',
                 40: 'GPIO21'
    }

    MODE_INPUT = 'input'
    MODE_OUTPUT = 'output'
    MODE_RESERVED = 'reserved'

    INPUT_DROP_THRESHOLD = 0.150 #in ms

    def __init__(self, bootstrap, debug_enabled):
        """
        Constructor

        Args:
            bootstrap (dict): bootstrap objects
            debug_enabled: debug status
        """
        CleepModule.__init__(self, bootstrap, debug_enabled)

        # members
        self._input_watchers = {}

        # configure raspberry pi
        GPIO_setmode(GPIO_BOARD)
        GPIO_setwarnings(False)

        # events
        self.gpios_gpio_off = self._get_event('gpios.gpio.off')
        self.gpios_gpio_on = self._get_event('gpios.gpio.on')

    def _gpio_setup(self, pin, mode, initial=None, pull_up_down=None): # pragma: no cover
        """
        Gpio setup

        Args:
            pin (number): pin number
            mode (?): pin mode
            initial (?): ?
            pull_up_mode (?): ?
        """
        if initial is None and pull_up_down is None:
            GPIO_setup(pin, mode)
        elif initial is None:
            GPIO_setup(pin, mode, pull_up_down=pull_up_down)
        elif pull_up_down is None:
            GPIO_setup(pin, mode, initial=initial)

    def _gpio_output(self, pin, level):
        """
        Set gpio output level

        Args:
            pin (int): pin number
            level (int): RPi.GPIO.LOW or RPi.GPIO.HIGH
        """
        GPIO_output(pin, level)

    def _configure(self):
        """
        Configure module
        """
        # configure gpios
        devices = self.get_module_devices()
        for uuid in devices:
            self._configure_gpio(devices[uuid])

    def _on_stop(self):
        """
        Stop module
        """
        # stop input watchers
        for uuid in self._input_watchers:
            self._input_watchers[uuid].stop()

        # cleanup gpios
        GPIO_cleanup()

    def __launch_input_watcher(self, device):
        """
        Launch input watcher for specified device

        Args:
            device (dict): device data
        """
        self.logger.debug('Launch input watcher for device "%s" (inverted=%s)' % (device['uuid'], device['inverted']))
        if not device['inverted']:
            watcher = GpioInputWatcher(
                device['pin'],
                device['uuid'],
                self.__input_on_callback,
                self.__input_off_callback,
                GPIO_LOW
            )
        else:
            watcher = GpioInputWatcher(
                device['pin'],
                device['uuid'],
                self.__input_on_callback,
                self.__input_off_callback,
                GPIO_HIGH
            )
        self._input_watchers[device['uuid']] = watcher
        watcher.start()

    def _configure_gpio(self, device):
        """
        Configure GPIO (internal use)

        Args:
            device (dict): device object

        Returns:
            bool: True if gpio is configured False otherwise
        """
        self.logger.debug('Configure gpio for device %s' % (device))

        # check if gpio is not reserved
        if device['mode'] == self.MODE_RESERVED:
            self.logger.debug('Reserved gpio cannot be configured')
            return True

        try:
            # get gpio pin
            if device['mode'] == self.MODE_OUTPUT:
                self.logger.debug('Configure gpio %s pin %d as OUTPUT' % (device['gpio'], device['pin']))
                # configure it
                if device['on']:
                    initial = GPIO_LOW
                    self.logger.debug('Event=%s initial=%s' % ('gpios.gpio.on', str(initial)))
                    self._gpio_setup(device['pin'], GPIO_OUT, initial=initial)

                    # and broadcast gpio status at startup
                    self.logger.debug('Broadcast event %s for gpio %s' % ('gpios.gpio.on', device['gpio']))
                    self.gpios_gpio_on.send(params={'gpio':device['gpio'], 'init':True}, device_id=device['uuid'])

                else:
                    initial = GPIO_HIGH
                    self.logger.debug('Event=%s initial=%s' % ('gpios.gpio.off', str(initial)))
                    self._gpio_setup(device['pin'], GPIO_OUT, initial=initial)

                    # and broadcast gpio status at startup
                    self.logger.debug('Broadcast event %s for gpio %s' % ('gpios.gpio.off', device['gpio']))
                    self.gpios_gpio_off.send(params={'gpio':device['gpio'], 'init':True, 'duration':0}, device_id=device['uuid'])

            elif device['mode'] == self.MODE_INPUT:
                if not device['inverted']:
                    self.logger.debug('Configure gpio %s (pin %s) as INPUT' % (device['gpio'], device['pin']))
                else:
                    self.logger.debug('Configure gpio %s (pin %s) as INPUT inverted' % (device['gpio'], device['pin']))

                # configure it
                self._gpio_setup(device['pin'], GPIO_IN, pull_up_down=GPIO_PUD_DOWN)

                # and launch input watcher
                self.__launch_input_watcher(device)

            return True

        except Exception:
            self.logger.exception('Exception during GPIO configuration:')
            return False

    def _reconfigure_gpio(self, device):
        """
        Reconfigure specified gpio. A reconfiguration consists of stopping watcher and launch it again with new parameters

        Args:
            device (dict): device data

        Returns:
            True if gpio reconfigured successfully, False otherwise
        """
        # stop watcher
        if self._deconfigure_gpio(device):
            # launch new watcher
            self.__launch_input_watcher(device)

        return True

    def _deconfigure_gpio(self, device):
        """
        Deconfigure device stopping its watcher

        Args:
            device (dict): device data

        Returns:
            True if gpio deconfigured successfully, False otherwise
        """
        if device['mode'] == self.MODE_OUTPUT:
            # nothing to deconfigure for output
            return True

        # get watcher
        if device['uuid'] not in self._input_watchers:
            self.logger.debug('No gpio watcher found for device "%s"' % device)
            return False

        # stop and launch again watcher
        self._input_watchers[device['uuid']].stop()
        del self._input_watchers[device['uuid']]

        return True

    def __input_on_callback(self, device_uuid):
        """
        Callback when input is turned on (internal use)

        Args:
            device_uuid (string): device uuid
        """
        self.logger.debug('on_callback for gpio %s triggered' % device_uuid)
        device = self._get_device(device_uuid)
        if device is None:
            raise Exception('Device "%s" not found' % device_uuid)

        # broadcast event
        self.gpios_gpio_on.send(params={'gpio':device['gpio'], 'init':False}, device_id=device_uuid)

    def __input_off_callback(self, device_uuid, duration):
        """
        Callback when input is turned off

        Args:
            device_uuid (string): device uuid
            duration (float): trigger duration
        """
        self.logger.debug('off_callback for gpio %s triggered' % device_uuid)
        device = self._get_device(device_uuid)
        if device is None:
            raise Exception('Device "%s" not found' % device_uuid)

        # broadcast event
        self.gpios_gpio_off.send(params={'gpio':device['gpio'], 'init':False, 'duration':duration}, device_id=device_uuid)

    def _get_revision(self):
        """
        Return raspberry pi revision

        Returns:
            int: raspberry pi revision number
        """
        return GPIO_RPI_INFO['P1_REVISION']

    def get_module_config(self):
        """
        Return module full config

        Returns:
            gpios configuration::

                {
                    revision (int): revision number (1|2|3)
                    pinsnumber (int): number of board pins
                }

        """
        config = {}

        config['revision'] = self._get_revision()
        config['pinsnumber'] = self.get_pins_number()

        return config

    def get_pins_usage(self):
        """
        Return pins usage

        Returns:
            dict: dict of pins::

                {
                    <pin number (int)>:<gpio name|5v|3.3v|gnd|dnc(string)>
                }

        """
        output = {}

        # get pins descriptions according to raspberry pi revision
        all_pins = {}
        rev = self._get_revision()
        if rev == 1:
            all_pins = self.PINS_REV1
        elif rev == 2:
            all_pins = self.PINS_REV2
        elif rev == 3:
            all_pins = self.PINS_REV3
        self.logger.debug('all_pins %s' % all_pins)

        # fill pins usage
        all_gpios = self.get_raspi_gpios()
        self.logger.debug('all_gpios %s' % all_gpios)
        devices = self.get_module_devices()
        for pin_number in all_pins:
            # default pin data
            output[pin_number] = {
                'label': all_pins[pin_number],
                'gpio': None
            }

            # fill gpio data
            if all_pins[pin_number] in all_gpios:
                gpio_name = all_pins[pin_number]
                assigned = False
                owner = None
                for uuid in devices:
                    if devices[uuid]['gpio'] == gpio_name:
                        assigned = True
                        owner = devices[uuid]['owner']
                        break

                output[pin_number]['gpio'] = {
                    'assigned': assigned,
                    'owner': owner
                }

        return output

    def get_assigned_gpios(self):
        """
        Return assigned gpios

        Returns:
            list: list of gpios
        """
        return [device['gpio'] for _, device in self.get_module_devices().items()]

    def get_raspi_gpios(self):
        """
        Return available GPIO pins according to board revision

        Returns:
            dict of gpios::

                {
                    <gpio name>: <pin number>
                }

        """
        rev = self._get_revision()

        if rev == 1:
            return self.GPIOS_REV1
        if rev == 2:
            return self.GPIOS_REV2
        if rev == 3:
            gpios = self.GPIOS_REV2.copy()
            gpios.update(self.GPIOS_REV3)
            return gpios

        return {}

    def get_pins_number(self):
        """
        Return pins number according to board revision

        Returns:
            int: pins number
        """
        rev = self._get_revision()

        if rev in (1, 2):
            return 26
        if rev == 3:
            return 40

        return 0

    def reserve_gpio(self, name, gpio, usage, command_sender):
        """
        Reserve a gpio used to configure raspberry pi (ie onewire, lirc...)
        This action only flag this gpio as reserved to avoid using it again

        Args:
            name (string): name of gpio
            gpio (string) : gpio value
            usage (string) : describe gpio usage
            command_sender (string): command request sender (used to set gpio in readonly mode)

        Returns:
            dict: Created gpio device

        Raises:
            CommandError
            MissingParameter
            InvalidParameter
        """
        # fix command_sender: rpcserver is the default gpio entry point
        if command_sender == 'rpcserver':
            command_sender = 'gpios'

        # search for gpio device
        found_gpio = self._search_device('gpio', gpio)

        # check values
        if not gpio:
            raise MissingParameter('Parameter "gpio" is missing')
        if found_gpio is not None and found_gpio['subtype'] != usage:
            raise InvalidParameter('Gpio "%s" is already reserved for "%s" usage' % (found_gpio['gpio'], found_gpio['subtype']))
        if found_gpio is not None and found_gpio['subtype'] == usage:
            return found_gpio
        if not name:
            raise MissingParameter('Parameter "name" is missing')
        if self._search_device('name', name) is not None:
            raise InvalidParameter('Name "%s" is already used' % name)
        if gpio not in self.get_raspi_gpios().keys():
            raise InvalidParameter('Gpio "%s" does not exist for this raspberry pi' % gpio)
        if usage is None or len(usage) == 0:
            raise MissingParameter('Parameter "usage" is missing')

        # gpio is valid, prepare new entry
        data = {
            'name': name,
            'mode': self.MODE_RESERVED,
            'pin': self.get_raspi_gpios()[gpio],
            'gpio': gpio,
            'keep': False,
            'on': False,
            'inverted': False,
            'owner': command_sender,
            'type': 'gpio',
            'subtype': usage
        }

        # add device
        self.logger.debug('data=%s' % data)
        device = self._add_device(data)
        if device is None:
            raise CommandError('Unable to add device')

        return device

    def get_reserved_gpios(self, usage):
        """
        Return reserved gpios for specified usage

        Args:
            usage (string): gpio reserved usage

        Returns:
            list: list of reserved gpios (full data)
        """
        if usage is None or len(usage) == 0:
            raise MissingParameter('Parameter "usage" is missing')

        gpios = self._search_devices('subtype', usage)
        return [gpio for gpio in gpios if gpio['mode'] == self.MODE_RESERVED]

    def is_reserved_gpio(self, gpio):
        """
        Return True if gpio is reserved

        Args:
            uuid (string): device uuid

        Returns:
            bool: True if gpio is reserved, False otherwise
        """
        device = self._search_device('gpio', gpio)
        if device is None:
            return False

        self.logger.debug('is_reserved_gpio: %s' % device)
        if device['mode'] == self.MODE_RESERVED:
            return True

        return False

    def add_gpio(self, name, gpio, mode, keep, inverted, command_sender):
        """
        Add new gpio

        Args:
            name: name of gpio
            gpio: gpio value
            mode: mode (input or output)
            keep: keep state when restarting
            inverted: if true a callback will be triggered on gpio low level instead of high level
            command_sender: command request sender (used to set gpio in readonly mode)

        Returns:
            dict: created gpio device

        Raises:
            CommandError
            MissingParameter
            InvalidParameter
        """
        # fix command_sender: rpcserver is the default gpio entry point
        if command_sender == 'rpcserver':
            command_sender = 'gpios'

        # check values
        if not gpio:
            raise MissingParameter('Parameter "gpio" is missing')
        if not name:
            raise MissingParameter('Parameter "name" is missing')
        if not mode:
            raise MissingParameter('Parameter "mode" is missing')
        if keep is None:
            raise MissingParameter('Parameter "keep" is missing')
        if inverted is None:
            raise MissingParameter('Parameter "inverted" is missing')
        if self._search_device('name', name) is not None:
            raise InvalidParameter('Name "%s" is already used' % name)
        if gpio not in self.get_raspi_gpios().keys():
            raise InvalidParameter('Gpio "%s" does not exist for this raspberry pi' % gpio)
        if mode not in (self.MODE_INPUT, self.MODE_OUTPUT):
            raise InvalidParameter('Parameter mode "%s" is invalid' % mode)
        if self._search_device('gpio', gpio) is not None:
            raise InvalidParameter('Gpio "%s" is already configured' % gpio)
        if not isinstance(keep, bool):
            raise InvalidParameter('Parameter "keep" must be bool')
        if not isinstance(inverted, bool):
            raise InvalidParameter('Parameter "inverted" must be bool')

        # gpio is valid, prepare new entry
        data = {
            'name': name,
            'mode': mode,
            'pin': self.get_raspi_gpios()[gpio],
            'gpio': gpio,
            'keep': keep,
            'on': inverted,
            'inverted': inverted,
            'owner': command_sender,
            'type': 'gpio',
            'subtype': mode
        }

        # add device
        device = self._add_device(data)
        if device is None:
            raise CommandError('Unable to add device')

        # configure it
        self._configure_gpio(device)

        return device

    def delete_gpio(self, device_uuid, command_sender):
        """
        Delete gpio

        Args:
            uuid: device identifier
            command_sender (string): command sender

        Returns:
            bool: True if device was deleted, False otherwise

        Raises:
            CommandError
            MissingParameter
            Unauthorized
            InvalidParameter
        """
        # fix command_sender: rpcserver is the default gpio entry point
        if command_sender == 'rpcserver':
            command_sender = 'gpios'

        # check values
        if not device_uuid:
            raise MissingParameter('Parameter "device_uuid" is missing')
        device = self._get_device(device_uuid)
        if device is None:
            raise InvalidParameter('Device "%s" does not exist' % device_uuid)
        if device['owner'] != command_sender:
            raise Unauthorized('Device can only be deleted by its owner')

        # device is valid, remove entry
        if not self._delete_device(device_uuid):
            raise CommandError('Failed to delete device "%s"' % device['uuid'])

        self._deconfigure_gpio(device)

        return True

    def update_gpio(self, device_uuid, name, keep, inverted, command_sender):
        """
        Update gpio

        Args:
            device_uuid (string): device identifier
            name (string): gpio name
            keep (bool): keep status flag
            inverted (bool): inverted flag
            command_sender (string): command sender

        Returns:
            dict: updated gpio device

        Raises:
            CommandError
            MissingParameter
            Unauthorized
            InvalidParameter
        """
        # fix command_sender: rpcserver is the default gpio entry point
        if command_sender == 'rpcserver':
            command_sender = 'gpios'

        # check values
        if not device_uuid:
            raise MissingParameter('Parameter "device_uuid" is missing')
        device = self._get_device(device_uuid)
        if device is None:
            raise InvalidParameter('Device "%s" does not exist' % device_uuid)
        if name is None or len(name) == 0:
            raise MissingParameter('Parameter "name" is missing')
        if keep is None:
            raise MissingParameter('Parameter "keep" is missing')
        if not isinstance(keep, bool):
            raise InvalidParameter('Parameter "keep" must be bool')
        if inverted is None:
            raise MissingParameter('Parameter "inverted" is missing')
        if not isinstance(inverted, bool):
            raise InvalidParameter('Parameter "inverted" must be bool')
        if device['owner'] != command_sender:
            raise Unauthorized('Device can only be updated by its owner')

        # device is valid, update entry
        device['name'] = name
        device['keep'] = keep
        device['inverted'] = inverted
        if not self._update_device(device_uuid, device):
            raise CommandError('Failed to update device "%s"' % device['uuid'])

        # relaunch watcher
        self._reconfigure_gpio(device)

        return device

    def turn_on(self, device_uuid):
        """
        Turn on specified device

        Args:
            device_uuid (string): device identifier

        Returns:
            bool: True if command executed successfully

        Raises:
            CommandError
        """
        # check values
        device = self._get_device(device_uuid)
        if device is None:
            raise CommandError('Device not found')
        if device['mode'] != self.MODE_OUTPUT:
            raise CommandError('Gpio "%s" configured as "%s" cannot be turned on' % (device['gpio'], device['mode']))

        # turn on relay
        self.logger.debug('Turn on GPIO %s' % device['gpio'])
        self._gpio_output(device['pin'], GPIO_LOW)

        # save current state
        device['on'] = True
        if device['keep']:
            self._update_device(device_uuid, device)

        # broadcast event
        self.gpios_gpio_on.send(params={'gpio':device['gpio'], 'init':False}, device_id=device_uuid)

        return True

    def turn_off(self, uuid):
        """
        Turn off specified device

        Args:
            uuid (string): device identifier

        Returns:
            bool: True if command executed successfully

        Raises:
            CommandError
        """
        device = self._get_device(uuid)
        if device is None:
            raise CommandError('Device not found')
        if device['mode'] != self.MODE_OUTPUT:
            raise CommandError('Gpio "%s" configured as "%s" cannot be turned off' % (device['gpio'], device['mode']))

        # turn off relay
        self.logger.debug('Turn off GPIO %s' % device['gpio'])
        self._gpio_output(device['pin'], GPIO_HIGH)

        # save current state
        device['on'] = False
        if device['keep']:
            self._update_device(uuid, device)

        # broadcast event
        self.gpios_gpio_off.send(params={'gpio':device['gpio'], 'init':False, 'duration':0}, device_id=uuid)

        return True

    def is_on(self, uuid):
        """
        Return gpio status (on or off)

        Args:
            uuid (string): device identifier

        Returns:
            bool: True if device is on, False if device is off

        Raises:
            CommandError
        """
        # check values
        device = self._get_device(uuid)
        if device is None:
            raise CommandError('Device not found')
        if device['mode'] == self.MODE_RESERVED:
            raise CommandError('Gpio "%s" configured as "%s" cannot be checked' % (device['gpio'], device['mode']))

        return device['on']

    def is_gpio_on(self, gpio):
        """
        Get value of specified gpio. Gpio doesn't have to be declared as device

        Args:
            gpio (string): gpio name

        Return:
            bool: True if gpio is on, False otherwise
        """
        # check values
        all_gpios = self.get_raspi_gpios()
        if gpio not in all_gpios.keys():
            raise InvalidParameter('Parameter "gpio" is invalid')

        pin = all_gpios[gpio]
        self.logger.debug('Read value for gpio "%s" (pin %s)' % (gpio, pin))

        return GPIO_input(pin) == GPIO_HIGH

    def reset_gpios(self):
        """
        Reset all gpios turning them off
        """
        devices = self.get_module_devices()
        for uuid in devices:
            if devices[uuid]['mode'] == Gpios.MODE_OUTPUT:
                self.turn_off(uuid)


