
__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Optional

import logging


from http import HTTPStatus

from xml.etree.ElementTree import fromstring as parse_xml_content
from xml.etree.ElementTree import Element

import requests

from automojo.networking.protocols.upnp.manufacturers.bose.bosedetailprocessor import BoseDetailProcessor
from automojo.networking.protocols.upnp.manufacturers.bose.constants import MANUFACTURER_NAME as BOSE_MANUFACTURER_NAME

from automojo.networking.protocols.upnp.constants import UPNP_DEVICE1_NAMESPACE
from automojo.networking.protocols.upnp.devicedetailprocessor import DeviceDetailProcessor

from automojo.networking.protocols.upnp.description.basic1devicedesc import Basic1DeviceDesc

logger = logging.getLogger()

class DeviceQueryManager:

    MANUFACTURER_HINTS = {
        BOSE_MANUFACTURER_NAME: BoseDetailProcessor
    }

    def __init__(self):
        return
    
    def query_device_details(self, location: str) -> Optional[Basic1DeviceDesc]:

        device_desc = None

        try:
            resp = requests.get(location, timeout=2)

            if resp.status_code == HTTPStatus.OK:
                try:
                    default_namespaces = {"": UPNP_DEVICE1_NAMESPACE}
                    xml_content = resp.content.decode("utf-8")
                    root_el = parse_xml_content(xml_content)
                    
                    spec_ver_el = root_el.find("specVersion", default_namespaces)
                    sver = DeviceDetailProcessor.process_spec_version(spec_ver_el, default_namespaces)
                    
                    device_el = root_el.find("device", namespaces=default_namespaces)
                    device_desc = DeviceDetailProcessor.process_device(root_el, device_el, default_namespaces, self.MANUFACTURER_HINTS, sver, locationURL=location)
                    
                except Exception as parse_err:
                    err_msg = f"Error parsing device description XML: {parse_err}"
                    logger.error(err_msg)

        except Exception as req_err:
            err_msg = f"Error querying device at {location}: {req_err}"
            logger.error(err_msg)

        return device_desc
    
    
