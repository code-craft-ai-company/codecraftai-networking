"""
    .. module:: test_resolve_in_plane
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Unit and property tests for
                   :func:`ccai.networking.resolution.resolve_in_plane`,
                   expressed as a testbase test module.

    .. moduleauthor:: CodeCraftAI Test Author
"""

import inspect
from typing import Dict, Optional
from unittest import mock

from hypothesis import HealthCheck, given, settings, strategies as st

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


def _establish_dispatch_env() -> None:
    """
        Replicate the ``ResolveInPlaneDispatchTests.setUp`` step so each
        dispatch test starts with no registered overlay DNS resolver.
    """
    register_overlay_dns_resolver(resolver=None)
    return


def _teardown_dispatch_env() -> None:
    """
        Replicate the ``ResolveInPlaneDispatchTests.tearDown`` step so each
        dispatch test leaves no registered overlay DNS resolver behind.
    """
    register_overlay_dns_resolver(resolver=None)
    return


# ----- ResolveInPlaneDispatchTests (example-based) ----------------------


def test_public_plane_delegates_to_public_resolver() -> None:
    """
        Verify ``PUBLIC`` delegates to :func:`_resolve_public`.
    """
    _establish_dispatch_env()
    try:
        with mock.patch.object(resolution, "_resolve_public", return_value="1.2.3.4") as pub:
            rtnval = resolve_in_plane(
                name="host.example.com",
                plane=AddressPlane.PUBLIC,
                aspects=_make_aspects(),
            )
        assert rtnval == "1.2.3.4"
        pub.assert_called_once()
    finally:
        _teardown_dispatch_env()
    return


def test_private_plane_delegates_to_private_resolver() -> None:
    """
        Verify ``PRIVATE`` delegates to :func:`_resolve_private`.
    """
    _establish_dispatch_env()
    try:
        with mock.patch.object(resolution, "_resolve_private", return_value="10.0.0.5") as priv:
            rtnval = resolve_in_plane(
                name="host.internal",
                plane=AddressPlane.PRIVATE,
                aspects=_make_aspects(),
            )
        assert rtnval == "10.0.0.5"
        priv.assert_called_once()
    finally:
        _teardown_dispatch_env()
    return


def test_overlay_plane_consults_vpn_client_first() -> None:
    """
        Verify ``OVERLAY`` consults the ``vpn_client.peer_addresses()``
        map and returns the matching value.
    """
    _establish_dispatch_env()
    try:
        client = _PeerClient(peers={"db1": "100.64.0.5"})
        rtnval = resolve_in_plane(
            name="db1",
            plane=AddressPlane.OVERLAY,
            aspects=_make_aspects(),
            vpn_client=client,
        )
        assert rtnval == "100.64.0.5"
        assert client.call_count == 1
    finally:
        _teardown_dispatch_env()
    return


def test_overlay_plane_falls_through_to_overlay_dns_resolver() -> None:
    """
        Verify the overlay DNS resolver is consulted when the
        vpn_client does not have the name.
    """
    _establish_dispatch_env()
    try:
        client = _PeerClient(peers={})
        resolver = _OverlayResolver(answer="100.64.0.7")
        register_overlay_dns_resolver(resolver=resolver)
        rtnval = resolve_in_plane(
            name="db2",
            plane=AddressPlane.OVERLAY,
            aspects=_make_aspects(),
            vpn_client=client,
        )
        assert rtnval == "100.64.0.7"
        assert resolver.call_count == 1
    finally:
        _teardown_dispatch_env()
    return


def test_overlay_plane_returns_none_when_no_resolver_available() -> None:
    """
        Verify ``None`` is returned when no vpn_client and no
        registered overlay DNS resolver are available.
    """
    _establish_dispatch_env()
    try:
        rtnval = resolve_in_plane(
            name="db3",
            plane=AddressPlane.OVERLAY,
            aspects=_make_aspects(),
            vpn_client=None,
        )
        assert rtnval is None
    finally:
        _teardown_dispatch_env()
    return


