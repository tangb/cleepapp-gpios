#!/usr/bin/env python
# -*- coding: utf-8 -*-

from raspiot.libs.internals.event import Event

class GpiosGpioOnEvent(Event):
    """
    Gpios.gpio.on event
    """

    EVENT_NAME = u'gpios.gpio.on'
    EVENT_SYSTEM = False
    EVENT_PARAMS = [u'gpio', u'init']

    def __init__(self, bus, formatters_broker, events_broker):
        """
        Constructor

        Args:
            bus (MessageBus): message bus instance
            formatters_broker (FormattersBroker): formatters broker instance
            events_broker (EventsBroker): events broker instance
        """
        Event.__init__(self, bus, formatters_broker, events_broker)

