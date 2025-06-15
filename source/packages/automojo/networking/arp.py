"""
    .. module:: arp
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains helper functions for working with the ARP table.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import List, Dict

import platform

def get_arp_table() -> List[Dict[str, str]]:
    """
        Get the ARP table from the system.

        :returns: A list of dictionaries containing ARP table entries.
    """

    import subprocess
    import re

    arp_command = None
    arp_item_match = None

    this_platform = platform.system()
    if this_platform == 'Windows':
        # Windows uses a different command for ARP
        arp_command = ['arp', '-a']
        arp_item_match = re.compile(r'([-.0-9]+)\s+([-0-9a-f]{17})\s+(\w+)', re.MULTILINE)
    else:
        arp_command = ['ip','neigh']
        arp_item_match = re.compile(r'([\da-fA-F.:]+)\s+dev\s+([\w-]+)\s+lladdr\s+([\da-fA-F:]+)\s+.*', re.MULTILINE)

    # Run the arp command and capture the output
    try:
        output = subprocess.check_output(arp_command, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running arp command: {e}")
        return []

    # Parse the output using regex
    arp_entries = []
    for line in output.splitlines()[1:]:
        match = arp_item_match.match(line)
        if match:
            ip, hw_type, mac = match.groups()
            arp_entries.append({
                'IPAddress': ip,
                'HWType': hw_type,
                'MACAddress': mac
            })

    return arp_entries


if __name__ == "__main__":
    # Example usage
    arp_table = get_arp_table()
    for entry in arp_table:
        print(f"IP Address: {entry['IPAddress']}, HW Type: {entry['HWType']}, MAC Address: {entry['MACAddress']}")