def test_overlay_plane_does_not_fall_through_to_public() -> None:
    """
        Verify ``OVERLAY`` never delegates to the public resolver
        even when the public resolver would have answered.
    """
    _establish_dispatch_env()
    try:
        client = _PeerClient(peers={})
        with mock.patch.object(resolution, "_resolve_public", return_value="1.2.3.4") as pub:
            rtnval = resolve_in_plane(
                name="db4",
                plane=AddressPlane.OVERLAY,
                aspects=_make_aspects(),
                vpn_client=client,
            )
        assert rtnval is None
        pub.assert_not_called()
    finally:
        _teardown_dispatch_env()
    return


def test_empty_name_raises_semantic_error() -> None:
    """
        Verify an empty ``name`` raises :class:`SemanticError`.
    """
    _establish_dispatch_env()
    try:
        raised = False
        try:
            resolve_in_plane(
                name="",
                plane=AddressPlane.PUBLIC,
                aspects=_make_aspects(),
            )
        except SemanticError:
            raised = True
        assert raised
    finally:
        _teardown_dispatch_env()
    return


def test_unknown_plane_raises_semantic_error() -> None:
    """
        Verify a non-``AddressPlane`` member raises
        :class:`SemanticError` via the else branch.
    """
    _establish_dispatch_env()
    try:
        raised = False
        try:
            resolve_in_plane(
                name="db",
                plane=999,  # type: ignore[arg-type]
                aspects=_make_aspects(),
            )
        except SemanticError:
            raised = True
        assert raised
    finally:
        _teardown_dispatch_env()
    return


def test_no_cidr_sniffing_in_dispatch() -> None:
    """
        Review-style test: assert no branch in :func:`resolve_in_plane`
        or its overlay helper reads CIDR ranges from a resolved
        address (which would imply implicit plane classification).
    """
    _establish_dispatch_env()
    try:
        src = inspect.getsource(resolve_in_plane) + inspect.getsource(resolution._resolve_overlay)
        for token in ("ipaddress.", "ip_network", "ip_address", "CIDR", "cidr"):
            assert token not in src, f"unexpected CIDR-sniffing token {token!r} in dispatch"
    finally:
        _teardown_dispatch_env()
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


def _establish_property_env() -> Dict[str, object]:
    """
        Replicate the ``ResolveInPlanePropertyTests.setUp`` step: clear any
        registered overlay DNS resolver and stub the OS resolvers so totality
        tests are network-free.

        :returns: A mapping holding the two started mock patchers under the
                  keys ``public_patcher`` and ``private_patcher`` so the
                  caller can stop them during teardown.
    """
    register_overlay_dns_resolver(resolver=None)
    # Stub the OS resolvers so totality tests are network-free.
    public_patcher = mock.patch.object(
        resolution, "_resolve_public", return_value="9.9.9.9"
    )
    private_patcher = mock.patch.object(
        resolution, "_resolve_private", return_value="10.10.10.10"
    )
    public_patcher.start()
    private_patcher.start()
    rtnval = {
        "public_patcher": public_patcher,
        "private_patcher": private_patcher,
    }
    return rtnval


def _teardown_property_env(env: Dict[str, object]) -> None:
    """
        Replicate the ``ResolveInPlanePropertyTests.tearDown`` step: stop the
        started mock patchers and clear any registered overlay DNS resolver.

        :param env: The mapping returned by :func:`_establish_property_env`.
    """
    public_patcher = env["public_patcher"]
    private_patcher = env["private_patcher"]
    public_patcher.stop()
    private_patcher.stop()
    register_overlay_dns_resolver(resolver=None)
    return


def test_p1_totality() -> None:
    """
        P1 — For any ``plane`` and non-empty ``name``,
        :func:`resolve_in_plane` returns ``Optional[str]`` and does
        not raise.
    """
    env = _establish_property_env()
    try:

        @settings(max_examples=80, suppress_health_check=[HealthCheck.function_scoped_fixture])
        @given(name=_name_strategy, plane=_plane_strategy, peers=_peer_map_strategy)
        def _property(name: str, plane: AddressPlane, peers: Dict[str, str]) -> None:
            client = _PeerClient(peers=peers)
            rtnval = resolve_in_plane(
                name=name,
                plane=plane,
                aspects=_make_aspects(),
                vpn_client=client,
            )
            assert rtnval is None or isinstance(rtnval, str)
            return

        _property()
    finally:
        _teardown_property_env(env=env)
    return


