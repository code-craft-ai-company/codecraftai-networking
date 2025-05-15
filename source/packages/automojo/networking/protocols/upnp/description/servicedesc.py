
__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


def xml_format_service_desc(
    service_type: str,
    service_id: str,
    control_url: str,
    event_sub_url: str,
    scpd_url: str,
    indent: str = ""
) -> str:
    """
    Create an XML representation of a service description.

    :param service_type: Type of the service.
    :param service_id: ID of the service.
    :param control_url: Control URL of the service.
    :param event_sub_url: Event subscription URL of the service.
    :param scpd_url: SCPD URL of the service.
    :param indent: Indentation for the XML string.
    :returns: XML string representation of the service description.
    """
    
    desc_lines = [
        f"{indent}<service>",
        f"{indent}    <serviceType>{service_type}</serviceType>",
        f"{indent}    <serviceId>{service_id}</serviceId>",
        f"{indent}    <controlURL>{control_url}</controlURL>",
        f"{indent}    <eventSubURL>{event_sub_url}</eventSubURL>",
        f"{indent}    <SCPDURL>{scpd_url}</SCPDURL>",
        f"{indent}</service>"
    ]

    desc = "\r\n".join(desc_lines)

    return desc


class ServiceDesc:
    """
        Class representing a UPnP service description.
    """

    def __init__(self, *, service_type: str, service_id: str, control_url: str, event_sub_url: str, scpd_url: str):
        self.service_type = service_type
        self.service_id = service_id
        self.control_url = control_url
        self.event_sub_url = event_sub_url
        self.scpd_url = scpd_url
        return
    
    def as_xml(self, indent="") -> str:
        """
        Convert the ServiceDesc object to an XML string.

        :param indent: Indentation for the XML string.
        :returns: XML string representation of the ServiceDesc object.
        """
        
        desc = xml_format_service_desc(
            service_type=self.service_type,
            service_id=self.service_id,
            control_url=self.control_url,
            event_sub_url=self.event_sub_url,
            scpd_url=self.scpd_url,
            indent=indent
        )

        return desc
    
    def __repr__(self):
        rval = f"ServiceDesc(service_type={self.service_type}, service_id={self.service_id})"
        return rval

