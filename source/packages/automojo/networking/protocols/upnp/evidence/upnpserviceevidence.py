"""
.. module:: upnpserviceevidence
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module containing the UpnpServiceEvidence object.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>

"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import TYPE_CHECKING


import weakref


if TYPE_CHECKING:
    from automojo.networking.protocols.upnp.upnppresence import UpnpPresence


class UpnpServiceEvidence:
    
    def __init__(self, *, device: str, service: str, location: str, status: str, presence: "UpnpPresence"):
        self._device = device
        self._service = service
        self._location = location
        self._status = status
        self._presence_ref = weakref.ref(presence)
        return

    @property
    def device(self) -> str:
        return self._device
    
    @property
    def location(self) -> str:
        return self._location
    
    @property
    def presence(self) -> "UpnpPresence":
        """
            The :class:`UpnpPresence` object that is associated with this service evidence.
        """
        return self._presence_ref()

    @property
    def service(self) -> str:
        return self._service
    
    @property
    def status(self) -> str:
        return self._status
