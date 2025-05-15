"""
.. module:: upnpdeviceevidence
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module containing the UpnpDeviceEvidence object which profides basic contact information about
               the presence of a UPNP device that is available on the network.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>

"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from typing import Dict, TYPE_CHECKING

import weakref

from datetime import datetime

if TYPE_CHECKING:
    from automojo.networking.protocols.upnp.upnppresence import UpnpPresence


class UpnpDeviceEvidence:
    """
        A :class:`UpnpDeviceEvidence` object is an object used to track evidence of the current state of UPnP devices on a network.
    """

    def __init__(self, *, usn: str, status: str, server: str, location: str, ip: str, other: Dict[str, str], presence: "UpnpPresence"):
        self._usn = usn
        self._status = status
        self._server = server
        self._location = location
        self._ip = ip
        self._other = other
        self._presence_ref = weakref.ref(presence)
        self._timestamp = datetime.now()
        return
    
    @property
    def location(self) -> str:
        """
            The location of the device on the network.  This is typically a URL that can be used to access
            the device's web interface or API.
        """
        return self._location
    
    @property
    def other(self) -> Dict[str, str]:
        """
            A dictionary of other information about the device.  This can include things like the device's
            manufacturer, model number, and other metadata.
        """
        return self._other
    
    @property
    def ip(self) -> str:
        """
            The IP address of the device on the network.  This is typically a string in the format
        """
        return self._ip

    @property
    def presence(self) -> "UpnpPresence":
        """
            The UpnpPresence object that recognized the device on the network and created this evidence object.
        """
        return self._presence_ref()

    @property
    def server(self) -> str:
        """
            The server that is hosting the device.  This is typically a string that identifies the server
            software and version number.
        """
        return self._server

    @property
    def status(self) -> str:
        """
            The status of the device.  This is typically a string that indicates whether the device is
            online or offline.
        """
        return self._status

    @property
    def timestamp(self) -> datetime:
        """
            The timestamp of when this evidence of the devices state was created.
        """
        return self._timestamp

    @property
    def usn(self) -> str:
        """
            The USN (Unique Service Name) of the device.  This is typically a string that uniquely identifies
            the device on the network.
        """
        return self._usn