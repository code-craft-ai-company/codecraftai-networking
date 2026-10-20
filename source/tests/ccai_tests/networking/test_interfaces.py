"""
    .. module:: test_interfaces
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Unit tests for the :mod:`ccai.networking.interfaces` module.

    .. moduleauthor:: CodeCraftAI Test Author
"""

import socket
import unittest
import unittest.mock


from ccai.networking import interfaces
from ccai.networking.interfaces import InterfaceClass


class EncodeAddressTests(unittest.TestCase):
    """
        Tests for :func:`interfaces.encode_address`.
    """

    def test_encode_ipv4_address_returns_four_bytes(self) -> None:
        """
            Encoding an IPv4 address should produce a 4-byte packed value.
        """
        rtnval = interfaces.encode_address("192.168.1.1")
        self.assertEqual(len(rtnval), 4)
        self.assertEqual(rtnval, socket.inet_pton(socket.AF_INET, "192.168.1.1"))
        return

    def test_encode_ipv6_address_returns_sixteen_bytes(self) -> None:
        """
            Encoding an IPv6 address should produce a 16-byte packed value.
        """
        rtnval = interfaces.encode_address("fe80::1")
        self.assertEqual(len(rtnval), 16)
        self.assertEqual(rtnval, socket.inet_pton(socket.AF_INET6, "fe80::1"))
        return


class GetAllIpv4InterfacesTests(unittest.TestCase):
    """
        Tests for :func:`interfaces.get_all_ipv4_interfaces`.
    """

    def setUp(self) -> None:
        self.ifnames = ["eth0", "lo", "wlan0"]
        self.interfaces_patcher = unittest.mock.patch(
            "ccai.networking.nativeinterfaces.list_interfaces", return_value=self.ifnames
        )
        self.interfaces_patcher.start()

        self.addr_map = {
            "eth0": {socket.AF_INET: [{"addr": "192.168.1.10"}]},
            "lo": {socket.AF_INET: [{"addr": "127.0.0.1"}]},
            "wlan0": {socket.AF_INET6: [{"addr": "fe80::1"}]},
        }

        def fake_ifaddresses(ifname: str) -> dict:
            rtnval = self.addr_map.get(ifname, {})
            return rtnval

        self.ifaddresses_patcher = unittest.mock.patch(
            "ccai.networking.nativeinterfaces.interface_addresses", side_effect=fake_ifaddresses
        )
        self.ifaddresses_patcher.start()
        return

    def tearDown(self) -> None:
        self.interfaces_patcher.stop()
        self.ifaddresses_patcher.stop()
        return

    def test_returns_only_ipv4_interfaces(self) -> None:
        """
            Verify only interfaces with IPv4 addresses are returned.
        """
        rtnval = interfaces.get_all_ipv4_interfaces()
        expected = ["eth0", "lo"]
        self.assertEqual(rtnval, expected)
        return

    def test_returns_empty_list_when_no_ipv4(self) -> None:
        """
            Verify an empty list is returned when no IPv4-capable interfaces exist.
        """
        self.addr_map.clear()
        rtnval = interfaces.get_all_ipv4_interfaces()
        self.assertEqual(rtnval, [])
        return

    def test_skips_interfaces_with_empty_ipv4_list(self) -> None:
        """
            An interface with an empty AF_INET list should be skipped.
        """
        self.addr_map["eth0"] = {socket.AF_INET: []}
        rtnval = interfaces.get_all_ipv4_interfaces()
        self.assertNotIn("eth0", rtnval)
        return


class GetAllIpv6InterfacesTests(unittest.TestCase):
    """
        Tests for :func:`interfaces.get_all_ipv6_interfaces`.
    """

    def setUp(self) -> None:
        self.ifnames = ["eth0", "lo", "wlan0"]
        self.interfaces_patcher = unittest.mock.patch(
            "ccai.networking.nativeinterfaces.list_interfaces", return_value=self.ifnames
        )
        self.interfaces_patcher.start()

        self.addr_map = {
            "eth0": {
                socket.AF_INET: [{"addr": "192.168.1.10"}],
                socket.AF_INET6: [{"addr": "fe80::1"}],
            },
            "lo": {socket.AF_INET: [{"addr": "127.0.0.1"}]},
            "wlan0": {socket.AF_INET6: [{"addr": "fe80::2"}]},
        }

        def fake_ifaddresses(ifname: str) -> dict:
            rtnval = self.addr_map.get(ifname, {})
            return rtnval

        self.ifaddresses_patcher = unittest.mock.patch(
            "ccai.networking.nativeinterfaces.interface_addresses", side_effect=fake_ifaddresses
        )
        self.ifaddresses_patcher.start()
        return

    def tearDown(self) -> None:
        self.interfaces_patcher.stop()
        self.ifaddresses_patcher.stop()
        return

    def test_returns_only_ipv6_interfaces(self) -> None:
        """
            Verify only interfaces with IPv6 addresses are returned.
        """
        rtnval = interfaces.get_all_ipv6_interfaces()
        expected = ["eth0", "wlan0"]
        self.assertEqual(rtnval, expected)
        return

    def test_returns_empty_list_when_no_ipv6(self) -> None:
        """
            Verify an empty list is returned when no IPv6-capable interfaces exist.
        """
        self.addr_map["eth0"] = {socket.AF_INET: [{"addr": "192.168.1.10"}]}
        del self.addr_map["wlan0"]
        rtnval = interfaces.get_all_ipv6_interfaces()
        self.assertEqual(rtnval, [])
        return


