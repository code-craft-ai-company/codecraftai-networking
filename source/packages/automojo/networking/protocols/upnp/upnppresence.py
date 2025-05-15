"""
.. module:: UpnpPresence
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module containing the :class:`UpnpPresence` class and associated diagnostic.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>

"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2024, Myron W Walker"
__credits__ = []


from typing import Dict, List, Optional, Tuple

import copy
import logging
import re
import socket
import threading
import uuid
import weakref

from datetime import datetime, timedelta

from automojo.networking.multicast import create_multicast_listener_socket

from automojo.networking.protocols.upnp.upnpsearchwindow import UpnpSearchWindow
from automojo.networking.protocols.upnp.upnpdevicedetail import UpnpDeviceDetail
from automojo.networking.protocols.upnp.devicequerymanager import DeviceQueryManager
from automojo.networking.protocols.upnp.constants import (
    UPNP_DEFAULT_SEARCH_WINDOW_LENGTH,
    UPNP_DEFAULT_SEARCH_MONITOR_INTERVAL
)

from automojo.networking.protocols.upnp.upnpdevicehint import UpnpDeviceHint
from automojo.networking.protocols.upnp.evidence.upnpdeviceevidence import UpnpDeviceEvidence
from automojo.networking.protocols.upnp.evidence.upnpserviceevidence import UpnpServiceEvidence


REGEX_NOTIFY_HEADER = re.compile("NOTIFY[ ]+[*/]+[ ]+HTTP/1")


logger = logging.getLogger()


class MSearchTargets:
    """
        MSearch target constants.
    """
    ROOTDEVICE = "upnp:rootdevice"
    ALL="ssdp:all"


class MSearchKeys:
    """
        MSearch dictionary or header keys that MSearch response data items are stored under.
    """
    CACHE_CONTROL = "CACHE-CONTROL"
    EXT = "EXT"
    LOCATION = "LOCATION"
    NTS = "NTS"
    SERVER = "SERVER"
    ST = "ST"
    USN = "USN"
    USN_DEV = "USN_DEV"
    USN_CLS = "USN_CLS"

    IP = "IP"
    ROUTES = "ROUTES"


class MSearchRouteKeys:
    """
        The dictionary keys that MSearch interface routing information is stored under.
    """
    IFNAME = "LOCAL_IFNAME"
    IP = "LOCAL_IP"


class SsdpProtocol:
    """
        SSDP Protocol constants.
    """
    MULTICAST_ADDRESS = '239.255.255.250'
    PORT = 1900

    HEADERS = {
        "ST": MSearchTargets.ROOTDEVICE,
        "Man": "ssdp:discover",
        "MX": "1"
    }


SSDP_IPV6_MULTICAST_ADDRESS_LINK_LOCAL="FF02::C"
SSDP_IPV6_MULTICAST_ADDRESS_SITE_LOCAL="FF05::C"
SSDP_IPV6_MULTICAST_ADDRESS_ORG_LOCAL="FF08::C"
SSDP_IPV6_MULTICAST_ADDRESS_GLOBAL_LOCAL="FF0E::"


def notify_parse_request(content: str) -> dict:
    """
        Takes in the content of the NOTIFY request and parses it into a
        python dictionary object.

        :param content: Notify request content as a string.

        :return: A python dictionary with key and values from the Notify request
    """
    content = content.decode('utf-8')

    resp_headers = None
    resp_body = None

    mobj = REGEX_NOTIFY_HEADER.search(content)
    if mobj is not None:
        header_content = None
        body_content = None

        if content.find("\r\n\r\n") > -1:
            header_content, body_content = content.split("\r\n\r\n", 1)
        elif content.find("\n\n") > -1:
            header_content, body_content = content.split("\n\n", 1)
        else:
            header_content = content

        resplines = header_content.splitlines(False)

        # Pop the NOTIFY header
        resplines.pop(0).strip()

        resp_headers = {}
        for nxtline in resplines:
            cidx = nxtline.find(":")
            if cidx > -1:
                key = nxtline[:cidx].upper()
                val = nxtline[cidx+1:].strip()
                resp_headers[key] = val

        if body_content is not None:
            resp_body = body_content

    return resp_headers, resp_body


def parse_ssdp_message(content: bytes) -> Dict[str, str]:
    """
        Takes in the content of the response of an MSEARCH request and parses it into a
        python dictionary object.

        :param content: MSearch response content as a bytes.

        :return: A python dictionary with key and values from the MSearch response
    """
    content = content.decode('utf-8')

    respinfo = None

    resplines = content.splitlines(False)
    if len(resplines) > 0:
        header = resplines.pop(0).strip()
        if header.startswith("M-SEARCH * HTTP/") or header.startswith("NOTIFY * HTTP/") or header.startswith("HTTP/"):
            respinfo = {}
            for nxtline in resplines:
                cidx = nxtline.find(":")
                if cidx > -1:
                    key = nxtline[:cidx].upper()
                    val = nxtline[cidx+1:].strip()
                    respinfo[key] = val

    return respinfo


class UpnpPresenceId:

    def __init__(self, device_id: str, device_class: str):
        self._device_id = device_id
        self._device_class = device_class
        return

    def to_usn(self) -> str:
        usn = f"uuid:{self._device_id}::{self._device_class}"
        return usn


class UpnpPresence:
    """
        The UpnpPresence class is used to manage the presence of a device on the network using SSDP. The UpnpPresence object
        maintains a multi-cast listening socket and thread that listens for incoming multi-cast SSDP messages allowing the
        UpnpPresence to establish a UPNP device presence on the network.

        The UpnpPresence class also maintains a multip-cast send and receive socket that is associated M-SEARCH activites on
        the network.  The purpose of the seperate M-SEARCH socket is because devices receiving M-SEARCH messages are going to send back
        responses in the form of a reply to the M-SEARCH request and not in the form of a broadcast.  This means we need to listend for
        M-SEARCH responses on the socket that the M-SEARCH messages were sent from.

        The M-SEARCH socket thread containuously calls the socket.recvfrom() method to listen for incoming M-SEARCH messages.  Because the
        socket is thread safe, when a 'discovery' call is made, then the calling thread simply sends the M-SEARCH message on the send side
        of the socket.  

    """


    def __init__(self, agent_id: Optional[UpnpPresenceId] = None, multicast_address = SsdpProtocol.MULTICAST_ADDRESS,
                 multicast_port = SsdpProtocol.PORT, discover_interval: int = 60, ttl: int=32):
        """
            :param agent_id: The id that is used to provide a presence for this node.  If not provided, the agent will
                             not respond to M-SEARCH events.
            :param ttl: The time to live for the multicast packet
                    0 = same host
                    1 = same subnet
                    32 = same site
                    64 = same region
                    128 = same continent
                    255 = unrestricted scope
        """
        self._agent_id = agent_id

        self._multicast_address = multicast_address
        self._multicast_port = multicast_port

        self._discover_interval = discover_interval
        self._ttl = ttl

        self._lock = threading.Lock()

        self._running = False

        self._msearch_sock = None
        self._msearch_thread = None
        
        self._presence_sock = None
        self._presence_thread = None

        self._inactive_devices: Dict[str, UpnpDeviceDetail] = {}
        self._active_devices: Dict[str, UpnpDeviceDetail] = {}

        self._services_by_device = {}

        self._query_manager = DeviceQueryManager()

        self._search_windows: Dict[str, UpnpSearchWindow] = {}

        return


    @property
    def active_devices(self) -> Dict[str, Dict[str, str]]:
        rtnval = None

        self._lock.acquire()
        try:
            rtnval = copy.deepcopy(self._active_devices)
        finally:
            self._lock.release()

        return rtnval


    @property
    def inactive_devices(self) -> Dict[str, Dict[str, str]]:

        self._lock.acquire()
        try:
            rtnval = copy.deepcopy(self._inactive_devices)
        finally:
            self._lock.release()

        return rtnval
    

    def discover_devices(self, limit_to: List[UpnpDeviceHint]=None, custom_headers: Optional[Dict[str, str]] = None,
                         window_length: float = UPNP_DEFAULT_SEARCH_WINDOW_LENGTH,
                         monitor_interval: float = UPNP_DEFAULT_SEARCH_MONITOR_INTERVAL) -> UpnpSearchWindow:

        st: str = MSearchTargets.ROOTDEVICE

        if not self._running:
            raise RuntimeError("The SSDP Scanner must be running before a discovery can be triggered.  Call 'start'.")

        msearch_msg_lines = [
            b'M-SEARCH * HTTP/1.1',
            b'HOST: %s:%d' % (SsdpProtocol.MULTICAST_ADDRESS.encode("utf-8"), SsdpProtocol.PORT),
            b'ST: %s' % st.encode("utf-8"),
            b'MX: 1',
            b'MAN: "ssdp:discover"'
        ]

        if custom_headers is not None:
            for hname, hval in custom_headers.items():
                hname = hname.upper().encode("utf-8")
                msearch_msg_lines.append(b'%s: %s' % (hname, hval.encode("utf-8")))

        msearch_msg_lines.append(b'')
        msearch_msg_lines.append(b'')

        msearch_msg = b"\r\n".join(msearch_msg_lines)
        
        start = datetime.now()
        end = start + timedelta(seconds=window_length)

        wid = str(uuid.uuid4())

        disco_window = UpnpSearchWindow(self, wid, start, end, monitor_interval, limit_to=limit_to)
        disco_window.start()

        self._lock.acquire()
        try:
            disco_window_ref = weakref.ref(disco_window)
            self._search_windows[wid] = disco_window_ref
        finally:
            self._lock.release()

        sock = self._get_search_socket()

        try:
            sock.sendto(msearch_msg, (self._multicast_address, self._multicast_port))
        except OSError as serr:
            # If we get an OSError while sending, our socket is likely invalid and we need
            # to force the socket to be re-freshed
            self._lock.acquire()
            try:
                if sock is not None:
                    sock.close()

                self._msearch_sock = None
            finally:
                self._lock.release()
            raise

        return disco_window


    def process_msearch(self, from_endpoint: Tuple[str, int], response: bytes):
        
        # We only process and respond to M-SEARCH messages if we have been given an identity
        # to respond as
        if self._agent_id is not None:
            from_ip = from_endpoint[0]
            
            msg_info = parse_ssdp_message(response)
            
            print(f"M-SEARCH: from={from_ip} ST={msg_info["ST"]}\n")
        
        return


    def process_notify(self, from_endpoint: Tuple[str, int], message: bytes):

        from_ip = from_endpoint[0]

        msg_info = parse_ssdp_message(message)

        if msg_info is not None:
            message_st = msg_info.get(MSearchKeys.ST, None)
        
            if MSearchKeys.USN in msg_info:

                if "NT" in msg_info:
                    nt = msg_info["NT"]
                    usn = msg_info.pop("USN")
                    status = None

                    if nt == 'upnp:rootdevice':

                        if "NTS" in msg_info:
                            nts = msg_info["NTS"]
                            server = msg_info.pop("SERVER")
                            location = msg_info.pop("LOCATION")

                            if nts == "ssdp:alive":
                                status = 'active'
                                
                                device_evidence = UpnpDeviceEvidence(usn=usn, status=status, server=server, location=location, ip=from_ip, other=msg_info, presence=self)
                                
                                device_desc = self._query_manager.query_device_details(location)

                                device_detail = UpnpDeviceDetail(device_evidence, device_desc)

                                self._lock.acquire()
                                try:
                                    # If we got an alive message and were able to get a new description from the device,
                                    # then we know it is now active, remove the old device detail from the inactive devices
                                    # list and add our new device detail to the active devices list. 
                                    if usn in self._inactive_devices:
                                        del self._inactive_devices[usn]

                                    self._active_devices[usn] = device_detail
                                finally:
                                    self._lock.release()

                            elif nts == "ssdp:byebye":
                                status = 'inactive'

                                device_detail = None

                                # this is a device bye-bye
                                device_evidence = UpnpDeviceEvidence(usn=usn, status=status, server=server, location=location, ip=from_ip, other=msg_info, presence=self)

                                self._lock.acquire()
                                try:
                                    device_desc = None

                                    if usn in self._active_devices:
                                        old_device_detail = self._active_devices[usn]
                                        device_desc = old_device_detail.description
                                        del self._active_devices[usn]

                                    device_detail = UpnpDeviceDetail(device_evidence, device_desc)

                                    self._inactive_devices[usn] = device_detail
                                finally:
                                    self._lock.release()

                                if device_detail is not None:
                                    self._update_device("NOTIFY", usn, status, device_detail)

                        print(f"NOTIFY - DEVICE: usn={usn} from={from_ip}")
    
                    elif nt.startswith("urn:schemas-upnp-org:service"):
                        nts = msg_info["NTS"]

                        status = 'unknown'
                        if nts == "ssdp:alive":
                            status = 'active'
                        elif nts == "ssdp:byebye":
                            status = 'inactive'

                        devusn, _ = usn.split("::")

                        self._lock.acquire()
                        try:
                            if devusn in self._active_devices:

                                service_info = UpnpServiceEvidence(device=devusn, service=nt, location=location, status=status, presence=self)

                                # If the device is active, then register the service and associate it with the device
                                if devusn in self._services_by_device:
                                    self._services_by_device[devusn] = { nt: service_info }
                                else:
                                    service_table = self._services_by_device[devusn]
                                    service_table[nt] = service_info

                        finally:
                            self._lock.release()

                        print(f"NOTIFY - SERVICE usn={devusn} from={from_ip} service={nt} status={status}")

                    else:
                        print(f"NOTIFY - OTHER usn={usn} from={from_ip}")

        else:
            logger.debug("msg_info was None.")
        
        return


    def process_msearch_reply(self, from_endpoint: Tuple[str, int], response: bytes):
        
        from_ip = from_endpoint[0]

        reply_info = parse_ssdp_message(response)

        if MSearchKeys.USN in reply_info:
            if "ST" in reply_info:
                st = reply_info["ST"]

                if st == 'upnp:rootdevice':
                    usn = reply_info.pop("USN")
                    server = reply_info.pop("SERVER")
                    location = reply_info.pop("LOCATION")

                    device_desc = self._query_manager.query_device_details(location)

                    device_evidence = UpnpDeviceEvidence(usn=usn, status="alive", server=server, location=location, ip=from_ip, other=reply_info, presence=self)

                    device_detail = UpnpDeviceDetail(device_evidence, device_desc)

                    self._lock.acquire()
                    try:
                        if usn in self._inactive_devices:
                            del self._inactive_devices[usn]

                        self._active_devices[usn] = device_detail

                        for wid, search_window_ref in self._search_windows.items():

                            search_window = search_window_ref()
                            if search_window is not None:
                                # If the search window is still active, then add the device to the search window
                                if search_window.is_active():
                                    search_window.add_device(usn, device_detail)
                                else:
                                    # If the search window is not active, then remove it from the list of search windows
                                    del self._search_windows[wid]
                            else:
                                # If the search window reference is None, then remove it from the list of search windows
                                del self._search_windows[wid]

                    finally:
                        self._lock.release()

                    self._update_device("M-SEARCH", usn, "active", device_detail)

        else:
            print(f"REPLY: from={from_ip} usn=<not found>")

        return


    def search_window_closed(self, window_id: str):
        """
            Called when a search window is closed.  This method is used to remove the search window from the list of
            active search windows.

            :param window_id: The ID of the search window that was closed.
        """
        self._lock.acquire()
        try:
            if window_id in self._search_windows:
                del self._search_windows[window_id]
        finally:
            self._lock.release()

        return
    
    
    def start(self):
        
        if self._running:
            raise RuntimeError("SSDP Scanner is already running.")

        sgate = threading.Event()

        sgate.clear()
        
        self._presence_thread = threading.Thread(target=self._presence_thread_entry, name="am-upnp-presence", args=(sgate,), daemon=True)
        self._presence_thread.start()

        sgate.wait()

        sgate.clear()
        
        self._msearch_thread = threading.Thread(target=self._msearch_thread_entry, name="am-upnp-search", args=(sgate,), daemon=True)
        self._msearch_thread.start()

        sgate.wait()

        return


    def _update_device(self, context: str, usn: str, status: str, device_detail: UpnpDeviceDetail):

        location = device_detail.evidence.location

        print(f"UPDATE DEVICE: context={context} usn={usn} status={status} location={location}")

        return


    def _update_service(self, context: str, usn: str, service: str, status: str, device_info: UpnpDeviceEvidence):

        print(f"UPDATE DEVICE SERVICE: context={context} usn={usn} service={service} status={status}")

        return


    def _get_presence_socket(self) -> socket.socket:

        sock = None

        self._lock.acquire()
        try:
            if self._presence_sock is None:
                self._presence_sock: socket.socket = create_multicast_listener_socket(self._multicast_address, self._multicast_port, family=socket.AF_INET, ttl=self._ttl)
            
            sock = self._presence_sock
        finally:
            self._lock.release()
            
        return sock


    def _get_search_socket(self) -> socket.socket:

        sock = None

        self._lock.acquire()
        try:
            if self._msearch_sock is None:
                self._msearch_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

            sock = self._msearch_sock
        finally:
            self._lock.release()
            
        return sock


    def _msearch_thread_entry(self, sgate: threading.Event):

        self._running = True

        self._msearch_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        sgate.set()

        while self._running:

            sock = self._get_search_socket()

            try:
                resp, addr = sock.recvfrom(1024)

                if resp.startswith(b"HTTP/"):
                    self.process_msearch_reply(addr, resp)
                
                else:
                    print(resp)

            except socket.timeout:
                pass

            except OSError:
                self._lock.acquire()
                try:
                    if sock is not None:
                        sock.close()

                    self._msearch_sock = None
                finally:
                    self._lock.release()

        return
    

    def _presence_thread_entry(self, sgate: threading.Event):

        self._running = True

        self._presence_sock: socket.socket = create_multicast_listener_socket(self._multicast_address, self._multicast_port, family=socket.AF_INET, ttl=self._ttl)

        sgate.set()

        while self._running:

            sock = self._get_presence_socket()

            try:
                resp, addr = sock.recvfrom(1024)

                if resp.startswith(b"M-SEARCH * HTTP/"):
                    self.process_msearch(addr, resp)

                elif resp.startswith(b"NOTIFY * HTTP/"):
                    self.process_notify(addr, resp)
                
                else:
                    print(resp)

            except socket.timeout:
                pass

            except:
                self._lock.acquire()
                try:
                    if sock is not None:
                        sock.close()

                    self._presence_sock = None
                finally:
                    self._lock.release()

        return

