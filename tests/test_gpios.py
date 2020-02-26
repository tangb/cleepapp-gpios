import unittest
import logging
import time
import sys, os
import shutil
sys.path.append('../')
from backend.gpios import Gpios, GpioInputWatcher
from raspiot.utils import InvalidParameter, MissingParameter, CommandError, Unauthorized
from raspiot.libs.tests import session
import RPi.GPIO as GPIO

class TestGpioInputWatcher(unittest.TestCase):

    def setUp(self):
        self.session = session.TestSession(logging.ERROR)
        self.w = GpioInputWatcher(7, '123-456-789-123', self.__on_callback, self.__off_callback)
        self.on_cb_count = 0 
        self.off_cb_count = 0 

    def tearDown(self):
        if self.w and self.w.is_alive():
            self.w.stop()
            self.w.join()
        self.session.clean()

    def test_stop(self):
        self.w._get_input_level = self.__get_input_level_high
        self.w.start()
        time.sleep(1.0)
        self.w.stop()
        try:
            self.w.join(2.5)
        except:
            self.assertFalse(True, 'Thread should properly stop')

    def test_initial_level_off(self):
        w = GpioInputWatcher(7, '123-456-789-123', self.__on_callback, self.__off_callback, GPIO.LOW)
        w._get_input_level = self.__get_input_level_high
        w.start()
        time.sleep(0.25)
        self.assertEqual(self.on_cb_count, 0)
        self.assertEqual(self.off_cb_count, 1)
        w.stop()
        w.join()

    def test_initial_level_on(self):
        w = GpioInputWatcher(7, '123-456-789-123', self.__on_callback, self.__off_callback, GPIO.HIGH)
        w._get_input_level = self.__get_input_level_high
        w.start()
        time.sleep(0.25)
        self.assertEqual(self.on_cb_count, 1)
        self.assertEqual(self.off_cb_count, 0)
        w.stop()
        w.join()

    def test_callbacks(self):
        self.w._get_input_level = self.__get_input_level_high
        self.w.start()
        time.sleep(0.5)
        self.assertEqual(self.on_cb_count, 0)
        self.assertEqual(self.off_cb_count, 1)

        self.w._get_input_level = self.__get_input_level_low
        time.sleep(0.5)
        self.assertEqual(self.on_cb_count, 1)
        self.assertEqual(self.off_cb_count, 1)

        self.w._get_input_level = self.__get_input_level_high
        time.sleep(0.5)
        self.assertEqual(self.on_cb_count, 1)
        self.assertEqual(self.off_cb_count, 2)

        self.w._get_input_level = self.__get_input_level_low
        time.sleep(0.5)
        self.assertEqual(self.on_cb_count, 2)
        self.assertEqual(self.off_cb_count, 2)

    #MOCKS
    def __get_input_level_high(self):
        return GPIO.HIGH

    def __get_input_level_low(self):
        return GPIO.LOW

    def __on_callback(self, uuid):
        self.on_cb_count += 1

    def __off_callback(self, uuid, duration):
        self.off_cb_count += 1


