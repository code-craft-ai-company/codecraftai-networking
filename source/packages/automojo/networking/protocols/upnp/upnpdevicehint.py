

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from automojo.networking.protocols.upnp.evidence.upnpdeviceevidence import UpnpDeviceEvidence

class UpnpDeviceHint:
    """
        A class to represent a UPnP device hint.
    """

    def __init__(self, hint: str):
        """
        Initialize the UPnP device hint with device type and friendly name.

        :param device_type: The type of the UPnP device.
        :param friendly_name: The friendly name of the UPnP device.
        """
        self._hint = hint
        return
    
    def get_hint(self) -> str:
        """
            Get the hint that can be used to identify a Upnp device.

            :return: The hint for the UPnP device.
        """
        return self._hint

    def matches(self, exhibit: UpnpDeviceEvidence) -> bool:
        """
            Check if the hint provided by the user configuration matches the device exhibit.

            :param exhibit: The UPnP device exhibit to check against.

            :return: True if the hint matches the device exhibit, False otherwise.
        """
        rtnval = False

        if self._hint in exhibit.usn:
            rtnval = True

        return rtnval