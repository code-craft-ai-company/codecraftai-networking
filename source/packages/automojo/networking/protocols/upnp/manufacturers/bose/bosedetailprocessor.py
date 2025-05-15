"""
.. module:: bosehints
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module containing data description classes that describe Bose UPNP devices.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2024, Myron W Walker"
__credits__ = []


from typing import Any, Dict

from xml.etree.ElementTree import Element

from automojo.networking.protocols.upnp.description.embeddeddevicedesc import EmbeddedDeviceDesc
from automojo.networking.protocols.upnp.description.specversion import SpecVersion
from automojo.networking.protocols.upnp.devicedetailprocessor import DeviceDetailProcessor

from automojo.networking.protocols.upnp.manufacturers.bose.constants import BOSE_XML_NAMESPACES, BOSE_NAMESPACE_PREFIX_END


from automojo.networking.protocols.upnp.manufacturers.bose.description.bosedevicedetail import BoseDeviceDetail
from automojo.networking.protocols.upnp.manufacturers.bose.description.boseembeddeddevicedetail import BoseEmbeddedDeviceDetail
from automojo.networking.protocols.upnp.manufacturers.bose.description.bosemultiroomversions import BoseMultiRoomVersions
from automojo.networking.protocols.upnp.manufacturers.bose.description.bosefeatureversion import BoseFeatureVersion

class BoseDetailProcessor(DeviceDetailProcessor):
    """
        The :class:`BoseHints` object is a :class:`ManufacturerHints` object that has been customized provide
        more detailed processing of Bose secific device descriptions.
    """

    @classmethod
    def create_basic1_device_desc(cls, root_el: Element, device_el: Element, namespaces: Dict[str, str], specVersion: SpecVersion,
                                  locationURL: str, params: Dict[str, Any]) -> BoseDeviceDetail:

        ext_params = {
            "mac_addr": None,
            "generation":  None,
            "codename":  None,
            "color": None,
            "software_version": None,
            "multi_room": None
        }

        params.update(ext_params)

        all_namespaces = {}
        all_namespaces.update(namespaces)
        all_namespaces.update(BOSE_XML_NAMESPACES)

        for child_el in device_el.iterfind("./bose:*", namespaces=BOSE_XML_NAMESPACES):
            full_tag = child_el.tag
            tag = full_tag[BOSE_NAMESPACE_PREFIX_END:]

            if tag == "X_MAC":
                params['mac_addr'] = child_el.text
            elif tag == "X_ecoSystem":
                params['generation'] = child_el.text
            elif tag == "X_productType":
                params['codename'] = child_el.text
            elif tag == "X_productColor":
                params['color'] = child_el.text
            elif tag == "X_softwareVersion":
                params['software_version'] = child_el.text
            elif tag == "X_multiroomVersions":
                params['multi_room'] = BoseDetailProcessor.process_device_multiroom_versions(child_el, all_namespaces)
        
        try:
            device = BoseDeviceDetail(specVersion=specVersion, locationURL=locationURL, **params)
        except Exception as err:
            err_msg = f"Error creating Bose device description: {err}"
            raise

        return device

    @classmethod
    def create_embedded_device_desc(cls, root_el: Element, device_el: Element, namespaces: Dict[str, str], specVersion: SpecVersion,
                                   params: Dict[str, Any]) -> EmbeddedDeviceDesc:
        ext_params = {
            "mac_addr": None,
            "generation":  None,
            "codename":  None,
            "color": None,
            "software_version": None,
            "multi_room": None
        }

        params.update(ext_params)
        
        all_namespaces = {}
        all_namespaces.update(namespaces)
        all_namespaces.update(BOSE_XML_NAMESPACES)

        for child_el in device_el.iterfind("./bose:*", namespaces=BOSE_XML_NAMESPACES):            
            full_tag = child_el.tag
            tag = full_tag[BOSE_NAMESPACE_PREFIX_END:]

            if tag == "X_MAC":
                params['mac_addr'] = child_el.text
            elif tag == "X_ecoSystem":
                params['generation'] = child_el.text
            elif tag == "X_productType":
                params['codename'] = child_el.text
            elif tag == "X_productColor":
                params['color'] = child_el.text
            elif tag == "X_softwareVersion":
                params['software_version'] = child_el.text
            elif tag == "X_multiroomVersions":
                params['multi_room'] = BoseDetailProcessor.process_device_multiroom_versions(child_el, all_namespaces)

        try:
            device = BoseEmbeddedDeviceDetail(specVersion=specVersion, locationURL=None, **params)
        except Exception as err:
            err_msg = f"Error creating Bose device description: {err}"
            raise

        return device

    @classmethod
    def process_device_multiroom_versions(cls, multiroom_el: Element, namespaces: Dict[str, str] ) -> BoseMultiRoomVersions:

        bmrv = None

        audio_control_ver = None
        audio_payload_ver = None
        clock_sync_ver = None
        nowplaying_ver = None
        playback_request_ver = None
        zonecontrol_ver = None
        
        # Bose BUG: There is a bug in the Bose specific device description content.  The base elements specific to bose are
        # in a 'bose' namespace, but the child elements are in the default namespace.  Not the 'bose' namespace.

        next_ver_el = multiroom_el.find("./AudioControl_Protocol_Version", namespaces=namespaces)
        if next_ver_el is not None:
            audio_control_ver = BoseDetailProcessor.process_bose_feature_version(next_ver_el, namespaces=namespaces)
        
        next_ver_el = multiroom_el.find("./ClockSync_Protocol_Version", namespaces=namespaces)
        if next_ver_el is not None:
            audio_payload_ver = BoseDetailProcessor.process_bose_feature_version(next_ver_el, namespaces=namespaces)
        
        next_ver_el = multiroom_el.find("./Audio_Payload_Version", namespaces=namespaces)
        if next_ver_el is not None:
            clock_sync_ver = BoseDetailProcessor.process_bose_feature_version(next_ver_el, namespaces=namespaces)

        next_ver_el = multiroom_el.find("./NowPlaying_Version", namespaces=namespaces)
        if next_ver_el is not None:
            nowplaying_ver = BoseDetailProcessor.process_bose_feature_version(next_ver_el, namespaces=namespaces)
        
        next_ver_el = multiroom_el.find("./bose:PlaybackRequest_Version", namespaces=namespaces)
        if next_ver_el is not None:
            playback_request_ver = BoseDetailProcessor.process_bose_feature_version(next_ver_el, namespaces=namespaces)
        
        next_ver_el = multiroom_el.find("./ZoneControl_Version", namespaces=namespaces)
        if next_ver_el is not None:
            zonecontrol_ver = BoseDetailProcessor.process_bose_feature_version(next_ver_el, namespaces=namespaces)
        

        bmrv = BoseMultiRoomVersions(audio_control=audio_control_ver, audio_payload=audio_payload_ver, clock_sync=clock_sync_ver,
                                     now_playing=nowplaying_ver, playback_request=playback_request_ver, zone_control=zonecontrol_ver)


        return bmrv
    
    @classmethod
    def process_bose_feature_version(cls, version_el: Element, namespaces: Dict[str, str] ) -> BoseFeatureVersion:

        major = None
        minor = None

        next_el = version_el.find("./major_version", namespaces=namespaces)
        if next_el is not None:
            major = BoseDetailProcessor.process_bose_feature_version(next_el, namespaces=namespaces)
        
        next_el = version_el.find("./minor_version", namespaces=namespaces)
        if next_el is not None:
            minor = BoseDetailProcessor.process_bose_feature_version(next_el, namespaces=namespaces)
        
        verobj = BoseFeatureVersion(major, minor)

        return verobj