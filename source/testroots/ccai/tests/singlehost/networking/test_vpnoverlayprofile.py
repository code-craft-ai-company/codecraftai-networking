"""
    .. module:: test_vpnoverlayprofile
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Testbase tests for :mod:`ccai.interfaces.vpnoverlayprofile`.

    .. moduleauthor:: CodeCraftAI Test Author
"""

import logging

from ccai.errors.exceptions import ConfigurationError
from ccai.interfaces.vpnoverlayprofile import (
    SUPPORTED_VPN_PROVIDERS,
    VPNOverlayProfile,
)


def test_construction_with_complete_payload() -> None:
    """
        Verify a complete payload constructs successfully and the
        stored field values match.
    """
    profile = VPNOverlayProfile(
        name="lab-overlay",
        provider="tailscale",
        network="acme.ts.net",
        tags=("tag:lab",),
        dns_suffix="acme.ts.net",
        magic_dns_enabled=True,
        acl_ref="acls/lab.json",
    )
    assert profile.name == "lab-overlay"
    assert profile.provider == "tailscale"
    assert profile.network == "acme.ts.net"
    assert profile.tags == ("tag:lab",)
    assert profile.dns_suffix == "acme.ts.net"
    assert profile.magic_dns_enabled
    assert profile.acl_ref == "acls/lab.json"
    return


def test_construction_empty_name_raises() -> None:
    """
        Verify an empty ``name`` raises :class:`ConfigurationError`.
    """
    raised = False
    try:
        VPNOverlayProfile(name="", provider="tailscale", network="acme.ts.net")
    except ConfigurationError:
        raised = True
    assert raised
    return


def test_construction_whitespace_name_raises() -> None:
    """
        Verify a ``name`` containing whitespace raises.
    """
    raised = False
    try:
        VPNOverlayProfile(name="lab overlay", provider="tailscale", network="acme.ts.net")
    except ConfigurationError:
        raised = True
    assert raised
    return


def test_construction_unknown_provider_raises() -> None:
    """
        Verify an unsupported ``provider`` value raises.
    """
    raised = False
    try:
        VPNOverlayProfile(name="lab", provider="nordvpn", network="acme.ts.net")
    except ConfigurationError:
        raised = True
    assert raised
    return


def test_supported_providers_constant() -> None:
    """
        Verify the supported providers constant has the expected entries.
    """
    assert "tailscale" in SUPPORTED_VPN_PROVIDERS
    assert "twingate" in SUPPORTED_VPN_PROVIDERS
    return


def test_from_dict_round_trip() -> None:
    """
        Verify a complete YAML-shaped dict round-trips into an equal profile.
    """
    data = {
        "name": "lab-overlay",
        "provider": "tailscale",
        "network": "acme.ts.net",
        "tags": ["tag:lab"],
        "dns_suffix": "acme.ts.net",
        "magic_dns_enabled": True,
        "acl_ref": "acls/lab.json",
    }
    profile = VPNOverlayProfile.from_dict(data=data)
    expected = VPNOverlayProfile(
        name="lab-overlay",
        provider="tailscale",
        network="acme.ts.net",
        tags=("tag:lab",),
        dns_suffix="acme.ts.net",
        magic_dns_enabled=True,
        acl_ref="acls/lab.json",
    )
    assert profile == expected
    assert profile.tags == ("tag:lab",)
    return


def test_from_dict_missing_keys_raises_with_list() -> None:
    """
        Verify the error message lists the missing required keys.
    """
    data = {"provider": "tailscale"}
    raised = False
    msg = ""
    try:
        VPNOverlayProfile.from_dict(data=data)
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
    assert raised
    assert "name" in msg
    assert "network" in msg
    return


def test_from_dict_ignores_unknown_keys_with_warning() -> None:
    """
        Verify unknown keys are ignored with a logger warning.
    """
    data = {
        "name": "lab",
        "provider": "twingate",
        "network": "acme.twingate.com",
        "weird_field": 42,
    }
    target_logger = logging.getLogger("ccai.interfaces.vpnoverlayprofile")
    captured_records = []

    class _ListHandler(logging.Handler):
        """
            Collects emitted log records for later inspection.
        """

        def emit(self, record: logging.LogRecord) -> None:
            """
                Append the formatted record output to the captured list.

                :param record: The log record being emitted.
            """
            formatted = self.format(record)
            captured_records.append(formatted)
            return

    list_handler = _ListHandler(level=logging.WARNING)
    previous_level = target_logger.level
    previous_propagate = target_logger.propagate
    target_logger.addHandler(list_handler)
    target_logger.setLevel(logging.WARNING)
    target_logger.propagate = False
    try:
        profile = VPNOverlayProfile.from_dict(data=data)
    finally:
        target_logger.removeHandler(list_handler)
        target_logger.setLevel(previous_level)
        target_logger.propagate = previous_propagate
    assert profile.provider == "twingate"
    assert len(captured_records) > 0
    joined = "\n".join(captured_records)
    assert "weird_field" in joined
    return


def test_equal_profiles_hash_identically() -> None:
    """
        Verify two equally-constructed profiles compare equal and
        hash identically, and are usable as a dict key.
    """
    a = VPNOverlayProfile(name="lab", provider="tailscale", network="acme.ts.net")
    b = VPNOverlayProfile(name="lab", provider="tailscale", network="acme.ts.net")
    assert a == b
    assert hash(a) == hash(b)
    bucket = {a: "value"}
    assert bucket[b] == "value"
    return


def test_effective_dns_suffix_returns_field_verbatim() -> None:
    """
        Verify the suffix string is returned regardless of the
        ``magic_dns_enabled`` flag.
    """
    profile_a = VPNOverlayProfile(
        name="lab",
        provider="tailscale",
        network="acme.ts.net",
        dns_suffix="acme.ts.net",
        magic_dns_enabled=True,
    )
    profile_b = VPNOverlayProfile(
        name="lab",
        provider="tailscale",
        network="acme.ts.net",
        dns_suffix="acme.ts.net",
        magic_dns_enabled=False,
    )
    assert profile_a.effective_dns_suffix() == "acme.ts.net"
    assert profile_b.effective_dns_suffix() == "acme.ts.net"
    return


def test_magic_dns_enabled_with_no_suffix_accepted() -> None:
    """
        Verify ``magic_dns_enabled=True`` with ``dns_suffix=None`` is
        accepted (the field combination is legal — the resolver
        decides at runtime).
    """
    profile = VPNOverlayProfile(
        name="lab",
        provider="tailscale",
        network="acme.ts.net",
        dns_suffix=None,
        magic_dns_enabled=True,
    )
    assert profile.effective_dns_suffix() is None
    assert profile.magic_dns_enabled
    return
