

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from typing import Any, Callable, Dict, List, Optional, Type

import logging

logger = logging.getLogger()

from xml.etree.ElementTree import Element

from automojo.networking.protocols.upnp.description.basic1devicedesc import Basic1DeviceDesc
from automojo.networking.protocols.upnp.description.embeddeddevicedesc import EmbeddedDeviceDesc
from automojo.networking.protocols.upnp.description.icondesc import IconDesc
from automojo.networking.protocols.upnp.description.servicedesc import ServiceDesc
from automojo.networking.protocols.upnp.description.specversion import SpecVersion


from automojo.networking.protocols.upnp.constants import (
    UPNP_DEVICE1_NAMESPACE_PREFIX,
    UPNP_DEVICE1_NAMESPACE_PREFIX_END
)

class DeviceDetailProcessor:
    """
        A :class:`DeviceDetailProcessor` object is an object that assists the :class:`DeviceQueryManager` in the processing
        of information queries for devices.
    """

    @classmethod
    def create_basic1_device_desc(cls, root_el: Element, device_el: Element, namespaces: Dict[str, str], specVersion: SpecVersion,
                                         locationURL: str, params: Dict[str, Any]) -> Basic1DeviceDesc:
        
        device = Basic1DeviceDesc(specVersion=specVersion, **params, locationURL=locationURL)

        return device

    @classmethod
    def create_embedded_device_desc(cls, root_el: Element, device_el: Element, namespaces: Dict[str, str], specVersion: SpecVersion,
                                  params: Dict[str, Any]) -> Basic1DeviceDesc:
        
        device = EmbeddedDeviceDesc(specVersion=specVersion, **params)

        return device

    @classmethod
    def process_device(cls, root_el: Element, device_el: Element, namespaces: Dict[str, str], hints: Dict[str, "DeviceDetailProcessor"],
                       specVersion: SpecVersion, locationURL: Optional[str] = None, is_embedded: bool = False) -> Basic1DeviceDesc:

        required_elements = ['deviceType', 'friendlyName', 'manufacturer', 'modelName', 'UDN']
        
        device_desc = None
        create_device = None

        manufacturerEl: Element = device_el.find("manufacturer", namespaces=namespaces)
        if manufacturerEl is not None:
            manufacturer = manufacturerEl.text.upper()


            if manufacturer in hints:
                hintsobj = hints[manufacturer]
                if not is_embedded:
                    if hasattr(hintsobj, "create_basic1_device_desc"):
                        create_device = hintsobj.create_basic1_device_desc
                else:
                    if hasattr(hintsobj, "create_embedded_device_desc"):
                        create_device = hintsobj.create_embedded_device_desc

            if create_device is None:
                if not is_embedded:
                    create_device = DeviceDetailProcessor.create_basic1_device_desc
                else:
                    create_device = DeviceDetailProcessor.create_embedded_device_desc

            params = {}

            for child_el in device_el:
                full_tag = child_el.tag

                if full_tag.startswith(UPNP_DEVICE1_NAMESPACE_PREFIX):
                    tag = full_tag[UPNP_DEVICE1_NAMESPACE_PREFIX_END:]

                    val = None
                    if tag == "manufacturer":
                        val = child_el.text
                        manufacturer = val.upper()
                    elif tag == "iconList":
                        val = DeviceDetailProcessor.process_icons_list(child_el, namespaces=namespaces)
                    elif tag == 'deviceList':
                        val = DeviceDetailProcessor.process_embedded_devices_list(child_el, namespaces=namespaces, hints=hints)
                    elif tag == 'serviceList':
                        val = DeviceDetailProcessor.process_services_list(child_el, namespaces=namespaces)
                    else:
                        val = child_el.text
                    
                    if val != None:
                        params[tag] = val

                    if tag in required_elements:
                        required_elements.remove(tag)

            if len(required_elements) > 0:
                err_msg = f"Missing required elements in device description: {', '.join(required_elements)}"
                logger.error(err_msg)
                raise ValueError(err_msg)

            device_desc = create_device(root_el, device_el, namespaces, specVersion, locationURL, params)

        else:
            warnmsg = "Received an SSDP response that did not have a 'manufacturer' field."
            logger.warning(warnmsg)

        return device_desc


    @classmethod
    def process_icons_list(cls, icons_el: Element, namespaces: Dict[str, str]) -> List[IconDesc]:
        
        iconsList = []

        for nxtEl in icons_el:
            full_tag = nxtEl.tag

            if full_tag.startswith(UPNP_DEVICE1_NAMESPACE_PREFIX):
                tag = full_tag[UPNP_DEVICE1_NAMESPACE_PREFIX_END:]

                if tag == "icon":
                    propEl = nxtEl.find("mimetype", namespaces=namespaces)
                    mimetype = propEl.text

                    propEl = nxtEl.find("mimetype", namespaces=namespaces)
                    width = int(propEl.text)

                    propEl = nxtEl.find("mimetype", namespaces=namespaces)
                    height = int(propEl.text)

                    propEl = nxtEl.find("mimetype", namespaces=namespaces)
                    depth = int(propEl.text)

                    propEl = nxtEl.find("url", namespaces=namespaces)
                    url = propEl.text

                    iconInfo = IconDesc(mimetype=mimetype, width=width, height=height, depth=depth, url=url)
                    iconsList.append(iconInfo)

        return iconsList
    

    @classmethod
    def process_embedded_devices_list(cls, devices_el: Element, namespaces: Dict[str, str], hints: Dict[str, str]) -> List[EmbeddedDeviceDesc]:
        
        devicesList = []

        specVersion = None

        for nxtEl in devices_el:
            full_tag = nxtEl.tag

            if full_tag.startswith(UPNP_DEVICE1_NAMESPACE_PREFIX):
                tag = full_tag[UPNP_DEVICE1_NAMESPACE_PREFIX_END:]

                if tag == "device":
                    propEl = nxtEl.find("deviceType", namespaces=namespaces)
                    deviceType = propEl.text

                    svcInfo = cls.process_device(nxtEl, nxtEl, namespaces=namespaces, hints=hints, specVersion=specVersion)
                    
                    devicesList.append(svcInfo)
                elif tag == "specVersion":

                    specVersion = cls.process_spec_version(nxtEl, namespaces=namespaces)

        return devicesList


    @classmethod
    def process_services_list(cls, services_el: Element, namespaces: Dict[str, str]) -> List[ServiceDesc]:
        
        servicesList = []

        for nxtEl in services_el:
            full_tag = nxtEl.tag

            if full_tag.startswith(UPNP_DEVICE1_NAMESPACE_PREFIX):
                tag = full_tag[UPNP_DEVICE1_NAMESPACE_PREFIX_END:]

                if tag == "service":
                    propEl = nxtEl.find("serviceType", namespaces=namespaces)
                    service_type = propEl.text

                    propEl = nxtEl.find("serviceId", namespaces=namespaces)
                    service_id = propEl.text

                    propEl = nxtEl.find("SCPDURL", namespaces=namespaces)
                    scpd_url = propEl.text

                    propEl = nxtEl.find("controlURL", namespaces=namespaces)
                    control_url = propEl.text

                    propEl = nxtEl.find("eventSubURL", namespaces=namespaces)
                    event_sub_url = propEl.text

                    svcInfo = ServiceDesc(service_type=service_type, service_id=service_id, control_url=control_url, event_sub_url=event_sub_url, scpd_url=scpd_url)
                    
                    servicesList.append(svcInfo)

        return servicesList


    @classmethod
    def process_spec_version(cls, spec_ver_el: Element, namespaces: Dict[str, str]) -> SpecVersion:

        major = int(spec_ver_el.find("major", namespaces=namespaces).text)
        minor = int(spec_ver_el.find("minor", namespaces=namespaces).text)
        
        sver = SpecVersion(major=major, minor=minor)
        
        return sver

