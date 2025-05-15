
__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


def xml_format_spec_version(
    major: int,
    minor: int,
    indent: str = ""
) -> str:
    """
    Create an XML representation of the spec version.

    :param major: Major version number.
    :param minor: Minor version number.
    :param indent: Indentation for the XML string.
    :returns: XML string representation of the spec version.
    """

    desc_lines = [
        f"{indent}<specVersion>",
        f"{indent}    <major>{major}</major>",
        f"{indent}    <minor>{minor}</minor>",
        f"{indent}</specVersion>"
    ]

    desc = "\r\n".join(desc_lines)

    return desc


class SpecVersion:

    def __init__(self, *, major: int, minor: int):
        self.major = major
        self.minor = minor
        return

    def as_xml(self, indent="") -> str:
        """
        Convert the SpecVersion object to an XML string.

        :param indent: Indentation for the XML string.
        :returns: XML string representation of the SpecVersion object.
        """

        desc = xml_format_spec_version(
            major=self.major,
            minor=self.minor,
            indent=indent
        )

        return desc

