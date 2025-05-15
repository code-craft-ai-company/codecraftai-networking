
__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Union

from automojo.networking.protocols.upnp.description.basic1devicedesc import Basic1DeviceDesc
from automojo.networking.protocols.upnp.evidence.upnpdeviceevidence import UpnpDeviceEvidence


class UpnpDeviceDetail:
    """
        Class to represent UPnP device details.
    """

    def __init__(self, evidence: UpnpDeviceEvidence, description: Union[Basic1DeviceDesc, None]):
        """
            Initialize the UPnP device details.

            :param device: The UPnP device object.
        """
        self._evidence = evidence
        self._description = description
        return
    
    @property
    def evidence(self) -> UpnpDeviceEvidence:
        """
            Get the UPnP device evidence from the las M-Search response or Notify message.

            :return: The UPnP device evidence.
        """
        return self._evidence
    
    @property
    def description(self) -> Union[Basic1DeviceDesc, None]:
        """
            Get the UPnP device description for the device or None if the device description was not available.

            :return: The last UPnP device description obtained for the device or None if a device description has not been obtained.
        """
        return self._description
    
