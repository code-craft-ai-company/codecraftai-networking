
__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []
__version__ = "1.0.0"


from typing import List, Optional, TYPE_CHECKING

from automojo.networking.protocols.upnp.description.icondesc import IconDesc
from automojo.networking.protocols.upnp.description.servicedesc import ServiceDesc
from automojo.networking.protocols.upnp.description.specversion import SpecVersion

if TYPE_CHECKING:
    from automojo.networking.protocols.upnp.description.embeddeddevicedesc import EmbeddedDeviceDesc

def xml_format_basci1_device_desc(iconList: Optional[List[IconDesc]] = None, serviceList: Optional[List[ServiceDesc]] = None,
                                  deviceList: Optional[List["EmbeddedDeviceDesc"]] = None, indent: str = "") -> str:

    desc_lines = [
        f'{indent}<?xml version="1.0"?>'
        f'{indent}<root xmlns="urn:schemas-upnp-org:device-1-0">'
        f'{indent}    <specVersion>'
        f'{indent}        <major>1</major>'
        f'{indent}        <minor>0</minor>'
        f'{indent}    </specVersion>'
        f'{indent}    <URLBase>%(URLBase)s</URLBase>'
        f'{indent}    <device>'
        f'{indent}        <deviceType>urn:schemas-upnp-org:device:Basic:1</deviceType>'
        f'{indent}        <friendlyName>%(friendlyName)s</friendlyName>'
        f'{indent}        <manufacturer>%(manufacturer)s</manufacturer>'
        f'{indent}        <manufacturerURL>%(manufacturerURL)s</manufacturerURL>'
        f'{indent}        <modelDescription>%(modelDescription)s</modelDescription>'
        f'{indent}        <modelName>%(modelName)s</modelName>'
        f'{indent}        <modelNumber>%(modelNumber)s</modelNumber>'
        f'{indent}        <modelURL>%(modelURL)s</modelURL>'
        f'{indent}        <serialNumber>%(serialNumber)s</serialNumber>'
        f'{indent}        <UDN>%(UDN)s</UDN>'
        f'{indent}        <UPC>%(UPC)s</UPC>'
    ]

    if iconList is not None and len(iconList) > 0:
        desc_lines.extend([
            f'{indent}        <iconList>'
        ])
        
        icon_indent = indent + "    "
        for icon in iconList:
            desc_lines.append(icon.as_xml(indent=icon_indent))

        desc_lines.extend([
            f'{indent}        </iconList>'
        ])

    if serviceList is not None and len(serviceList) > 0:
        desc_lines.extend([
            f'{indent}        <serviceList>'
        ])
        
        service_indent = indent + "    "
        for service in serviceList:
            desc_lines.append(service.as_xml(indent=service_indent))

        desc_lines.extend([
            f'{indent}        </serviceList>'
        ])
    
    if deviceList is not None and len(deviceList) > 0:
        desc_lines.extend([
            f'{indent}        <deviceList>'
        ])
        
        device_indent = indent + "    "
        for device in deviceList:
            desc_lines.append(device.as_xml(indent=device_indent))

        desc_lines.extend([
            f'{indent}        </deviceList>'
        ])

    desc_lines.extend([
        f'{indent}        <presentationURL>%(presentationURL)s</presentationURL>'
        f'{indent}    </device>'
        f'{indent}</root>'
    ])

    desc = "\r\n".join(desc_lines)

    return desc


class Basic1DeviceDesc:
    """
        Class representing a UPnP Basic 1 device description.
    """

    def __init__(self, *, specVersion: SpecVersion, deviceType: str, friendlyName: str, manufacturer: str, modelName: str, UDN: str, 
                 modelNumber: str="", serialNumber: str="", manufacturerURL: str="", modelDescription: str = "", modelURL: str = "", UPC: str="", presentationURL: str="",
                 iconList: Optional[List[IconDesc]] = None, serviceList: Optional[List[ServiceDesc]] = None, deviceList: Optional[List['EmbeddedDeviceDesc']] = None,
                 locationURL: Optional[str]=None, **extras: dict):
        self.deviceType = deviceType
        self.specVersion = specVersion
        self.friendlyName = friendlyName
        self.manufacturer = manufacturer
        self.manufacturerURL = manufacturerURL
        self.modelDescription = modelDescription
        self.modelName = modelName
        self.modelNumber = modelNumber
        self.serialNumber = serialNumber
        self.UDN = UDN
        self.UPC = UPC
        self.modelURL = modelURL
        self.presentationURL = presentationURL

        self.iconList = iconList if iconList is not None else []
        self.deviceList = deviceList if deviceList is not None else []
        self.serviceList = serviceList if serviceList is not None else []
        
        self.locationURL = locationURL

        self.extras = extras
        return
    
    def add_icon(self, icon: "IconDesc"):
        """
            Add an icon to the device description.
        
            :param icon: IconDesc object representing the icon to be added.
        """
        self.iconList.append(icon)
        return
    
    def add_device(self, device: "EmbeddedDeviceDesc"):
        """
            Add an embedded device to the device description.
        
            :param device: EmbeddedDeviceInfo object representing the device to be added.
        """
        self.deviceList.append(device)
        return

    def add_service(self, service: "ServiceDesc"):
        """
            Add a service to the device description.
        
            :param service: ServiceInfo object representing the service to be added.
        """
        self.serviceList.append(service)
        return

    def as_xml(self, indent="") -> str:
        """
            Convert the Basic1DeviceDesc object to an XML string.
        
            :param indent: Indentation for the XML string.
            :returns: XML string representation of the Basic1DeviceDesc object.
        """
        
        desc = xml_format_basci1_device_desc(
            iconList=self.iconList,
            serviceList=self.serviceList,
            deviceList=self.deviceList,
            indent=indent
        )
        
        return desc
    
    def __str__(self) -> str:
        """
            Convert the Basic1DeviceDesc object to a string.
        
            :returns: String representation of the Basic1DeviceDesc object.
        """
        sval = f'Basic1DeviceDesc(friendlyName={self.friendlyName}, modelName={self.modelName}, modelNumber={self.modelNumber}, serialNumber={self.serialNumber}, UDN={self.UDN}, UPC={self.UPC}, presentationURL={self.presentationURL})'
        return sval