class GetIpv4AddressTests(unittest.TestCase):
    """
        Tests for :func:`interfaces.get_ipv4_address`.
    """

    def test_returns_ipv4_address_when_available(self) -> None:
        """
            Verify the first IPv4 address is returned for an interface.
        """
        addr_table = {socket.AF_INET: [{"addr": "10.0.0.5"}]}
        with unittest.mock.patch("ccai.networking.nativeinterfaces.interface_addresses", return_value=addr_table):
            rtnval = interfaces.get_ipv4_address("eth0")
        self.assertEqual(rtnval, "10.0.0.5")
        return

    def test_returns_none_when_no_ipv4(self) -> None:
        """
            Verify ``None`` is returned when the interface has no IPv4 address.
        """
        addr_table = {socket.AF_INET6: [{"addr": "fe80::1"}]}
        with unittest.mock.patch("ccai.networking.nativeinterfaces.interface_addresses", return_value=addr_table):
            rtnval = interfaces.get_ipv4_address("eth0")
        self.assertIsNone(rtnval)
        return


class GetIpv6AddressTests(unittest.TestCase):
    """
        Tests for :func:`interfaces.get_ipv6_address`.
    """

    def test_returns_ipv6_address_when_available(self) -> None:
        """
            Verify the first IPv6 address is returned for an interface.
        """
        addr_table = {
            socket.AF_INET6: [{"addr": "fe80::1"}],
            socket.AF_INET: [{"addr": "127.0.0.1"}],
        }
        with unittest.mock.patch("ccai.networking.nativeinterfaces.interface_addresses", return_value=addr_table):
            rtnval = interfaces.get_ipv6_address("eth0")
        self.assertEqual(rtnval, "fe80::1")
        return

    def test_returns_none_when_no_ipv6(self) -> None:
        """
            Verify ``None`` is returned when the interface has no IPv6 address.
        """
        addr_table = {socket.AF_INET: [{"addr": "10.0.0.5"}]}
        with unittest.mock.patch("ccai.networking.nativeinterfaces.interface_addresses", return_value=addr_table):
            rtnval = interfaces.get_ipv6_address("eth0")
        self.assertIsNone(rtnval)
        return


class GetCorrespondanceIpAddressTests(unittest.TestCase):
    """
        Tests for :func:`interfaces.get_correspondance_ip_address`.
    """

    def test_returns_local_socket_address_on_success(self) -> None:
        """
            Verify the function returns the local socket name's address
            after connecting.
        """
        mock_sock = unittest.mock.MagicMock()
        mock_sock.getsockname.return_value = ("10.0.0.5", 12345)

        with unittest.mock.patch("socket.socket", return_value=mock_sock):
            rtnval = interfaces.get_correspondance_ip_address("8.8.8.8", ref_port=53)

        self.assertEqual(rtnval, "10.0.0.5")
        mock_sock.connect.assert_called_once_with(("8.8.8.8", 53))
        mock_sock.close.assert_called_once()
        return

    def test_returns_none_on_connect_failure(self) -> None:
        """
            Verify the function returns ``None`` when connect raises.
        """
        mock_sock = unittest.mock.MagicMock()
        mock_sock.connect.side_effect = OSError("Network unreachable")

        with unittest.mock.patch("socket.socket", return_value=mock_sock):
            rtnval = interfaces.get_correspondance_ip_address("8.8.8.8", ref_port=53)

        self.assertIsNone(rtnval)
        mock_sock.close.assert_called_once()
        return


