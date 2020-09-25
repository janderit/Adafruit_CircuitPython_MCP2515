# SPDX-FileCopyrightText: Copyright (c) 2020 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""Python implementation of the CircuitPython core `canio` API"""
# pylint:disable=too-few-public-methods, invalid-name, redefined-builtin
import time


class Message:
    """A class representing a message to send on a `canio` bus
    """

    # pylint:disable=too-many-arguments,invalid-name,redefined-builtin
    def __init__(self, id, data, extended=False):
        """Create a `Message` to send

        Args:
            id (int): The numeric ID of the message
            data (bytes): The content of the message
            extended (bool): True if the
        Raises:
            AttributeError: If `data` of type `bytes` is not provided for a non-RTR message
            AttributeError: If `data` is larger than 8 bytes
        """

        self._data = None
        self.id = id
        self.data = data
        self.extended = extended

    @property
    def data(self):
        """The content of the message, or dummy content in the case of an rtr"""
        return self._data

    @data.setter
    def data(self, new_data):
        if (new_data is None) or (not (type(new_data) in [bytes, bytearray])):

            raise AttributeError(
                "non-RTR canio.Message must have a `data` argument of type `bytes`"
            )
        if len(new_data) > 8:
            raise AttributeError(
                "`canio.Message` object data must be of length 8 or less"
            )
        # self.rtr = False
        # self._data = new_data
        self._data = bytearray(new_data)


class RemoteTransmissionRequest:
    """RRTTTTRRRR
    """

    def __init__(self, id: int, length: int, *, extended: bool = False):
        """Construct a Message to send on a CAN bus

        Args:
            id (int): The numeric ID of the requested message
            length (int): The length of the requested message
            extended (bool, optional): True if the message has an extended identifier, False if it\
                has a standard identifier. Defaults to False.

        """
        self.id = id
        self.length = length
        self.extended = extended


class Listener:
    """Listens for a CAN message

        canio.Listener is not constructed directly, but instead by calling the `listen` method of a\
        canio.CAN object.
    """

    def __init__(self, bus_obj, timeout=1.0):
        self._timer = Timer()
        self._bus_obj = bus_obj
        self._read_timeout = None
        self.timeout = timeout

    @property
    def timeout(self):
        """The maximum amount of time in seconds that `read` or `readinto` will wait before giving\
            up"""
        return self._read_timeout

    @timeout.setter
    def timeout(self, timeout):
        self._read_timeout = float(timeout)

    def receive(self):
        """Receives a message. If after waiting up to self.timeout seconds if no message is\
        received, None is returned. Otherwise, a Message is returned."""
        self._timer.rewind_to(self._read_timeout)
        while not self._timer.expired:
            if self._bus_obj.unread_message_count == 0:
                continue
            return self._bus_obj.read_message()
        return None

    def in_waiting(self):
        """Returns the number of messages waiting"""
        return self._bus_obj.unread_message_count

    def __iter__(self):
        """Returns self, unless the object is deinitialized"""
        return self

    def __next__(self):
        """Receives a message, after waiting up to self.timeout seconds"""
        return self.receive()

    def deinit(self):
        """Deinitialize this object, freeing its hardware resources"""

    def __enter__(self):
        """Returns self, to allow the object to be used in a The with statement statement for\
            resource control"""
        return self

    def __exit__(self, unused1, unused2, unused3):
        """Calls deinit()"""
        self.deinit()


class BusState:
    """The state of the CAN bus """

    ERROR_ACTIVE = 0
    """The bus is in the normal (active) state"""

    ERROR_WARNING = 1
    """ The bus is in the normal (active) state, but a moderate number of\
        errors have occurred recently.

        NOTE: Not all implementations may use ERROR_WARNING. Do not rely on seeing ERROR_WARNING\
            before ERROR_PASSIVE.
    """

    ERROR_PASSIVE = 2
    """ The bus is in the passive state due to the number of errors that have occurred recently.

    This device will acknowledge packets it receives, but cannot transmit messages. If additional\
    errors occur, this device may progress to BUS_OFF. If it successfully acknowledges other\
    packets on the bus, it can return to ERROR_WARNING or ERROR_ACTIVE and transmit packets.
    """
    BUS_OFF = 3
    """ The bus has turned off due to the number of errors that have occurred recently. It must be \
    restarted before it will send or receive packets. This device will neither send or acknowledge \
    packets on the bus."""


class Match:
    """A class representing an ID pattern to match against
    """

    def __init__(self, address: int, *, mask: int = 0, extended: bool = False):
        """Describe CAN bus messages to match

    Construct a Match with the given properties.

    If mask is nonzero, then the filter is for any sender which matches all the nonzero bits in\
        mask. Otherwise, it matches exactly the given address. If extended is true then only\
            extended addresses are matched, otherwise only standard addresses are matched.

        Args:
            address (int): he address to match
            mask (int, optional): The optional mask of addresses to match. Defaults to 0.
            extended (bool, optional): True to match extended addresses, False to match standard\
                addresses.

        Returns:
            [type]: [description]
        """
        self.address = address
        self.mask = mask
        self.extended = extended


############# non-api classes and methods
class Timer:
    """A class to track timeouts, like an egg timer
    """

    def __init__(self, timeout=0.0):
        self._timeout = None
        self._start_time = None
        if timeout:
            self.rewind_to(timeout)

    @property
    def expired(self):
        """Returns the expiration status of the timer

        Returns:
            bool: True if more than `timeout` seconds has past since it was set
        """
        return (time.monotonic() - self._start_time) > self._timeout

    def rewind_to(self, new_timeout):
        """Re-wind the timer to a new timeout and start ticking"""
        self._timeout = float(new_timeout)
        self._start_time = time.monotonic()
