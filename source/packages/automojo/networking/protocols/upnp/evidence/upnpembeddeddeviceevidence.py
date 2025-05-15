
__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from typing import Dict

from automojo.networking.protocols.upnp.evidence.upnpdeviceevidence import UpnpDeviceEvidence


class UpnpEmbeddedDeviceEvidence(UpnpDeviceEvidence):
    """
        The UpnpEmbeddedDeviceEvidence object is a specialized version of the UpnpDeviceEvidence object that
        is used to represent embedded devices.  Embedded devices are devices that are not directly
        accessible on the network, but are instead accessed through another device.
    """
    
    def __init__(self, *, usn: str, status: str, server: str, location: str, ip: str, other: Dict[str, str], presence):
        super().__init__(usn=usn, status=status, server=server, location=location, ip=ip, other=other, presence=presence)
        return

