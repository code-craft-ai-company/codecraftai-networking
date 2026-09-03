"""
    .. module:: test_resolve_in_plane
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Unit and property tests for
                   :func:`ccai.networking.resolution.resolve_in_plane`.

    .. moduleauthor:: CodeCraftAI Test Author
"""

import inspect
import random
import unittest
from typing import Dict, Optional
from unittest import mock

from ccai.testbase.properties import strategies as st

from ccai.networking import resolution
from ccai.networking.resolution import (
    AddressPlane,
    Aspects,
    SemanticError,
    register_overlay_dns_resolver,
    resolve_in_plane,
)


class _PeerClient:
    """
        Minimal ``IVPNClient`` stand-in exposing only
        ``peer_addresses()``.
    """

    def __init__(self, *, peers: Optional[Dict[str, str]] = None) -> None:
        self._peers: Dict[str, str] = peers if peers is not None else {}
        self.call_count: int = 0
        return

    def peer_addresses(self) -> Dict[str, str]:
        self.call_count += 1
        rtnval = dict(self._peers)
        return rtnval


class _OverlayResolver:
    """
        Minimal overlay DNS resolver stand-in.
    """

    def __init__(self, *, answer: Optional[str] = None) -> None:
        self._answer: Optional[str] = answer
        self.call_count: int = 0
        return

    def resolve(self, *, name: str, aspects: Aspects) -> Optional[str]:
        self.call_count += 1
        rtnval = self._answer
        return rtnval


def _make_aspects() -> Aspects:
    rtnval = Aspects(connection_timeout=1.0)
    return rtnval


class ResolveInPlaneDispatchTests(unittest.TestCase):
    """
        Example-based dispatch tests for :func:`resolve_in_plane`.
    """

    def setUp(self) -> None:
        register_overlay_dns_resolver(resolver=None)
        return

    def tearDown(self) -> None:
        register_overlay_dns_resolver(resolver=None)
        return

    def test_public_plane_delegates_to_public_resolver(self) -> None:
        """
            Verify ``PUBLIC`` delegates to :func:`_resolve_public`.
        """
        with mock.patch.object(resolution, "_resolve_public", return_value="1.2.3.4") as pub:
            rtnval = resolve_in_plane(
                name="host.example.com",
                plane=AddressPlane.PUBLIC,
                aspects=_make_aspects(),
            )
        self.assertEqual(rtnval, "1.2.3.4")
        pub.assert_called_once()
        return

    def test_private_plane_delegates_to_private_resolver(self) -> None:
        """
            Verify ``PRIVATE`` delegates to :func:`_resolve_private`.
        """
        with mock.patch.object(resolution, "_resolve_private", return_value="10.0.0.5") as priv:
            rtnval = resolve_in_plane(
                name="host.internal",
                plane=AddressPlane.PRIVATE,
                aspects=_make_aspects(),
            )
        self.assertEqual(rtnval, "10.0.0.5")
        priv.assert_called_once()
        return

    def test_overlay_plane_consults_vpn_client_first(self) -> None:
        """
            Verify ``OVERLAY`` consults the ``vpn_client.peer_addresses()``
            map and returns the matching value.
        """
        client = _PeerClient(peers={"db1": "100.64.0.5"})
        rtnval = resolve_in_plane(
            name="db1",
            plane=AddressPlane.OVERLAY,
            aspects=_make_aspects(),
            vpn_client=client,
        )
        self.assertEqual(rtnval, "100.64.0.5")
        self.assertEqual(client.call_count, 1)
        return

    def test_overlay_plane_falls_through_to_overlay_dns_resolver(self) -> None:
        """
            Verify the overlay DNS resolver is consulted when the
            vpn_client does not have the name.
        """
        client = _PeerClient(peers={})
        resolver = _OverlayResolver(answer="100.64.0.7")
        register_overlay_dns_resolver(resolver=resolver)
        rtnval = resolve_in_plane(
            name="db2",
            plane=AddressPlane.OVERLAY,
            aspects=_make_aspects(),
            vpn_client=client,
        )
        self.assertEqual(rtnval, "100.64.0.7")
        self.assertEqual(resolver.call_count, 1)
        return

    def test_overlay_plane_returns_none_when_no_resolver_available(self) -> None:
        """
            Verify ``None`` is returned when no vpn_client and no
            registered overlay DNS resolver are available.
        """
        rtnval = resolve_in_plane(
            name="db3",
            plane=AddressPlane.OVERLAY,
            aspects=_make_aspects(),
            vpn_client=None,
        )
        self.assertIsNone(rtnval)
        return

    def test_overlay_plane_does_not_fall_through_to_public(self) -> None:
        """
            Verify ``OVERLAY`` never delegates to the public resolver
            even when the public resolver would have answered.
        """
        client = _PeerClient(peers={})
        with mock.patch.object(resolution, "_resolve_public", return_value="1.2.3.4") as pub:
            rtnval = resolve_in_plane(
                name="db4",
                plane=AddressPlane.OVERLAY,
                aspects=_make_aspects(),
                vpn_client=client,
            )
        self.assertIsNone(rtnval)
        pub.assert_not_called()
        return

    def test_empty_name_raises_semantic_error(self) -> None:
        """
            Verify an empty ``name`` raises :class:`SemanticError`.
        """
        with self.assertRaises(SemanticError):
            resolve_in_plane(
                name="",
                plane=AddressPlane.PUBLIC,
                aspects=_make_aspects(),
            )
        return

    def test_unknown_plane_raises_semantic_error(self) -> None:
        """
            Verify a non-``AddressPlane`` member raises
            :class:`SemanticError` via the else branch.
        """
        with self.assertRaises(SemanticError):
            resolve_in_plane(
                name="db",
                plane=999,  # type: ignore[arg-type]
                aspects=_make_aspects(),
            )
        return

    def test_no_cidr_sniffing_in_dispatch(self) -> None:
        """
            Review-style test: assert no branch in :func:`resolve_in_plane`
            or its overlay helper reads CIDR ranges from a resolved
            address (which would imply implicit plane classification).
        """
        src = inspect.getsource(resolve_in_plane) + inspect.getsource(resolution._resolve_overlay)
        for token in ("ipaddress.", "ip_network", "ip_address", "CIDR", "cidr"):
            self.assertNotIn(token, src, f"unexpected CIDR-sniffing token {token!r} in dispatch")
        return