class GetCorrespondanceInterfaceTests(unittest.TestCase):
    """
        Tests for :func:`interfaces.get_correspondance_interface`.
    """

    def test_returns_none_when_no_correspondance_ip(self) -> None:
        """
            Verify both returns are ``None`` when no correspondence IP is found.
        """
        with unittest.mock.patch(
            "ccai.networking.interfaces.get_correspondance_ip_address",
            return_value=None,
        ) as gcia, unittest.mock.patch(
            "ccai.networking.interfaces.get_interface_for_ip"
        ) as gifip:
            iface, ip = interfaces.get_correspondance_interface("1.1.1.1", 80)
            gcia.assert_called_once()
            gifip.assert_not_called()

        self.assertIsNone(ip)
        self.assertIsNone(iface)
        return

    def test_returns_tuple_when_ip_resolved(self) -> None:
        """
            Verify the (interface, ip) tuple is returned on success.
        """
        with unittest.mock.patch(
            "ccai.networking.interfaces.get_correspondance_ip_address",
            return_value="1.2.3.4",
        ), unittest.mock.patch(
            "ccai.networking.interfaces.get_interface_for_ip",
            return_value="eth0",
        ):
            iface, ip = interfaces.get_correspondance_interface("1.1.1.1", 80)

        self.assertEqual(ip, "1.2.3.4")
        self.assertEqual(iface, "eth0")
        return


class GetInterfaceForIpTests(unittest.TestCase):
    """
        Tests for :func:`interfaces.get_interface_for_ip`.
    """

    def test_returns_matching_interface_name(self) -> None:
        """
            Verify the interface name owning the address is returned.
        """
        addr_info = [(socket.AF_INET, None, None, None, None)]
        ifnames = ["lo", "eth0"]
        addr_map = {
            "lo": {socket.AF_INET: [{"addr": "127.0.0.1"}]},
            "eth0": {socket.AF_INET: [{"addr": "10.0.0.5"}]},
        }

        def fake_ifaddresses(ifname: str) -> dict:
            rtnval = addr_map.get(ifname, {})
            return rtnval

        with unittest.mock.patch("socket.getaddrinfo", return_value=addr_info), unittest.mock.patch(
            "ccai.networking.nativeinterfaces.list_interfaces", return_value=ifnames
        ), unittest.mock.patch("ccai.networking.nativeinterfaces.interface_addresses", side_effect=fake_ifaddresses):
            rtnval = interfaces.get_interface_for_ip("10.0.0.5")

        self.assertEqual(rtnval, "eth0")
        return

    def test_returns_none_when_no_match(self) -> None:
        """
            Verify ``None`` is returned when no interface owns the address.
        """
        addr_info = [(socket.AF_INET, None, None, None, None)]
        ifnames = ["lo"]
        addr_map = {
            "lo": {socket.AF_INET: [{"addr": "127.0.0.1"}]},
        }

        def fake_ifaddresses(ifname: str) -> dict:
            rtnval = addr_map.get(ifname, {})
            return rtnval

        with unittest.mock.patch("socket.getaddrinfo", return_value=addr_info), unittest.mock.patch(
            "ccai.networking.nativeinterfaces.list_interfaces", return_value=ifnames
        ), unittest.mock.patch("ccai.networking.nativeinterfaces.interface_addresses", side_effect=fake_ifaddresses):
            rtnval = interfaces.get_interface_for_ip("10.0.0.5")

        self.assertIsNone(rtnval)
        return


