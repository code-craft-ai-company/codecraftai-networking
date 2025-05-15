

from typing import Dict, List, Optional

from automojo.networking.protocols.upnp.description.specversion import SpecVersion
from automojo.networking.protocols.upnp.description.embeddeddevicedesc import EmbeddedDeviceDesc
from automojo.networking.protocols.upnp.description.icondesc import IconDesc
from automojo.networking.protocols.upnp.description.servicedesc import ServiceDesc

from automojo.networking.protocols.upnp.manufacturers.bose.description.bosedevicedetail import BoseDeviceDetail
from automojo.networking.protocols.upnp.manufacturers.bose.description.bosemultiroomversions import BoseMultiRoomVersions

class BoseEmbeddedDeviceDetail(BoseDeviceDetail):
    """
        The BoseEmbeddedDeviceDetail object is a specialized version of the BoseDeviceDetail object that
        is used to represent embedded devices.  Embedded devices are devices that are not directly
        accessible on the network, but are instead accessed through another device.
    """
    
    def __init__(self, *, specVersion: SpecVersion, deviceType: str, friendlyName: str, manufacturer: str, modelName: str, UDN: str,
                 mac_addr: str, generation: str, codename: str, color: str, software_version: str, multi_room: BoseMultiRoomVersions,
                 modelNumber: str="", serialNumber: str="", manufacturerURL: str="", modelDescription: str = "", modelURL: str = "",
                 UPC: str="", presentationURL: str="", iconList: Optional[List[IconDesc]] = None, serviceList: Optional[List[ServiceDesc]] = None,
                 deviceList: Optional[List['EmbeddedDeviceDesc']] = None, **extra: Dict[str, str]):
        
        super().__init__(specVersion=specVersion, deviceType=deviceType, friendlyName=friendlyName,
                         manufacturer=manufacturer, modelName=modelName,
                         modelNumber=modelNumber, serialNumber=serialNumber,
                         UDN=UDN, mac_addr=mac_addr, generation=generation,
                         codename=codename, color=color,
                         software_version=software_version,
                         multi_room=multi_room,
                         manufacturerURL=manufacturerURL,
                         modelDescription=modelDescription,
                         modelURL=modelURL,
                         UPC=UPC,
                         presentationURL=presentationURL,
                         iconList=iconList,
                         serviceList=serviceList,
                         deviceList=deviceList,
                         locationURL=None,
                         **extra)
        return