# ----- Hypothesis property tests (⊙) ------------------------------------

_plane_strategy = st.sampled_from(list(AddressPlane))
_name_strategy = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters="\x00"),
    min_size=1,
    max_size=64,
)
_addr_strategy = st.text(min_size=1, max_size=39)
_peer_map_strategy = st.dictionaries(_name_strategy, _addr_strategy, max_size=8)


def _run_property(test: unittest.TestCase, check, max_examples: int, **strategies) -> None:
    """
        Runs ``check`` against ``max_examples`` generated inputs. ``@given`` from ccai.testbase only marks a
        test for the testbase sequencer's property runner; under plain unittest the examples have to be drawn
        here, from a fixed seed so a failure reproduces.
    """
    rng = random.Random(0x5EED)
    for index in range(max_examples):
        kwargs = {name: strategy.generate(rng) for name, strategy in strategies.items()}
        with test.subTest(example=index, **{name: repr(value)[:48] for name, value in kwargs.items()}):
            check(**kwargs)
    return


class ResolveInPlanePropertyTests(unittest.TestCase):
    """
        Hypothesis property tests for :func:`resolve_in_plane`.
    """

    def setUp(self) -> None:
        register_overlay_dns_resolver(resolver=None)
        # Stub the OS resolvers so totality tests are network-free.
        self._public_patcher = mock.patch.object(
            resolution, "_resolve_public", return_value="9.9.9.9"
        )
        self._private_patcher = mock.patch.object(
            resolution, "_resolve_private", return_value="10.10.10.10"
        )
        self._public_patcher.start()
        self._private_patcher.start()
        return

    def tearDown(self) -> None:
        self._public_patcher.stop()
        self._private_patcher.stop()
        register_overlay_dns_resolver(resolver=None)
        return

    def test_p1_totality(self) -> None:
        _run_property(self, self._test_p1_totality, 80, name=_name_strategy, plane=_plane_strategy, peers=_peer_map_strategy)
        return

    def _test_p1_totality(self, name: str, plane: AddressPlane, peers: Dict[str, str]) -> None:
        """
            P1 — For any ``plane`` and non-empty ``name``,
            :func:`resolve_in_plane` returns ``Optional[str]`` and does
            not raise.
        """
        client = _PeerClient(peers=peers)
        rtnval = resolve_in_plane(
            name=name,
            plane=plane,
            aspects=_make_aspects(),
            vpn_client=client,
        )
        self.assertTrue(rtnval is None or isinstance(rtnval, str))
        return

    def test_p2_plane_isolation(self) -> None:
        _run_property(self, self._test_p2_plane_isolation, 80, name=_name_strategy)
        return

    def _test_p2_plane_isolation(self, name: str) -> None:
        """
            P2 — Asking for ``OVERLAY`` with an empty peer map and no
            registered overlay DNS resolver returns ``None`` even though
            the public resolver mock would have answered.
        """
        client = _PeerClient(peers={})
        rtnval = resolve_in_plane(
            name=name,
            plane=AddressPlane.OVERLAY,
            aspects=_make_aspects(),
            vpn_client=client,
        )
        self.assertIsNone(rtnval)
        return

    def test_p3_idempotence(self) -> None:
        _run_property(self, self._test_p3_idempotence, 60, name=_name_strategy, plane=_plane_strategy, peers=_peer_map_strategy)
        return

    def _test_p3_idempotence(self, name: str, plane: AddressPlane, peers: Dict[str, str]) -> None:
        """
            P3 — Repeated calls with the same inputs return the same value.
        """
        client = _PeerClient(peers=peers)
        first = resolve_in_plane(
            name=name, plane=plane, aspects=_make_aspects(), vpn_client=client,
        )
        second = resolve_in_plane(
            name=name, plane=plane, aspects=_make_aspects(), vpn_client=client,
        )
        self.assertEqual(first, second)
        return

    def test_p4_vpn_client_first(self) -> None:
        _run_property(self, self._test_p4_vpn_client_first, 80, name=_name_strategy, address=_addr_strategy)
        return

    def _test_p4_vpn_client_first(self, name: str, address: str) -> None:
        """
            P4 — For any ``name`` present in the vpn_client map, asking
            for ``OVERLAY`` returns the map value regardless of whether
            an overlay DNS resolver is registered.
        """
        client = _PeerClient(peers={name: address})
        # Registered resolver would otherwise return a different answer.
        register_overlay_dns_resolver(resolver=_OverlayResolver(answer="zzz"))
        try:
            rtnval = resolve_in_plane(
                name=name,
                plane=AddressPlane.OVERLAY,
                aspects=_make_aspects(),
                vpn_client=client,
            )
        finally:
            register_overlay_dns_resolver(resolver=None)
        self.assertEqual(rtnval, address)
        return

    def test_p5_public_resolver_not_consulted_under_overlay(self) -> None:
        _run_property(self, self._test_p5_public_resolver_not_consulted_under_overlay, 80, name=_name_strategy, peers=_peer_map_strategy)
        return

    def _test_p5_public_resolver_not_consulted_under_overlay(self, name: str, peers: Dict[str, str]) -> None:
        """
            P5 — The public resolver mock is never called when the
            requested plane is ``OVERLAY``.
        """
        client = _PeerClient(peers=peers)
        pub_mock = resolution._resolve_public  # currently patched
        before = pub_mock.call_count  # type: ignore[attr-defined]
        resolve_in_plane(
            name=name,
            plane=AddressPlane.OVERLAY,
            aspects=_make_aspects(),
            vpn_client=client,
        )
        after = pub_mock.call_count  # type: ignore[attr-defined]
        self.assertEqual(before, after)
        return