class GetInterfaceClassTests(unittest.TestCase):
    """
        Tests for :func:`interfaces.get_interface_class` and the related
        table/filter helpers.
    """

    def test_raises_filenotfound_when_syspath_missing(self) -> None:
        """
            Verify a missing /sys/class/net path raises FileNotFoundError.
        """
        with unittest.mock.patch("os.path.exists", return_value=False):
            with self.assertRaises(FileNotFoundError):
                interfaces.get_interface_class("eth0")
        return

    def test_returns_wireless_when_wireless_dir_present(self) -> None:
        """
            Verify a directory listing containing 'wireless' yields WIRELESS.
        """
        with unittest.mock.patch("os.path.exists", return_value=True), unittest.mock.patch(
            "os.listdir", return_value=["wireless", "address"]
        ):
            rtnval = interfaces.get_interface_class("wlan0")
        self.assertEqual(rtnval, InterfaceClass.WIRELESS)
        return

    def test_returns_bridge_when_bridge_dir_present(self) -> None:
        """
            Verify a directory listing containing 'bridge' yields BRIDGE.
        """
        with unittest.mock.patch("os.path.exists", return_value=True), unittest.mock.patch(
            "os.listdir", return_value=["bridge", "address"]
        ):
            rtnval = interfaces.get_interface_class("br0")
        self.assertEqual(rtnval, InterfaceClass.BRIDGE)
        return

    def test_returns_loopback_when_flags_indicate(self) -> None:
        """
            Verify ifconfig flags containing 'LOOPBACK' yield LOOPBACK.
        """
        ifconfig_output = "lo: flags=8049<UP,LOOPBACK,RUNNING,MULTICAST>\n"
        with unittest.mock.patch("os.path.exists", return_value=True), unittest.mock.patch(
            "os.listdir", return_value=["address"]
        ), unittest.mock.patch(
            "subprocess.check_output", return_value=ifconfig_output.encode("utf8")
        ):
            rtnval = interfaces.get_interface_class("lo")
        self.assertEqual(rtnval, InterfaceClass.LOOPBACK)
        return

    def test_returns_tunnel_when_flags_indicate_p2p(self) -> None:
        """
            Verify ifconfig flags containing 'POINTTOPOINT' yield TUNNEL.
        """
        ifconfig_output = "tun0: flags=8051<UP,POINTTOPOINT,RUNNING>\n"
        with unittest.mock.patch("os.path.exists", return_value=True), unittest.mock.patch(
            "os.listdir", return_value=["address"]
        ), unittest.mock.patch(
            "subprocess.check_output", return_value=ifconfig_output.encode("utf8")
        ):
            rtnval = interfaces.get_interface_class("tun0")
        self.assertEqual(rtnval, InterfaceClass.TUNNEL)
        return

    def test_returns_wired_when_no_special_flags(self) -> None:
        """
            Verify a regular interface yields WIRED.
        """
        ifconfig_output = "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>\n"
        with unittest.mock.patch("os.path.exists", return_value=True), unittest.mock.patch(
            "os.listdir", return_value=["address"]
        ), unittest.mock.patch(
            "subprocess.check_output", return_value=ifconfig_output.encode("utf8")
        ):
            rtnval = interfaces.get_interface_class("eth0")
        self.assertEqual(rtnval, InterfaceClass.WIRED)
        return


class GetInterfaceClassTableTests(unittest.TestCase):
    """
        Tests for :func:`interfaces.get_interface_class_table` and
        :func:`interfaces.get_interface_names_of_class`.
    """

    def test_table_aggregates_classes_for_each_interface(self) -> None:
        """
            Verify the table maps every interface name to a class.
        """
        ifnames = ["lo", "eth0"]

        def fake_get_class(ifname: str) -> InterfaceClass:
            rtnval = (
                InterfaceClass.LOOPBACK
                if ifname == "lo"
                else InterfaceClass.WIRED
            )
            return rtnval

        with unittest.mock.patch("ccai.networking.nativeinterfaces.list_interfaces", return_value=ifnames), unittest.mock.patch(
            "ccai.networking.interfaces.get_interface_class",
            side_effect=fake_get_class,
        ):
            rtnval = interfaces.get_interface_class_table()

        expected = {"lo": InterfaceClass.LOOPBACK, "eth0": InterfaceClass.WIRED}
        self.assertEqual(rtnval, expected)
        return

    def test_filter_returns_only_matching_class(self) -> None:
        """
            Verify the filter helper returns only interfaces of the given class.
        """
        table = {
            "lo": InterfaceClass.LOOPBACK,
            "eth0": InterfaceClass.WIRED,
            "wlan0": InterfaceClass.WIRELESS,
        }
        with unittest.mock.patch(
            "ccai.networking.interfaces.get_interface_class_table",
            return_value=table,
        ):
            rtnval = interfaces.get_interface_names_of_class(InterfaceClass.WIRELESS)
        self.assertEqual(rtnval, ["wlan0"])
        return


class IsIpv6AddressTests(unittest.TestCase):
    """
        Tests for the byte-length-based :func:`interfaces.is_ipv6_address`.
    """

    def test_returns_true_for_16_byte_input(self) -> None:
        """
            Verify a 16-byte raw input is treated as IPv6.
        """
        rtnval = interfaces.is_ipv6_address("0123456789abcdef")
        self.assertTrue(rtnval)
        return

    def test_returns_false_for_other_lengths(self) -> None:
        """
            Verify non-16-byte input is rejected.
        """
        rtnval = interfaces.is_ipv6_address("1234")
        self.assertFalse(rtnval)
        return


if __name__ == "__main__":
    unittest.main()
