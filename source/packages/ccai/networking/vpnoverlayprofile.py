"""
    .. module:: vpnoverlayprofile
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Contains the :class:`VPNOverlayProfile` frozen dataclass
                   and the ``SUPPORTED_VPN_PROVIDERS`` constant used by
                   landscape / provisioning code to describe a mesh-VPN
                   overlay.

    ``VPNOverlayProfile`` is an inert configuration container — it has no
    ``connect``, no ``client``, no credential reference. Concrete overlay
    bring-up combines a :class:`VPNOverlayProfile` with a separately
    looked-up credential and an ``IVPNClient`` from
    ``codecraftai-interfaces``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import logging
import os

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from ccai.errors.exceptions import ConfigurationError


SUPPORTED_VPN_PROVIDERS = ("tailscale", "twingate")


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VPNOverlayProfile:
    """
        Static configuration describing a single mesh-VPN overlay.

        Frozen, hashable, and equal-by-value so instances may be used as
        dictionary keys and as cache keys for VPN coordinator coupling.

        :param name: Identifier used by ``landscape.yaml`` and
            ``VPNJoinSpec`` to reference this profile. Must be a
            non-empty string with no whitespace.
        :param provider: One of :data:`SUPPORTED_VPN_PROVIDERS`.
        :param network: Tailnet name (``"acme.ts.net"``) or Twingate
            network slug.
        :param tags: Default tags to advertise on devices joining the
            overlay.
        :param dns_suffix: DNS suffix to append to short names, or
            ``None`` when no suffix is configured.
        :param magic_dns_enabled: ``True`` when short-name resolution
            via the control plane is expected (Tailscale MagicDNS or
            Twingate FQDN resolution).
        :param acl_ref: Optional path / id of an ACL document the
            control plane should reconcile after first apply.

        :raises: :class:`ConfigurationError` when ``name`` is empty,
            contains whitespace, or ``provider`` is not in
            :data:`SUPPORTED_VPN_PROVIDERS`.
    """
    name: str
    provider: str
    network: str
    tags: Tuple[str, ...] = field(default_factory=tuple)
    dns_suffix: Optional[str] = None
    magic_dns_enabled: bool = False
    acl_ref: Optional[str] = None

    def __post_init__(self) -> None:
        """
            Validate ``name`` and ``provider`` invariants and normalise
            ``tags`` to a tuple (so the frozen dataclass remains
            hashable and usable as a dict key).

            :raises: :class:`ConfigurationError`
        """
        if not isinstance(self.tags, tuple):
            tags_tuple = tuple(self.tags)
            object.__setattr__(self, "tags", tags_tuple)

        if len(self.name) == 0:
            err_msg_lines = ["VPNOverlayProfile 'name' must be a non-empty string."]
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg)

        has_whitespace = False
        for ch in self.name:
            if ch.isspace():
                has_whitespace = True
                break
        if has_whitespace:
            err_msg_lines = [
                "VPNOverlayProfile 'name' must contain no whitespace.",
                f"    name: {self.name!r}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg)

        if self.provider not in SUPPORTED_VPN_PROVIDERS:
            err_msg_lines = [
                "VPNOverlayProfile 'provider' must be one of the supported providers.",
                f"    expected: {SUPPORTED_VPN_PROVIDERS!r}",
                f"    actual:   {self.provider!r}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg)

        return

    def effective_dns_suffix(self) -> Optional[str]:
        """
            Return the DNS suffix verbatim regardless of the
            ``magic_dns_enabled`` flag. The flag controls overlay
            behaviour at resolve time, not the stored suffix string.

            :returns: The stored ``dns_suffix`` value, possibly ``None``.
        """
        rtnval = self.dns_suffix
        return rtnval

    @classmethod
    def from_dict(cls, *, data: dict) -> "VPNOverlayProfile":
        """
            Construct a :class:`VPNOverlayProfile` from a parsed dict
            (typically a fragment of ``landscape.yaml``).

            :param data: Mapping with the required keys ``name``,
                ``provider``, ``network`` and the optional keys
                ``tags``, ``dns_suffix``, ``magic_dns_enabled``,
                ``acl_ref``. Unknown keys are ignored with a logger
                warning.

            :returns: A constructed, validated :class:`VPNOverlayProfile`.
            :raises: :class:`ConfigurationError` when required keys are
                absent or when a field fails validation.
        """
        required = ("name", "provider", "network")
        missing: List[str] = []
        for key in required:
            if key not in data:
                missing.append(key)
        if len(missing) > 0:
            err_msg_lines = [
                "VPNOverlayProfile.from_dict missing required keys.",
                f"    missing: {missing!r}",
                f"    provided: {sorted(list(data.keys()))!r}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg)

        known_keys = {
            "name", "provider", "network", "tags",
            "dns_suffix", "magic_dns_enabled", "acl_ref",
        }
        unknown_keys: List[str] = []
        for key in data.keys():
            if key not in known_keys:
                unknown_keys.append(key)
        if len(unknown_keys) > 0:
            logger.warning(
                "VPNOverlayProfile.from_dict ignoring unknown keys: %r",
                unknown_keys,
            )

        tags_raw = data.get("tags", ())
        tags_value = tuple(tags_raw)

        rtnval = cls(
            name=data["name"],
            provider=data["provider"],
            network=data["network"],
            tags=tags_value,
            dns_suffix=data.get("dns_suffix"),
            magic_dns_enabled=bool(data.get("magic_dns_enabled", False)),
            acl_ref=data.get("acl_ref"),
        )
        return rtnval


__all__ = ["VPNOverlayProfile", "SUPPORTED_VPN_PROVIDERS"]