class CanonicalTypeIdentityTests(unittest.TestCase):
    """
        Regression tests for audit finding F-H5: the resolution module
        previously defined a SEPARATE local ``SemanticError`` class via an
        ImportError fallback, so callers' ``except`` / ``isinstance`` against
        the canonical ``ccai.errors.exceptions.SemanticError`` silently
        missed it.
    """

    def test_semantic_error_is_canonical(self) -> None:
        """
            ``resolution.SemanticError`` must be the canonical
            ``ccai.errors.exceptions.SemanticError`` type.
        """
        from ccai.errors.exceptions import SemanticError as CanonicalSemanticError

        self.assertIs(SemanticError, CanonicalSemanticError)
        return

    def test_empty_name_raises_canonical_semantic_error(self) -> None:
        """
            The error raised for an empty name must be catchable as the
            canonical ``SemanticError``.
        """
        from ccai.errors.exceptions import SemanticError as CanonicalSemanticError

        with self.assertRaises(CanonicalSemanticError):
            resolve_in_plane(
                name="",
                plane=AddressPlane.PUBLIC,
                aspects=_make_aspects(),
            )
        return

    def test_address_plane_is_canonical(self) -> None:
        """
            ``resolution.AddressPlane`` must be the canonical
            ``ccai.interfaces.addressplane.AddressPlane`` type.
        """
        from ccai.interfaces.addressplane import AddressPlane as CanonicalAddressPlane

        self.assertIs(resolution.AddressPlane, CanonicalAddressPlane)
        return


if __name__ == "__main__":
    unittest.main()
