"""
    .. module:: trafficcapturecontext
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Scope object used for capturing traffic.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Any, Callable, List, Tuple, Type, Union

from types import TracebackType

import threading
import weakref

class TrafficCaptureContext:
    """
        Context manager used for capturing network traffic from a specific source.
    """

    def __init__(self, owner: object, identifier: str, fromip: str, destroy_method: Callable):
        """
            Initializes a :class:`TrafficCaptureContext` instance.

            :param owner: The object that owns this context.
            :param identifier: An identifier for the capture session.
            :param fromip: The IP address being monitored.
            :param destroy_method: Callback used to clean up the context.

            :returns: ``None``
        """
        self._owner_ref = weakref.ref(owner)
        self._identifier = identifier
        self._fromip = fromip
        self._destroy_method = destroy_method
        self._lock = threading.Lock()
        self._captures = []
        return

    def __enter__(self) -> "TrafficCaptureContext":
        """
            Enters the context manager.

            :returns: ``self``
        """
        return self
    
    def __exit__(self, ex_type: Type[BaseException], ex_inst: BaseException, ex_tb: TracebackType) -> bool:
        """
            Exits the context manager and triggers destruction of the context.

            :param ex_type: The exception type if one occurred.
            :param ex_inst: The exception instance.
            :param ex_tb: The traceback associated with the exception.

            :returns: ``False`` so any exception is re-raised.
        """
        self._destroy_method(self)
        return False

    @property
    def captures(self) -> List[Tuple[Any, Any]]:
        """
            Returns the list of captured request information.

            :returns: A list of ``(headers, body)`` tuples.
        """
        rtnlist = None

        self._lock.acquire()
        try:
            rtnlist = [c for c in self._captures]
        finally:
            self._lock.release()

        return rtnlist
    
    @property
    def owner(self) -> Union[None, Any]:
        """
            Returns the owner object for this context or None if the owner has been cleaned up.

            :returns: The owner object.
        """
        return self._owner_ref()

    @property
    def fromip(self) -> str:
        """
            Returns the IP address being monitored.

            :returns: The IP address as a string.
        """
        return self._fromip

    @property
    def identifier(self) -> str:
        """
            Returns the identifier for this capture session.

            :returns: The session identifier.
        """
        return self._identifier

    def append_capture(self, req_headers: dict, req_body: str):
        """
            Appends a captured request to the context.

            :param req_headers: The request headers.
            :param req_body: The request body.

            :returns: ``None``
        """

        self._lock.acquire()
        try:
            self._captures.append((req_headers, req_body))
        finally:
            self._lock.release()

        return