def test_p2_plane_isolation() -> None:
    """
        P2 — Asking for ``OVERLAY`` with an empty peer map and no
        registered overlay DNS resolver returns ``None`` even though
        the public resolver mock would have answered.
    """
    env = _establish_property_env()
    try:

        @settings(max_examples=80, suppress_health_check=[HealthCheck.function_scoped_fixture])
        @given(name=_name_strategy)
        def _property(name: str) -> None:
            client = _PeerClient(peers={})
            rtnval = resolve_in_plane(
                name=name,
                plane=AddressPlane.OVERLAY,
                aspects=_make_aspects(),
                vpn_client=client,
            )
            assert rtnval is None
            return

        _property()
    finally:
        _teardown_property_env(env=env)
    return


def test_p3_idempotence() -> None:
    """
        P3 — Repeated calls with the same inputs return the same value.
    """
    env = _establish_property_env()
    try:

        @settings(max_examples=60, suppress_health_check=[HealthCheck.function_scoped_fixture])
        @given(name=_name_strategy, plane=_plane_strategy, peers=_peer_map_strategy)
        def _property(name: str, plane: AddressPlane, peers: Dict[str, str]) -> None:
            client = _PeerClient(peers=peers)
            first = resolve_in_plane(
                name=name, plane=plane, aspects=_make_aspects(), vpn_client=client,
            )
            second = resolve_in_plane(
                name=name, plane=plane, aspects=_make_aspects(), vpn_client=client,
            )
            assert first == second
            return

        _property()
    finally:
        _teardown_property_env(env=env)
    return


def test_p4_vpn_client_first() -> None:
    """
        P4 — For any ``name`` present in the vpn_client map, asking
        for ``OVERLAY`` returns the map value regardless of whether
        an overlay DNS resolver is registered.
    """
    env = _establish_property_env()
    try:

        @settings(max_examples=80, suppress_health_check=[HealthCheck.function_scoped_fixture])
        @given(name=_name_strategy, address=_addr_strategy)
        def _property(name: str, address: str) -> None:
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
            assert rtnval == address
            return

        _property()
    finally:
        _teardown_property_env(env=env)
    return


def test_p5_public_resolver_not_consulted_under_overlay() -> None:
    """
        P5 — The public resolver mock is never called when the
        requested plane is ``OVERLAY``.
    """
    env = _establish_property_env()
    try:

        @settings(max_examples=80, suppress_health_check=[HealthCheck.function_scoped_fixture])
        @given(name=_name_strategy, peers=_peer_map_strategy)
        def _property(name: str, peers: Dict[str, str]) -> None:
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
            assert before == after
            return

        _property()
    finally:
        _teardown_property_env(env=env)
    return


# ----- CanonicalTypeIdentityTests (no setUp/tearDown) -------------------


def test_semantic_error_is_canonical() -> None:
    """
        ``resolution.SemanticError`` must be the canonical
        ``ccai.errors.exceptions.SemanticError`` type.
    """
    from ccai.errors.exceptions import SemanticError as CanonicalSemanticError

    assert SemanticError is CanonicalSemanticError
    return


def test_empty_name_raises_canonical_semantic_error() -> None:
    """
        The error raised for an empty name must be catchable as the
        canonical ``SemanticError``.
    """
    from ccai.errors.exceptions import SemanticError as CanonicalSemanticError

    raised = False
    try:
        resolve_in_plane(
            name="",
            plane=AddressPlane.PUBLIC,
            aspects=_make_aspects(),
        )
    except CanonicalSemanticError:
        raised = True
    assert raised
    return


def test_address_plane_is_canonical() -> None:
    """
        ``resolution.AddressPlane`` must be the canonical
        ``ccai.interfaces.addressplane.AddressPlane`` type.
    """
    from ccai.interfaces.addressplane import AddressPlane as CanonicalAddressPlane

    assert resolution.AddressPlane is CanonicalAddressPlane
    return
