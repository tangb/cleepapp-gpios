#!/usr/bin/env python
# -*- coding: utf-8 -*-
    
import os
import logging
import glob
import uuid as moduuid
import json
import time
import uptime
from threading import Lock, Thread
import RPi.GPIO as GPIO
from raspiot.utils import InvalidParameter, Unauthorized, MissingParameter, CommandError
from raspiot.raspiot import RaspIotModule

__all__ = [u'Gpios']


class GpioInputWatcher(Thread):
    """
    Class that watches for changes on specified input pin
    We don't use GPIO lib implemented threaded callback due to a bug when executing a timer within callback function.

    Note:
        This object doesn't configure pin!
    """

    DEBOUNCE = 0.20

    def __init__(self, pin, uuid, on_callback, off_callback, level=GPIO.LOW):
        """
        Constructor

        Params: 
            pin (int): gpio pin number
            uuid (string): device uuid
            on_callback (function): on callback
            off_callback (function): off callback
            level (GPIO.LOW|GPIO.HIGH): triggered level
        """
        #init
        Thread.__init__(self)
        Thread.daemon = True
        self.logger = logging.getLogger(self.__class__.__name__)
        #self.logger.setLevel(logging.DEBUG)
        self.__debug_pin = None
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

    def run(self):
        """
        Run watcher
        """
        last_level = None
        time_on = 0

        #send current level
        if self.level==GPIO.LOW:
            if self.off_callback:
                self.off_callback(self.uuid, 0)
        else:
            if self.on_callback:
                self.on_callback(self.uuid)

        try:
            while self.continu:
                #get level
                level = GPIO.input(self.pin)
                if self.pin==self.__debug_pin:
                    self.logger.debug(u'thread=%s level=%s last_level=%s' % (unicode(self.ident), unicode(level), unicode(last_level)))

                if last_level is None:
                    #first run, nothing to do except init values
                    pass

                elif level!=last_level and level==self.level:
                    if self.pin==self.__debug_pin:
                        self.logger.debug(u'input %s on' % unicode(self.pin))
                    time_on = uptime.uptime()
                    self.on_callback(self.uuid)
                    time.sleep(self.debounce)

                elif level!=last_level:
                    if self.pin==self.__debug_pin:
                        self.logger.debug(u'input %s off' % unicode(self.pin))
                    if self.off_callback:
                        self.off_callback(self.uuid, uptime.uptime()-time_on)
                    time.sleep(self.debounce)

                else:
                    time.sleep(0.125)

                #update last level
                last_level = level
        except:
            self.logger.exception(u'Exception in GpioInputWatcher:')



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
class Gpios(RaspIotModule):
    """
    Raspberry pi gpios class
    """
    MODULE_AUTHOR = u'Cleep'
    MODULE_VERSION = u'1.0.0'
    MODULE_PRICE = 0
    MODULE_DEPS = []
    MODULE_DESCRIPTION = u'Configure your raspberry pins'
    MODULE_LONGDESCRIPTION = u'Gives you access to raspberry pins to configure your inputs/ouputs as you wish quickly and easily.'
    MODULE_TAGS = [u'gpios', u'inputs', u'outputs']
    MODULE_CATEGORY = u'DRIVER'
    MODULE_COUNTRY = None
    MODULE_URLINFO = u'https://github.com/tangb/cleepmod-gpios'
    MODULE_URLHELP = u'https://github.com/tangb/cleepmod-gpios/wiki'
    MODULE_URLSITE = None
    MODULE_URLBUGS = u'https://github.com/tangb/cleepmod-gpios/issues'

    MODULE_CONFIG_FILE = u'gpios.conf'

    GPIOS_REV1 = {u'GPIO0' : 3,
                  u'GPIO1' : 5,
                  u'GPIO4' : 7,
                  u'GPIO14': 8,
                  u'GPIO15': 10,
                  u'GPIO17': 11,
                  u'GPIO18': 12,
                  u'GPIO21': 13,
                  u'GPIO22': 15,
                  u'GPIO23': 16,
                  u'GPIO24': 18,
                  u'GPIO10': 19,
                  u'GPIO9' : 21,
                  u'GPIO25': 22,
                  u'GPIO11': 23,
                  u'GPIO8' : 24,
                  u'GPIO7' : 26
    }
    GPIOS_REV2 = {u'GPIO4' : 7,
                  u'GPIO17': 11,
                  u'GPIO18': 12,
                  u'GPIO22': 15,
                  u'GPIO23': 16,
                  u'GPIO24': 18,
                  u'GPIO25': 22,
                  u'GPIO27': 13,
                  u'GPIO2' : 3,
                  u'GPIO3' : 5,
                  u'GPIO7' : 26,
                  u'GPIO8' : 24,
                  u'GPIO9' : 21,
                  u'GPIO10': 19,
                  u'GPIO11': 23,
                  u'GPIO14': 8,
                  u'GPIO15': 10
    }
    GPIOS_REV3 = {u'GPIO5' : 29,
                  u'GPIO6' : 31,
                  u'GPIO12': 32,
                  u'GPIO13': 33,
                  u'GPIO26': 37,
                  u'GPIO0' : 27,
                  u'GPIO1' : 28,
                  u'GPIO19': 35,
                  u'GPIO16': 36,
                  u'GPIO20': 38,
                  u'GPIO21': 40
    }
    PINS_REV1 = {1 : u'3.3V',
                 2 : u'5V',
                 3 : u'GPIO0',
                 4 : u'5V',
                 5 : u'GPIO1',
                 6 : u'GND',
                 7 : u'GPIO4',
                 8 : u'GPIO14',
                 9 : u'GND',
                 10: u'GPIO15',
                 11: u'GPIO17',
                 12: u'GPIO18',
                 13: u'GPIO21',
                 14: u'GND',
                 15: u'GPIO22',
                 16: u'GPIO23',
                 17: u'3.3V',
                 18: u'GPIO24',
                 19: u'GPIO10',
                 20: u'GND',
                 21: u'GPIO9',
                 22: u'GPIO25',
                 23: u'GPIO11',
                 24: u'GPIO8',
                 25: u'GND',
                 26: u'GPIO7'
    }
    PINS_REV2 = {1 : u'3.3V',
                 2 : u'5V',
                 3 : u'GPIO2',
                 4 : u'5V',
                 5 : u'GPIO3',
                 6 : u'GND',
                 7 : u'GPIO4',
                 8 : u'GPIO14',
                 9 : u'GND',
                 10: u'GPIO15',
                 11: u'GPIO17',
                 12: u'GPIO18',
                 13: u'GPIO27',
                 14: u'GND',
                 15: u'GPIO22',
                 16: u'GPIO23',
                 17: u'3.3V',
                 18: u'GPIO24',
                 19: u'GPIO10',
                 20: u'GND',
                 21: u'GPIO9',
                 22: u'GPIO25',
                 23: u'GPIO11',
                 24: u'GPIO8',
                 25: u'GND',
                 26: u'GPIO7'
    }
    PINS_REV3 = {1: u'3.3V',
                 2: u'5V',
                 3: u'GPIO2',
                 4: u'5V',
                 5: u'GPIO3',
                 6: u'GND',
                 7: u'GPIO4',
                 8: u'GPIO14',
                 9: u'GND',
                 10: u'GPIO15',
                 11: u'GPIO17',
                 12: u'GPIO18',
                 13: u'GPIO27',
                 14: u'GND',
                 15: u'GPIO22',
                 16: u'GPIO23',
                 17: u'3.3V',
                 18: u'GPIO24',
                 19: u'GPIO10',
                 20: u'GND',
                 21: u'GPIO9',
                 22: u'GPIO25',
                 23: u'GPIO11',
                 24: u'GPIO8',
                 25: u'GND',
                 26: u'GPIO7',
                 27: u'DNC',
                 28: u'DNC',
                 29: u'GPIO5',
                 30: u'GND',
                 31: u'GPIO6',
                 32: u'GPIO12',
                 33: u'GPIO13',
                 34: u'GND',
                 35: u'GPIO19',
                 36: u'GPIO16',
                 37: u'GPIO26',
                 38: u'GPIO20',
                 39: u'GND',
                 40: u'GPIO21'
    }

    MODE_INPUT = u'input'
    MODE_OUTPUT = u'output'
    MODE_RESERVED = u'reserved'

    INPUT_DROP_THRESHOLD = 0.150 #in ms

    def __init__(self, bootstrap, debug_enabled):
        """
        Constructor

        Params:
            bootstrap (dict): bootstrap objects
            debug_enabled: debug status
        """
        RaspIotModule.__init__(self, bootstrap, debug_enabled)

        #members
        self.__input_watchers = {}

        #configure raspberry pi
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)

        #events
        self.gpios_gpios_off = self._get_event('gpios.gpio.off')
        self.gpios_gpios_on = self._get_event('gpios.gpio.on')

    def _configure(self):
        """
        Configure module
        """
        #configure gpios
        devices = self.get_module_devices()
        for uuid in devices:
            self._configure_gpio(devices[uuid])

    def _stop(self):
        """
        Stop module
        """
        #stop input watchers
        for uuid in self.__input_watchers:
            self.__input_watchers[uuid].stop()

        #cleanup gpios
        GPIO.cleanup()

    def __launch_input_watcher(self, device):
        """
        Launch input watcher for specified device

        Args:
            dict: device data
        """
        if not device[u'inverted']:
            watcher = GpioInputWatcher(device[u'pin'], device[u'uuid'], self.__input_on_callback, self.__input_off_callback, GPIO.LOW)
        else:
            watcher = GpioInputWatcher(device[u'pin'], device[u'uuid'], self.__input_on_callback, self.__input_off_callback, GPIO.HIGH)
        self.__input_watchers[device[u'uuid']] = watcher

    def _configure_gpio(self, device):
        """
        Configure GPIO (internal use)

        Params:
            device: device object
        
        Returns:
            bool: True if gpio is configured False otherwise
        """
        self.logger.debug('Configure gpio for device %s' % (device))

        #check if gpio is not reserved
        if device[u'mode']==self.MODE_RESERVED:
            self.logger.debug(u'Reserved gpio cannot be configured')
            return True

        try:
            #get gpio pin
            if device[u'mode']==self.MODE_OUTPUT:
                self.logger.debug(u'Configure gpio %s pin %d as OUTPUT' % (device[u'gpio'], device[u'pin']))
                #configure it
                if device[u'on']:
                    initial = GPIO.LOW
                    self.logger.debug(u'Event=%s initial=%s' % (u'gpios.gpio.on', str(initial)))
                    GPIO.setup(device[u'pin'], GPIO.OUT, initial=initial)

                    #and broadcast gpio status at startup
                    self.logger.debug(u'Broadcast event %s for gpio %s' % (u'gpios.gpio.on', device[u'gpio']))
                    self.gpios_gpios_on.send(params={u'gpio':u'gpio', u'init':True}, device_id=device[u'gpio'])

                else:
                    initial = GPIO.HIGH
                    self.logger.debug(u'Event=%s initial=%s' % (u'gpios.gpio.off', str(initial)))
                    GPIO.setup(device[u'pin'], GPIO.OUT, initial=initial)

                    #and broadcast gpio status at startup
                    self.logger.debug(u'Broadcast event %s for gpio %s' % (u'gpios.gpio.off', device[u'gpio']))
                    self.gpios_gpios_off.send(params={u'gpio':u'gpio', u'init':True, u'duration':0}, device_id=device[u'gpio'])

            elif device[u'mode']==self.MODE_INPUT:
                if not device[u'inverted']:
                    self.logger.debug(u'Configure gpio %s (pin %s) as INPUT' % (device[u'gpio'], device[u'pin']))
                else:
                    self.logger.debug(u'Configure gpio %s (pin %s) as INPUT inverted' % (device[u'gpio'], device[u'pin']))

                #configure it
                GPIO.setup(device[u'pin'], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

                #and launch input watcher
                self.__launch_input_watcher(device)

            return True

        except:
            self.logger.exception(u'Exception during GPIO configuration:')
            return False

    def _reconfigure_gpio(self, device):
        """
        Reconfigure specified gpio. A reconfiguration consists of stopping watcher and launch it again with new parameters

        Args:
            device (dict): device data

        Returns:
            bool: True if gpio reconfigured successfully, False otherwise
        """
        #stop watcher
        if self._deconfigure_gpio(device):
            #launch new watcher
            self.__launch_input_watcher(device)

        return True

    def _deconfigure_gpio(self, device):
        """
        Deconfigure device stopping its watcher

        Args:
            device (dict): device data

        Returns:
            bool: True if gpio deconfigured successfully, False otherwise
        """
        #get watcher
        if device[u'uuid'] not in self.__input_watchers:
            self.logger.warning(u'No gpio watcher found for device "%s"' % device)
            return False

        #stop and launch again watcher
        self.__input_watchers[device[u'uuid']].stop()
        del self.__input_watchers[device[u'uuid']]

        return True

    def __input_on_callback(self, uuid):
        """
        Callback when input is turned on (internal use)

        Params: 
            uuid (string): device uuid
        """
        self.logger.debug(u'on_callback for gpio %s triggered' % uuid)
        device = self._get_device(uuid)
        if device is None:
            raise Exception(u'Device %s not found' % uuid)

        #broadcast event
        self.gpios_gpios_on.send(params={u'gpio':device[u'gpio'], u'init':False}, device_id=uuid)

    def __input_off_callback(self, uuid, duration):
        """
        Callback when input is turned off

        Params: 
            uuid (string): device uuid
            duration (float): trigger duration
        """
        self.logger.debug(u'off_callback for gpio %s triggered' % uuid)
        device = self._get_device(uuid)
        if device is None:
            raise Exception(u'Device %s not found' % uuid)

        #broadcast event
        self.gpios_gpios_off.send(params={u'gpio':device[u'gpio'], u'init':False, u'duration':duration}, device_id=uuid)

    def get_module_config(self):
        """
        Return module full config

        Returns:
            dict: gpios configuration::
                {
                    gpios (dict): list of pin
                    revision (int): revision number (1|2|3)
                    pinsnumber (int): number of board pins
                }
        """
        config = {}

        config[u'revision'] = GPIO.RPI_INFO[u'P1_REVISION']
        config[u'pinsnumber'] = self.get_pins_number()

        return config

    def get_pins_usage(self):
        """
        Return pins usage

        Results:
            dict: dict of pins 
                {
                    <pin number (int)>:<gpio name|5v|3.3v|gnd|dnc(string)>
                }
        """
        output = {}

        #get pins descriptions according to raspberry pi revision
        all_pins = {}
        rev = GPIO.RPI_INFO['P1_REVISION']
        if rev==1:
            all_pins = self.PINS_REV1
        elif rev==2:
            all_pins = self.PINS_REV2
        elif rev==3:
            all_pins = self.PINS_REV3
        self.logger.debug(u'all_pins %s' % all_pins)

        #fill pins usage
        all_gpios = self.get_raspi_gpios()
        self.logger.debug(u'all_gpios %s' % all_gpios)
        devices = self.get_module_devices()
        for pin_number in all_pins:
            #default pin data
            output[pin_number] = {
                u'label': all_pins[pin_number],
                u'gpio': None
            }

            #fill gpio data
            if all_pins[pin_number] in all_gpios:
                gpio_name = all_pins[pin_number]
                gpio = all_gpios[gpio_name]
                assigned = False
                owner = None
                for uuid in devices:
                    if devices[uuid][u'gpio']==gpio_name:
                        assigned = True
                        owner = devices[uuid][u'owner']
                        break

                output[pin_number][u'gpio'] = {
                    u'assigned': assigned,
                    u'owner': owner
                }

        return output

    def get_assigned_gpios(self):
        """
        Return assigned gpios

        Returns:
            list: list of gpios
        """
        devices = self.get_module_devices()
        gpios = []
        for uuid in devices:
            gpios.append(devices[uuid][u'gpio'])
        
        return gpios

    def get_raspi_gpios(self):
        """
        Return available GPIO pins according to board revision

        Returns:
            dict: dict of gpios 
                {
                    <gpio name>, <pin number>
                }
        """
        rev = GPIO.RPI_INFO[u'P1_REVISION']

        if rev==1:
            return self.GPIOS_REV1
        if rev==2:
            return self.GPIOS_REV2
        elif rev==3:
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
        rev = GPIO.RPI_INFO[u'P1_REVISION']

        if rev==1 or rev==2:
            return 26
        elif rev==3:
            return 40

        return 0

    def reserve_gpio(self, name, gpio, usage, command_sender):
        """
        Reserve a gpio used to configure raspberry pi (ie onewire, lirc...)
        This action only flag this gpio as reserved to avoid using it again

        Params:
            name: name of gpio
            gpio: gpio value
            usage: describe gpio usage 
            command_sender: command request sender (used to set gpio in readonly mode)

        Returns:
            dict: Created gpio device

        Raises:
            CommandError, MissingParameter, InvalidParameter
        """
        #fix command_sender: rpcserver is the default gpio entry point
        if command_sender==u'rpcserver':
            command_sender = u'gpios'

        #search for gpio device
        found_gpio = self._search_device(u'gpio', gpio)

        #check values
        if not gpio:
            raise MissingParameter(u'Gpio parameter is missing')
        elif found_gpio is not None and found_gpio[u'mode']!=usage:
            raise InvalidParameter(u'Gpio is already reserved for "%s" usage' % found_gpio[u'mode'])
        elif found_gpio is not None and found_gpio[u'mode']==usage:
            return found_gpio
        elif not name:
            raise MissingParameter(u'Name parameter is missing')
        elif self._search_device(u'name', name) is not None:
            raise InvalidParameter(u'Name "%s" already used' % name)
        elif gpio not in self.get_raspi_gpios().keys():
            raise InvalidParameter(u'Gpio "%s" does not exist for this raspberry pi' % gpio)
        elif usage is None or len(usage)==0:
            raise MissingParameter(u'Parameter usage is missing')
        else:
            #gpio is valid, prepare new entry
            data = {
                u'name': name,
                u'mode': usage,
                u'pin': self.get_raspi_gpios()[gpio],
                u'gpio': gpio,
                u'keep': False,
                u'on': False,
                u'inverted': False,
                u'owner': command_sender,
                u'type': u'gpio',
                u'subtype': self.MODE_RESERVED
            }

            #add device
            self.logger.debug(u'data=%s' % data)
            device = self._add_device(data)
            if device is None:
                raise CommandError(u'Unable to add device')
    
            return device

    def get_reserved_gpio(self, usage):
        """
        Return reserved gpio for specified usage

        Args:
            usage (string): gpio reserved usage

        Returns:
            dict: gpio data. None if not found
        """
        if usage is None or len(usage)==0:
            raise MissingParameter(u'Parameter "usage" is missing')

        gpio = self._search_device(u'mode', usage)
        if gpio and gpio[u'subtype']==self.MODE_RESERVED:
            return gpio

        return None

    def is_reserved_gpio(self, uuid):
        """
        Return True if gpio is reserved

        Params:
            uuid (string): device uuid

        Returns:
            bool: True if gpio is reserved, False otherwise
        """
        device = self._get_device(uuid)
        if device is None:
            raise CommandError(u'Device %s not found' % uuid)

        self.logger.debug(u'is_reserved_gpio: %s' % device)
        if device[u'subtype']==self.MODE_RESERVED:
            return True

        return False

    def add_gpio(self, name, gpio, mode, keep, inverted, command_sender):
        """
        Add new gpio

        Params:
            name: name of gpio
            gpio: gpio value
            mode: mode (input or output)
            keep: keep state when restarting
            inverted: if true a callback will be triggered on gpio low level instead of high level
            command_sender: command request sender (used to set gpio in readonly mode)

        Returns:
            dict: created gpio device

        Raises:
            CommandError, MissingParameter, InvalidParameter
        """
        #fix command_sender: rpcserver is the default gpio entry point
        if command_sender==u'rpcserver':
            command_sender = u'gpios'

        #check values
        if not gpio:
            raise MissingParameter(u'Gpio parameter is missing')
        elif not name:
            raise MissingParameter(u'Name parameter is missing')
        elif not mode:
            raise MissingParameter(u'Mode parameter is missing')
        elif keep is None:
            raise MissingParameter(u'Keep parameter is missing')
        elif self._search_device(u'name', name) is not None:
            raise InvalidParameter(u'Name "%s" already used' % name)
        elif gpio not in self.get_raspi_gpios().keys():
            raise InvalidParameter(u'Gpio does not exist for this raspberry pi')
        elif mode not in (self.MODE_INPUT, self.MODE_OUTPUT):
            raise InvalidParameter(u'Mode "%s" is invalid' % mode)
        elif self._search_device(u'gpio', gpio) is not None:
            raise InvalidParameter(u'Gpio "%s" is already configured' % gpio)
        else:
            #gpio is valid, prepare new entry
            data = {
                u'name': name,
                u'mode': mode,
                u'pin': self.get_raspi_gpios()[gpio],
                u'gpio': gpio,
                u'keep': keep,
                u'on': inverted,
                u'inverted': inverted,
                u'owner': command_sender,
                u'type': 'gpio',
                u'subtype': mode
            }

            #add device
            device = self._add_device(data)
            if device is None:
                raise CommandError(u'Unable to add device')
    
            #configure it
            self._configure_gpio(device)

            return device

    def delete_gpio(self, uuid, command_sender):
        """
        Delete gpio

        Params:
            uuid: device identifier
            command_sender (string): command sender

        Returns:
            bool: True if device was deleted, False otherwise

        Raises:
            CommandError, MissingParameter, Unauthorized, InvalidParameter
        """
        #fix command_sender: rpcserver is the default gpio entry point
        if command_sender==u'rpcserver':
            command_sender = u'gpios'

        #check values
        if not uuid:
            raise MissingParameter(u'Uuid parameter is missing')
        device = self._get_device(uuid)
        if device is None:
            raise InvalidParameter(u'Device does not exist')
        elif device[u'owner']!=command_sender:
            raise Unauthorized(u'Device can only be deleted by module which created it')
        else:
            #device is valid, remove entry
            if not self._delete_device(uuid):
                raise CommandError(u'Failed to delete device "%s"' % device[u'uuid'])

            self._deconfigure_gpio(device)

        return True

    def update_gpio(self, uuid, name, keep, inverted, command_sender):
        """
        Update gpio

        Params:
            uuid (string): device identifier
            name (string): gpio name
            keep (bool): keep status flag
            inverted (bool): inverted flag
            command_sender (string): command sender

        Returns:
            bool: True if update was successfull, False otherwise

        Raises:
            CommandError, MissingParameter, Unauthorized, InvalidParameter
        """
        #fix command_sender: rpcserver is the default gpio entry point
        if command_sender==u'rpcserver':
            command_sender = u'gpios'

        #check values
        if not uuid:
            raise MissingParameter(u'Uuid parameter is missing')
        device = self._get_device(uuid)
        if device is None:
            raise InvalidParameter(u'Device does not exist')
        elif device[u'owner']!=command_sender:
            raise Unauthorized(u'Device can only be deleted by module that created it')
        else:
            #device is valid, update entry
            device[u'name'] = name
            device[u'keep'] = keep
            device[u'inverted'] = inverted
            if self._update_device(uuid, device)==None:
                raise CommandError(u'Unable to update device "%s"' % device[u'uuid'])

            #relaunch watcher
            self._reconfigure_gpio(device)

        return True

    def turn_on(self, uuid):
        """
        Turn on specified device

        Params:
            uuid (string): device identifier

        Returns:
            bool: True if command executed successfully
        """
        #check values
        device = self._get_device(uuid)
        if device is None:
            raise CommandError(u'Device not found')
        if device[u'mode']!=self.MODE_OUTPUT:
            raise CommandError(u'Gpio %s configured as %s cannot be turned on' % (device[u'uuid'], device[u'mode']))

        #turn on relay
        self.logger.debug(u'Turn on GPIO %s' % device[u'gpio'])
        GPIO.output(device[u'pin'], GPIO.LOW)

        #save current state
        device[u'on'] = True
        if device[u'keep']:
            self._update_device(uuid, device)

        #broadcast event
        self.gpios_gpios_on.send(params={u'gpio':device[u'gpio'], u'init':False}, device_id=uuid)

        return True

    def turn_off(self, uuid):
        """
        Turn off specified device

        Params:
            uuid (string): device identifier

        Returns:
            bool: True if command executed successfully

        Raises:
            CommandError
        """
        device = self._get_device(uuid)
        if device is None:
            raise CommandError(u'Device not found')
        if device[u'mode']!=self.MODE_OUTPUT:
            raise CommandError(u'Gpio %s configured as %s cannot be turned off' % (device[u'uuid'], device[u'mode']))
                
        #turn off relay
        self.logger.debug(u'Turn off GPIO %s' % device[u'gpio'])
        GPIO.output(device[u'pin'], GPIO.HIGH)

        #save current state
        device[u'on'] = False
        if device[u'keep']:
            self._update_device(uuid, device)

        #broadcast event
        self.gpios_gpios_off.send(params={u'gpio':device[u'gpio'], u'init':False, u'duration':0}, device_id=uuid)

        return True

    def is_on(self, uuid):
        """
        Return gpio status (on or off)

        Params:
            uuid (string): device identifier

        Returns:
            bool: True if device is on, False if device is off

        Raises:
            CommandError
        """
        #check values
        device = self._get_device(uuid)
        if device is None:
            raise CommandError(u'Device not found')
        if device[u'mode']==self.MODE_RESERVED:
            raise CommandError(u'Gpio %s configured as %s cannot be checked' % (device[u'uuid'], device[u'mode']))

        return device['on']

    def reset_gpios(self):
        """
        Reset all gpios turning them off
        """
        devices = self.get_module_devices()
        for uuid in devices:
            if devices[uuid][u'mode']==Gpios.MODE_OUTPUT:
                self.turn_off(uuid)


if __name__ == '__main__':
    #testu
    o = Gpios()
    print o.get_raspi_gpios()