class TestGpios(unittest.TestCase):

    def setUp(self):
        self.session = session.TestSession(logging.CRITICAL)
        self.module = self.session.setup(Gpios)
        self.module._gpio_setup = self.__gpio_setup
        self.configure_counter = 0
        self.deconfigure_counter = 0
        self.reconfigure_counter = 0
        self.original_configure_gpio = self.module._configure_gpio
        self.original_reconfigure_gpio = self.module._reconfigure_gpio
        self.original_deconfigure_gpio = self.module._deconfigure_gpio

        #patch GpioInputWatcher
        GpioInputWatcher._get_input_level = self.__get_input_level_high

    def tearDown(self):
        self.session.clean()

    def test_configure(self):
        pass

    def test_get_module_config(self):
        config = self.module.get_module_config()
        self.assertTrue(type(config) is dict, 'Get_module_config returns invalid output type (dict awaited)')
        self.assertTrue('pinsnumber' in config, '"pinsnumber" key does not exist in config')
        self.assertTrue(type(config['pinsnumber']) is int, 'Config pinsnumber is not int')
        self.assertTrue('revision' in config, '"revision" key does not exist in config')
        self.assertTrue(type(config['revision']) is int, 'Config revision is not int')

    def test_get_pins_usage(self):
        usage = self.module.get_pins_usage()
        #logging.info(usage)
        self.assertTrue(type(usage) is dict, 'get_pins_usage returns invalid type, dict awaited')

        config = self.module.get_module_config()
        self.module._get_revision = lambda : 3
        usage = self.module.get_pins_usage()
        self.assertEqual(len(usage), 40, 'Number of pins usage is invalid, 40 awaited')
        for pin in usage.values():
            self.__check_pin(pin)

        config = self.module.get_module_config()
        self.module._get_revision = lambda : 2
        usage = self.module.get_pins_usage()
        self.assertEqual(len(usage), 26, 'Number of pins usage is invalid, 26 awaited')
        for pin in usage.values():
            self.__check_pin(pin)

        config = self.module.get_module_config()
        self.module._get_revision = lambda : 1
        usage = self.module.get_pins_usage()
        self.assertEqual(len(usage), 26, 'Number of pins usage is invalid, 26 awaited')
        for pin in usage.values():
            self.__check_pin(pin)

    def test_get_assigned_gpios(self):
        gpios = self.module.get_assigned_gpios()
        self.assertTrue(type(gpios) is list, 'get_assigned_gpios returns invalid data type')
        self.assertEqual(len(gpios), 0, 'Assigned gpios list should be empty')

        gpio = 'GPIO18'
        device = self.module.reserve_gpio('dummy', gpio, 'test', 'unittest')
        gpios = self.module.get_assigned_gpios()
        self.assertEqual(len(gpios), 1, 'Assigned gpios list should be equal to 1')
        self.assertEqual(gpios[0], gpio, 'Reserved gpio is invalid')

    def test_reserve_gpio(self):
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'usage': 'test',
            'owner': 'unittest'
        }
        device = self.module.reserve_gpio(data['name'], data['gpio'], data['usage'], data['owner'])
        self.assertTrue(type(device) is dict, 'reserve_gpio should return dict')
        self.assertEqual(device['pin'], 12, 'Device pin should be 12 (for gpio18)')
        self.assertEqual(device['inverted'], False, 'Device inverted value should be False')
        self.assertEqual(device['owner'], data['owner'], 'Device owner is invalid')
        self.assertEqual(device['gpio'], data['gpio'], 'Device gpio is invalid')
        self.assertTrue('uuid' in device, 'Device should have uuid field')
        self.assertEqual(device['on'], False, 'Device on value should be False')
        self.assertEqual(device['name'], data['name'], 'Device name is invalid')
        self.assertEqual(device['keep'], False, 'Device keep flag is invalid')
        self.assertEqual(device['subtype'], data['usage'], 'Device subtype is invalid')
        self.assertEqual(device['mode'], Gpios.MODE_RESERVED, 'Device mode is invalid')
        self.assertEqual(device['type'], 'gpio', 'Device type is invalid')

    def test_reserve_gpio_ko_adddevice(self):
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'usage': 'test',
            'owner': 'unittest'
        }
        self.module._add_device = lambda data: None

        with self.assertRaises(CommandError) as cm:
            self.module.reserve_gpio(data['name'], data['gpio'], data['usage'], data['owner'])
        self.assertEqual(cm.exception.message, 'Unable to add device', 'Should raise exception when add_device failed')

    def test_reserve_gpio_ko_parameters(self):
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'usage': 'test',
            'owner': 'unittest'
        }

        with self.assertRaises(MissingParameter) as cm:
            self.module.reserve_gpio(None, data['gpio'], data['usage'], data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "name" is missing')

        with self.assertRaises(MissingParameter) as cm:
            self.module.reserve_gpio('', data['gpio'], data['usage'], data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "name" is missing')

        with self.assertRaises(MissingParameter) as cm:
            self.module.reserve_gpio(data['name'], None, data['usage'], data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "gpio" is missing')

        with self.assertRaises(MissingParameter) as cm:
            self.module.reserve_gpio(data['name'], '', data['usage'], data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "gpio" is missing')

        with self.assertRaises(InvalidParameter) as cm:
            self.module.reserve_gpio(data['name'], 'GPIO50', data['usage'], data['owner'])
        self.assertEqual(cm.exception.message, 'Gpio "GPIO50" does not exist for this raspberry pi')

        with self.assertRaises(MissingParameter) as cm:
            self.module.reserve_gpio(data['name'], data['gpio'], None, data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "usage" is missing')

        with self.assertRaises(MissingParameter) as cm:
            self.module.reserve_gpio(data['name'], data['gpio'], '', data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "usage" is missing')

    def test_get_reserved_gpios(self):
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'usage': 'test',
            'owner': 'unittest'
        }
        device = self.module.reserve_gpio(data['name'], data['gpio'], data['usage'], data['owner'])
        reserveds  = self.module.get_reserved_gpios(data['usage'])
        self.assertTrue(type(reserveds) is list)
        self.assertEqual(len(reserveds), 1)
        self.assertEqual(reserveds[0]['uuid'], device['uuid'])

        device = self.module.reserve_gpio(data['name']+'1', 'GPIO19', data['usage'], data['owner'])
        reserveds  = self.module.get_reserved_gpios(data['usage'])
        self.assertEqual(len(reserveds), 2)

    def test_is_reserved_gpio(self):
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'usage': 'test',
            'owner': 'unittest'
        }
        device = self.module.reserve_gpio(data['name'], data['gpio'], data['usage'], data['owner'])
        self.assertTrue(self.module.is_reserved_gpio(data['gpio']), 'Gpio should be reserved')
        self.module.delete_gpio(device['uuid'], data['owner'])
        self.assertFalse(self.module.is_reserved_gpio(data['gpio']), 'Gpio should not be reserved after device deletion')

    def test_add_gpio_input(self):
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'mode': Gpios.MODE_INPUT,
            'keep': False,
            'inverted': False,
            'owner': 'unittest'
        }
        self.module._configure_gpio = self.__configure_gpio

        device = self.module.add_gpio(data['name'], data['gpio'], data['mode'], data['keep'], data['inverted'], data['owner'])
        self.assertTrue(type(device) is dict, 'add_gpio returns invalid data type')
        self.assertEqual(device['name'], data['name'], 'Device name is invalid')
        self.assertEqual(device['gpio'], data['gpio'], 'Device gpiois invalid')
        self.assertEqual(device['mode'], data['mode'], 'Device mode is invalid')
        self.assertEqual(device['keep'], data['keep'], 'Device keep is invalid')
        self.assertEqual(device['inverted'], data['inverted'], 'Device inverted is invalid')
        self.assertTrue('uuid' in device and len(device['uuid'])>0, 'Device has no uuid')
        self.assertTrue(device['uuid'] in self.module._input_watchers, 'No input watcher for device')
        self.assertTrue(self.module._input_watchers[device['uuid']].is_alive, 'No input watcher running for device')
        self.assertEqual(len(self.module.get_module_devices()), 1, 'Module should have 1 device stored')
        self.assertEqual(self.configure_counter, 1, 'configure_gpio should be called once')

    def test_add_gpio_output(self):
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'mode': Gpios.MODE_OUTPUT,
            'keep': False,
            'inverted': False,
            'owner': 'unittest'
        }
        self.module._configure_gpio = self.__configure_gpio

        device = self.module.add_gpio(data['name'], data['gpio'], data['mode'], data['keep'], data['inverted'], data['owner'])
        self.assertTrue(type(device) is dict, 'add_gpio returns invalid data type')
        self.assertEqual(device['name'], data['name'], 'Device name is invalid')
        self.assertEqual(device['gpio'], data['gpio'], 'Device gpiois invalid')
        self.assertEqual(device['mode'], data['mode'], 'Device mode is invalid')
        self.assertEqual(device['keep'], data['keep'], 'Device keep is invalid')
        self.assertEqual(device['inverted'], data['inverted'], 'Device inverted is invalid')
        self.assertTrue('uuid' in device and len(device['uuid'])>0, 'Device has no uuid')
        self.assertEqual(len(self.module._input_watchers), 0, 'No input watcher should run for output device')
        self.assertEqual(len(self.module.get_module_devices()), 1, 'Module should have 1 device stored')
        self.assertEqual(self.configure_counter, 1, 'configure_gpio should be called once')

    def test_add_gpio_ko_adddevice(self):
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'mode': Gpios.MODE_OUTPUT,
            'keep': False,
            'inverted': False,
            'owner': 'unittest'
        }
        self.module._add_device = lambda data: None

        with self.assertRaises(CommandError) as cm:
            self.module.add_gpio(data['name'], data['gpio'], data['mode'], data['keep'], data['inverted'], data['owner'])
        self.assertEqual(cm.exception.message, 'Unable to add device', 'Should raise exception when add_device failed')

    def test_add_gpio_ko_parameters(self):
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'mode': Gpios.MODE_INPUT,
            'keep': False,
            'inverted': False,
            'owner': 'unittest'
        }

        with self.assertRaises(MissingParameter) as cm:
            self.module.add_gpio(None, data['gpio'], data['mode'], data['keep'], data['inverted'], data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "name" is missing')

        with self.assertRaises(MissingParameter) as cm:
            self.module.add_gpio('', data['gpio'], data['mode'], data['keep'], data['inverted'], data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "name" is missing')

        with self.assertRaises(MissingParameter) as cm:
            self.module.add_gpio(data['name'], None, data['mode'], data['keep'], data['inverted'], data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "gpio" is missing')

        with self.assertRaises(MissingParameter) as cm:
            self.module.add_gpio(data['name'], '', data['mode'], data['keep'], data['inverted'], data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "gpio" is missing')

        with self.assertRaises(InvalidParameter) as cm:
            self.module.add_gpio(data['name'], 'GPIO50', data['mode'], data['keep'], data['inverted'], data['owner'])
        self.assertEqual(cm.exception.message, 'Gpio "GPIO50" does not exist for this raspberry pi')

        with self.assertRaises(MissingParameter) as cm:
            self.module.add_gpio(data['name'], data['gpio'], None, data['keep'], data['inverted'], data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "mode" is missing')

        with self.assertRaises(MissingParameter) as cm:
            self.module.add_gpio(data['name'], data['mode'], '', data['keep'], data['inverted'], data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "mode" is missing')

        with self.assertRaises(MissingParameter) as cm:
            self.module.add_gpio(data['name'], data['gpio'], data['mode'], None, data['inverted'], data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "keep" is missing')

        with self.assertRaises(InvalidParameter) as cm:
            self.module.add_gpio(data['name'], data['gpio'], data['mode'], '', data['inverted'], data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "keep" must be bool')

        with self.assertRaises(MissingParameter) as cm:
            self.module.add_gpio(data['name'], data['gpio'], data['mode'], data['keep'], None, data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "inverted" is missing')

        with self.assertRaises(InvalidParameter) as cm:
            self.module.add_gpio(data['name'], data['gpio'], data['mode'], data['keep'], '', data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "inverted" must be bool')

    def test_delete_gpio_input(self):
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'mode': Gpios.MODE_INPUT,
            'keep': False,
            'inverted': False,
            'owner': 'unittest'
        }
        self.module._deconfigure_gpio = self.__deconfigure_gpio

        device = self.module.add_gpio(data['name'], data['gpio'], data['mode'], data['keep'], data['inverted'], data['owner'])
        self.assertTrue(self.module.delete_gpio(device['uuid'], data['owner']), 'Device should be deleted')
        self.assertEqual(len(self.module.get_module_devices()), 0, 'Module should have device deleted')
        self.assertEqual(self.deconfigure_counter, 1, 'deconfigure_gpio should be called once')

    def test_delete_gpio_output(self):
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'mode': Gpios.MODE_OUTPUT,
            'keep': False,
            'inverted': False,
            'owner': 'unittest'
        }
        self.module._deconfigure_gpio = self.__deconfigure_gpio

        device = self.module.add_gpio(data['name'], data['gpio'], data['mode'], data['keep'], data['inverted'], data['owner'])
        self.assertTrue(self.module.delete_gpio(device['uuid'], data['owner']), 'Device should be deleted')
        self.assertEqual(len(self.module.get_module_devices()), 0, 'Module should have device deleted')
        self.assertEqual(self.deconfigure_counter, 1, 'deconfigure_gpio should be called once')

    def test_delete_gpio_ko_deletedevice(self):
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'mode': Gpios.MODE_INPUT,
            'keep': False,
            'inverted': False,
            'owner': 'unittest'
        }

        device = self.module.add_gpio(data['name'], data['gpio'], data['mode'], data['keep'], data['inverted'], data['owner'])
        self.assertTrue(self.module.delete_gpio(device['uuid'], data['owner']), 'Device should be deleted')
        self.assertEqual(len(self.module.get_module_devices()), 0, 'Module should have device deleted')

    def test_delete_gpio_bad_owner(self):
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'mode': Gpios.MODE_INPUT,
            'keep': False,
            'inverted': False,
            'owner': 'unittest'
        }
        self.module._deconfigure_gpio = self.__deconfigure_gpio

        device = self.module.add_gpio(data['name'], data['gpio'], data['mode'], data['keep'], data['inverted'], data['owner'])
        with self.assertRaises(Unauthorized) as cm:
            self.module.delete_gpio(device['uuid'], 'another_owner')
        self.assertEqual(cm.exception.message, 'Device can only be deleted by module which created it')

    def test_update_gpio(self):
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'mode': Gpios.MODE_INPUT,
            'keep': False,
            'inverted': False,
            'owner': 'unittest'
        }
        self.module._reconfigure_gpio = self.__reconfigure_gpio

        device = self.module.add_gpio(data['name'], data['gpio'], data['mode'], data['keep'], data['inverted'], data['owner'])
        device = self.module.update_gpio(device['uuid'], 'dummynew', True, True, 'unittest')
        self.assertTrue(type(device) is dict, 'update_gpio returns invalid data type')
        self.assertEqual(device['name'], 'dummynew', 'Device name is invalid')
        self.assertEqual(device['keep'], True, 'Device keep is invalid')
        self.assertEqual(device['inverted'], True, 'Device inverted is invalid')
        self.assertTrue(device['uuid'] in self.module._input_watchers, 'No input watcher for device')
        self.assertTrue(self.module._input_watchers[device['uuid']].is_alive, 'No input watcher running for device')
        self.assertEqual(len(self.module.get_module_devices()), 1, 'Module should have 1 device stored')
        self.assertEqual(self.reconfigure_counter, 1, 'reconfigure_gpio should be called once')

    def test_update_gpio_ko_updatedevice(self):
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'mode': Gpios.MODE_INPUT,
            'keep': False,
            'inverted': False,
            'owner': 'unittest'
        }
        self.module._update_device = lambda uuid, data: False

        device = self.module.add_gpio(data['name'], data['gpio'], data['mode'], data['keep'], data['inverted'], data['owner'])
        with self.assertRaises(CommandError) as cm:
            self.module.update_gpio(device['uuid'], 'dummynew', True, True, 'unittest')
        self.assertEqual(cm.exception.message, 'Unable to update device "%s"' % device['uuid'])

    def test_update_gpio_ko_parameters(self):
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'mode': Gpios.MODE_INPUT,
            'keep': False,
            'inverted': False,
            'owner': 'unittest'
        }
        device = self.module.add_gpio(data['name'], data['gpio'], data['mode'], data['keep'], data['inverted'], data['owner'])

        with self.assertRaises(MissingParameter) as cm:
            self.module.update_gpio(device['uuid'], None, data['keep'], data['inverted'], data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "name" is missing')

        with self.assertRaises(MissingParameter) as cm:
            self.module.update_gpio(device['uuid'], '', data['keep'], data['inverted'], data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "name" is missing')

        with self.assertRaises(MissingParameter) as cm:
            self.module.update_gpio(device['uuid'], data['name'], None, data['inverted'], data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "keep" is missing')

        with self.assertRaises(InvalidParameter) as cm:
            self.module.update_gpio(device['uuid'], data['name'], '', data['inverted'], data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "keep" must be bool')

        with self.assertRaises(MissingParameter) as cm:
            self.module.update_gpio(device['uuid'], data['name'], data['keep'], None, data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "inverted" is missing')

        with self.assertRaises(InvalidParameter) as cm:
            self.module.update_gpio(device['uuid'], data['name'], data['keep'], '', data['owner'])
        self.assertEqual(cm.exception.message, 'Parameter "inverted" must be bool')

    def test_turn_on(self):
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'mode': Gpios.MODE_OUTPUT,
            'keep': False,
            'inverted': False,
            'owner': 'unittest'
        }
        self.module._gpio_output = self.__gpio_output
        device = self.module.add_gpio(data['name'], data['gpio'], data['mode'], data['keep'], data['inverted'], data['owner'])

        calls = self.session.get_event_calls('gpios.gpio.on')
        self.module.turn_on(device['uuid'])
        self.assertEqual(self.session.get_event_calls('gpios.gpio.on'), calls+1, '"gpios.gpio.on" wasn\'t triggered')

    def test_turn_off(self):
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'mode': Gpios.MODE_OUTPUT,
            'keep': False,
            'inverted': False,
            'owner': 'unittest'
        }
        self.module._gpio_output = self.__gpio_output
        device = self.module.add_gpio(data['name'], data['gpio'], data['mode'], data['keep'], data['inverted'], data['owner'])

        calls = self.session.get_event_calls('gpios.gpio.off')
        self.module.turn_off(device['uuid'])
        self.assertEqual(self.session.get_event_calls('gpios.gpio.off'), calls+1, '"gpios.gpio.off" wasn\'t triggered')

    def test_is_on(self):
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'mode': Gpios.MODE_OUTPUT,
            'keep': True,
            'inverted': False,
            'owner': 'unittest'
        }
        self.module._gpio_output = self.__gpio_output
        device = self.module.add_gpio(data['name'], data['gpio'], data['mode'], data['keep'], data['inverted'], data['owner'])

        self.assertEqual(self.module.is_on(device['uuid']), False)

        self.module.turn_on(device['uuid'])
        self.assertEqual(self.module.is_on(device['uuid']), True)

    def test_reset_gpios(self):
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'mode': Gpios.MODE_OUTPUT,
            'keep': True,
            'inverted': False,
            'owner': 'unittest'
        }
        self.module._gpio_output = self.__gpio_output

        device1 = self.module.add_gpio('name1', 'GPIO18', data['mode'], data['keep'], data['inverted'], data['owner'])
        device2 = self.module.add_gpio('name2', 'GPIO19', data['mode'], data['keep'], data['inverted'], data['owner'])
        self.module.turn_on(device1['uuid'])
        self.module.turn_on(device2['uuid'])
        self.assertEqual(self.module.is_on(device1['uuid']), True)
        self.assertEqual(self.module.is_on(device2['uuid']), True)
        self.module.reset_gpios()
        self.assertEqual(self.module.is_on(device1['uuid']), False)
        self.assertEqual(self.module.is_on(device2['uuid']), False)
        


    #MOCKS
    def __configure_gpio(self, data):
        self.configure_counter += 1
        return self.original_configure_gpio(data)

    def __reconfigure_gpio(self, data):
        self.reconfigure_counter += 1
        return self.original_reconfigure_gpio(data)

    def __deconfigure_gpio(self, data):
        self.deconfigure_counter += 1
        return self.original_deconfigure_gpio(data)

    def __gpio_setup(self, pin, mode, initial=None, pull_up_down=None):
        return None

    def __gpio_output(self, pin, level):
        return None

    def __get_input_level_high(self):
        return GPIO.HIGH

    def __get_input_level_low(self):
        return GPIO.LOW

    def __check_pin(self, pin):
        self.assertTrue('gpio' in pin)
        self.assertTrue('label' in pin)
        if pin['label'].startswith('GPIO'):
            self.assertTrue(type(pin['gpio']) is dict)
            self.assertTrue('assigned' in pin['gpio'])
            self.assertTrue('owner' in pin['gpio'])

if __name__ == '__main__':
    unittest.main()

