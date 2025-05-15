
__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []
__version__ = "1.0.0"

from typing import List, Optional

from automojo.networking.protocols.upnp.description.specversion import SpecVersion
from automojo.networking.protocols.upnp.description.icondesc import IconDesc
from automojo.networking.protocols.upnp.description.servicedesc import ServiceDesc

from automojo.networking.protocols.upnp.description.basic1devicedesc import Basic1DeviceDesc


class EmbeddedDeviceDesc(Basic1DeviceDesc):
    """
    EmbeddedDeviceDesc is a class that represents an embedded device description in UPnP.
    It inherits from Basic1DeviceDesc and adds additional attributes and methods specific to embedded devices.
    """

    def __init__(self, specVersion: SpecVersion, deviceType: str, friendlyName: str, manufacturer: str, modelName: str, modelNumber: str,
                 UDN: str, serialNumber: str="", manufacturerURL: str="", modelDescription: str = "", modelURL: str = "", UPC: str="",
                presentationURL: str="", iconList: Optional[List[IconDesc]] = None, serviceList: Optional[List[ServiceDesc]] = None,
                deviceList: Optional[List['EmbeddedDeviceDesc']] = None, **extras: dict):
        super().__init__(specVersion, deviceType, friendlyName, manufacturer, manufacturerURL,
                         modelDescription, modelName, modelNumber, modelURL,
                         serialNumber, UDN, UPC, deviceList=deviceList, iconList=iconList,
                         serviceList=serviceList, locationURL=None, **extras)
        return