import unittest
import logging
import time
import sys, os, copy
import shutil
sys.path.append('../')
from backend.gpios import Gpios, GpioInputWatcher
from cleep.exception import InvalidParameter, MissingParameter, CommandError, Unauthorized
from cleep.libs.tests import session
import RPi.GPIO as GPIO
from mock import Mock

class TestGpioInputWatcher(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.FATAL, format=u'%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s')
        self.session = session.TestSession(self)

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

    # MOCKS
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
        logging.basicConfig(level=logging.DEBUG, format=u'%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s')
        self.session = session.TestSession(self)

        self.configure_counter = 0
        self.deconfigure_counter = 0
        self.reconfigure_counter = 0

        # patch GpioInputWatcher
        GpioInputWatcher._get_input_level = self.__get_input_level_high

    def tearDown(self):
        self.session.clean()

    def init(self):
        self.module = self.session.setup(Gpios)
        self.module._gpio_setup = self.__gpio_setup
        self.original_configure_gpio = self.module._configure_gpio
        self.original_reconfigure_gpio = self.module._reconfigure_gpio
        self.original_deconfigure_gpio = self.module._deconfigure_gpio

        self.session.start_module(self.module)

    def get_device(self):
        """
        Return device
        """
        return copy.deepcopy({
            'name': 'dummy',
            'mode': 'output',
            'pin': 12,
            'gpio': 'GPIO18',
            'keep': False,
            'on': True,
            'inverted': False,
            'owner': 'unittest',
            'type': 'gpio',
            'subtype': 'output',
            'uuid': 'f0cbd7a2-4228-44a5-944f-e4d4d8d4d63d'
        })

    def test_configure_gpio_mode_reserved(self):
        self.init()
        device = self.get_device()
        device['mode'] = 'reserved'
        self.module._gpio_setup = Mock()
        self.module._Gpios__launch_input_watcher = Mock()

        self.assertTrue(self.module._configure_gpio(device))
        self.assertFalse(self.session.event_called('gpios.gpio.on'))
        self.assertFalse(self.module._Gpios__launch_input_watcher.called)

    def test_configure_gpio_mode_output_on(self):
        self.init()
        self.module._gpio_setup = Mock()
        self.module._Gpios__launch_input_watcher = Mock()
        device = self.get_device()
        device['mode'] = 'output'
        device['on'] = True
    
        self.assertTrue(self.module._configure_gpio(device))
        self.module._gpio_setup.assert_called_with(12, GPIO.OUT, initial=GPIO.LOW)
        self.session.assert_event_called_with('gpios.gpio.on', {'gpio': 'GPIO18', 'init': True}, device_id='f0cbd7a2-4228-44a5-944f-e4d4d8d4d63d')
        self.assertFalse(self.module._Gpios__launch_input_watcher.called)

    def test_configure_gpio_mode_output_off(self):
        self.init()
        self.module._gpio_setup = Mock()
        self.module._Gpios__launch_input_watcher = Mock()
        device = self.get_device()
        device['mode'] = 'output'
        device['on'] = False
    
        self.assertTrue(self.module._configure_gpio(device))
        self.module._gpio_setup.assert_called_with(12, GPIO.OUT, initial=GPIO.HIGH)
        self.session.assert_event_called_with('gpios.gpio.off', {'gpio': 'GPIO18', 'init': True, 'duration': 0}, device_id='f0cbd7a2-4228-44a5-944f-e4d4d8d4d63d')
        self.assertFalse(self.module._Gpios__launch_input_watcher.called)

    def test_configure_gpio_mode_input_on(self):
        self.init()
        self.module._gpio_setup = Mock()
        self.module._Gpios__launch_input_watcher = Mock()
        device = self.get_device()
        device['mode'] = 'input'
        device['on'] = True
    
        self.assertTrue(self.module._configure_gpio(device))
        self.module._gpio_setup.assert_called_with(12, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.assertFalse(self.session.event_called('gpios.gpio.on'))
        self.module._Gpios__launch_input_watcher.assert_called_with(device)

    def test_configure_gpio_mode_input_off(self):
        self.init()
        self.module._gpio_setup = Mock()
        self.module._Gpios__launch_input_watcher = Mock()
        device = self.get_device()
        device['mode'] = 'input'
        device['on'] = False
    
        self.assertTrue(self.module._configure_gpio(device))
        self.module._gpio_setup.assert_called_with(12, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.assertFalse(self.session.event_called('gpios.gpio.off'))
        self.module._Gpios__launch_input_watcher.assert_called_with(device)

    def test_configure_gpio_mode_exception(self):
        self.init()
        self.module._gpio_setup = Mock(side_effect=Exception('Test exception'))
        self.module._Gpios__launch_input_watcher = Mock()
        device = self.get_device()
        device['mode'] = 'input'
        device['on'] = False
    
        self.assertFalse(self.module._configure_gpio(device))
        self.assertFalse(self.session.event_called('gpios.gpio.off'))
        self.assertFalse(self.session.event_called('gpios.gpio.on'))
        self.assertFalse(self.module._Gpios__launch_input_watcher.called)

    def test_input_on_callback(self):
        self.init()
        device = self.get_device()
        self.module._get_device = Mock(return_value=device)

        self.module._Gpios__input_on_callback(device['uuid'])

        self.session.assert_event_called_with('gpios.gpio.on', {'gpio': 'GPIO18', 'init': False}, device_id='f0cbd7a2-4228-44a5-944f-e4d4d8d4d63d')

    def test_input_on_callback_invalid_params(self):
        self.init()
        self.module._get_device = Mock(return_value=None)

        with self.assertRaises(Exception) as cm:
            self.module._Gpios__input_on_callback('123456789')
        self.assertEqual(str(cm.exception), 'Device "123456789" not found')
        self.assertFalse(self.session.event_called('gpios.gpio.on'))

    def test_input_off_callback(self):
        self.init()
        device = self.get_device()
        self.module._get_device = Mock(return_value=device)

        self.module._Gpios__input_off_callback(device['uuid'], 666)

        self.session.assert_event_called_with('gpios.gpio.off', {'gpio': 'GPIO18', 'init': False, 'duration': 666}, device_id='f0cbd7a2-4228-44a5-944f-e4d4d8d4d63d')

    def test_input_off_callback_invalid_params(self):
        self.init()
        self.module._get_device = Mock(return_value=None)

        with self.assertRaises(Exception) as cm:
            self.module._Gpios__input_off_callback('123456789', 666)
        self.assertEqual(str(cm.exception), 'Device "123456789" not found')
        self.assertFalse(self.session.event_called('gpios.gpio.off'))

    def test_get_module_config(self):
        self.init()
        config = self.module.get_module_config()
        self.assertTrue(type(config) is dict, 'Get_module_config returns invalid output type (dict awaited)')
        self.assertTrue('pinsnumber' in config, '"pinsnumber" key does not exist in config')
        self.assertTrue(type(config['pinsnumber']) is int, 'Config pinsnumber is not int')
        self.assertTrue('revision' in config, '"revision" key does not exist in config')
        self.assertTrue(type(config['revision']) is int, 'Config revision is not int')

    def test_get_pins_usage(self):
        self.init()
        usage = self.module.get_pins_usage()
        # logging.info(usage)
        self.assertTrue(type(usage) is dict, 'get_pins_usage returns invalid type, dict awaited')

        config = self.module.get_module_config()
        self.module._get_revision = Mock(return_value=3)
        usage = self.module.get_pins_usage()
        self.assertEqual(len(usage), 40, 'Number of pins usage is invalid, 40 awaited')
        for pin in usage.values():
            self.__check_pin(pin)

        config = self.module.get_module_config()
        self.module._get_revision = Mock(return_value=2)
        usage = self.module.get_pins_usage()
        self.assertEqual(len(usage), 26, 'Number of pins usage is invalid, 26 awaited')
        for pin in usage.values():
            self.__check_pin(pin)

        config = self.module.get_module_config()
        self.module._get_revision = Mock(return_value=1)
        usage = self.module.get_pins_usage()
        self.assertEqual(len(usage), 26, 'Number of pins usage is invalid, 26 awaited')
        for pin in usage.values():
            self.__check_pin(pin)

    def test_get_pins_usage_with_owner(self):
        self.init()
        usage = self.module.get_pins_usage()
        # logging.info(usage)
        self.assertTrue(type(usage) is dict, 'get_pins_usage returns invalid type, dict awaited')
        self.module.add_gpio('test', 'GPIO18', 'input', False, False, 'testmod')

        config = self.module.get_module_config()
        self.module._get_revision = Mock(return_value=3)
        usage = self.module.get_pins_usage()
        # logging.debug('Usage: %s' % usage)

        gpio18 = usage[12]
        logging.debug('Gpio18: %s' % gpio18)
        self.assertEqual(gpio18['label'], 'GPIO18')
        self.assertEqual(gpio18['gpio']['assigned'], True)
        self.assertEqual(gpio18['gpio']['owner'], 'testmod')

    def test_get_assigned_gpios(self):
        self.init()
        gpios = self.module.get_assigned_gpios()
        self.assertTrue(type(gpios) is list, 'get_assigned_gpios returns invalid data type')
        self.assertEqual(len(gpios), 0, 'Assigned gpios list should be empty')

        gpio = 'GPIO18'
        device = self.module.reserve_gpio('dummy', gpio, 'test', 'unittest')
        gpios = self.module.get_assigned_gpios()
        self.assertEqual(len(gpios), 1, 'Assigned gpios list should be equal to 1')
        self.assertEqual(gpios[0], gpio, 'Reserved gpio is invalid')

    def test_get_raspi_gpios(self):
        self.init()
        self.module._get_revision = Mock()

        # rev 1
        self.module._get_revision.return_value = 1
        self.assertDictEqual(self.module.get_raspi_gpios(), self.module.GPIOS_REV1)

        # rev 2
        self.module._get_revision.return_value = 2
        self.assertDictEqual(self.module.get_raspi_gpios(), self.module.GPIOS_REV2)

        # rev 3
        self.module._get_revision.return_value = 3
        gpios = copy.deepcopy(self.module.GPIOS_REV2)
        gpios.update(self.module.GPIOS_REV3)
        self.assertDictEqual(self.module.get_raspi_gpios(), gpios)

        # invalid rev
        self.module._get_revision.return_value = 4
        self.assertDictEqual(self.module.get_raspi_gpios(), {})

    def test_get_pins_number(self):
        self.init()
        self.module._get_revision = Mock()

        # rev 1
        self.module._get_revision.return_value = 1
        self.assertEqual(self.module.get_pins_number(), 26)

        # rev 2
        self.module._get_revision.return_value = 2
        self.assertEqual(self.module.get_pins_number(), 26)

        # rev 3
        self.module._get_revision.return_value = 3
        self.assertEqual(self.module.get_pins_number(), 40)

        # invalid rev
        self.module._get_revision.return_value = 4
        self.assertEqual(self.module.get_pins_number(), 0)

    def test_reserve_gpio(self):
        self.init()
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
        self.init()
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

    def test_reserve_gpio_rpcserver_command_sender(self):
        self.init()
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'usage': 'test',
            'owner': 'rpcserver'
        }
        device = self.module.reserve_gpio(data['name'], data['gpio'], data['usage'], data['owner'])
        self.assertEqual(device['owner'], 'gpios', 'Device owner is invalid')

    def test_reserve_gpio_ko_parameters(self):
        self.init()
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
        self.assertEqual(str(cm.exception), 'Parameter "usage" is missing')

        self.module.reserve_gpio('onewire-sensor', 'GPIO18', 'onewire', 'test')
        with self.assertRaises(InvalidParameter) as cm:
            self.module.reserve_gpio(data['name'], data['gpio'], 'test', data['owner'])
        self.assertEqual(str(cm.exception), 'Gpio "GPIO18" is already reserved for "onewire" usage')

        with self.assertRaises(InvalidParameter) as cm:
            self.module.reserve_gpio('onewire-sensor', 'GPIO19', 'test', 'unittest')
        self.assertEqual(str(cm.exception), 'Name "onewire-sensor" is already used')

    def test_get_reserved_gpios(self):
        self.init()
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

    def test_get_reserved_gpios_return_same(self):
        self.init()
        data = {
            'name': 'dummy',
            'gpio': 'GPIO18',
            'usage': 'test',
            'owner': 'unittest'
        }
        device1 = self.module.reserve_gpio(data['name'], data['gpio'], data['usage'], data['owner'])
        device2 = self.module.reserve_gpio(data['name'], data['gpio'], data['usage'], data['owner'])
        self.assertEqual(device1, device2)

    def test_get_reserved_gpios_invalid_params(self):
        self.init()

        with self.assertRaises(MissingParameter) as cm:
            self.module.get_reserved_gpios(None)
        self.assertEqual(str(cm.exception), 'Parameter "usage" is missing')

    def test_is_reserved_gpio(self):
        self.init()
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
        self.init()
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
        self.assertTrue(isinstance(device, dict), 'add_gpio returns invalid data type')
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
        self.init()
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
        self.init()
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
        self.init()
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
        self.init()
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
        self.init()
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
        self.init()
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
        self.init()
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
        self.init()
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
        self.init()
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
        self.init()
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
        self.init()
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

        calls = self.session.event_call_count('gpios.gpio.on')
        self.module.turn_on(device['uuid'])
        self.assertEqual(self.session.event_call_count('gpios.gpio.on'), calls+1, '"gpios.gpio.on" wasn\'t triggered')

    def test_turn_off(self):
        self.init()
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

        calls = self.session.event_call_count('gpios.gpio.off')
        self.module.turn_off(device['uuid'])
        self.assertEqual(self.session.event_call_count('gpios.gpio.off'), calls+1, '"gpios.gpio.off" wasn\'t triggered')

    def test_is_on(self):
        self.init()
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
        self.init()
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
        


    # MOCKS
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
    # coverage run --omit="*/lib/python*/*","test_*" --concurrency=thread test_gpios.py; coverage report -m -i
    unittest.main()

