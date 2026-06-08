# Design

## Overview

`VPNOverlayProfile` is a frozen dataclass added under
`codecraftai-networking/source/packages/ccai/networking/vpnoverlayprofile.py`.
It captures every piece of static configuration an overlay needs:
the provider id, the tailnet/network identifier, the default tags
to advertise, the DNS suffix (if any), the MagicDNS toggle, and an
optional reference to an ACL document.

The class is intentionally inert. It has no `connect`, no `client`,
no credential. Concrete bring-up uses a `VPNOverlayProfile` plus a
separately-looked-up credential plus an `IVPNClient`. This keeps
the profile portable between provisioning, landscape, and test
contexts.

The §8 usability commitments are honoured here:

- One spec / two read paths (typed object + dict via `from_dict`).
- Named-only parameters at the public boundary.
- Frozen, hashable, equal-by-value — predictable container behaviour.
- No I/O.

**See Also:** [vpn-client-protocol](../../../codecraftai-interfaces/specs/vpn-client-protocol/design.md),
[vpn-control-plane-protocol](../../../codecraftai-interfaces/specs/vpn-control-plane-protocol/design.md),
[address-plane-resolution](../address-plane-resolution/design.md),
[interface-class-vpn-overlay](../interface-class-vpn-overlay/design.md),
[tailscale-credentials](../../../codecraftai-credentials/specs/tailscale-credentials/design.md),
[twingate-credentials](../../../codecraftai-credentials/specs/twingate-credentials/design.md).

---

## Architecture

```
+---------------------------+
| landscape.yaml            |
|   vpn:                    |
|     - name: lab-overlay   |
|       provider: tailscale |
|       network: acme.ts.net|
|       ...                 |
+-------------+-------------+
              |
              | parsed dict
              v
+---------------------------+
| VPNOverlayProfile         |
|   .from_dict(data)        |
|   frozen, hashable        |
+-------------+-------------+
              |
        +-----+-------------------+
        |                         |
        v                         v
+-----------------+   +-----------------------+
| VPNCoordinator- |   | ProvisioningEngine    |
| Coupling        |   |  (bootstrap VPN stage)|
+-----------------+   +-----------------------+
```

---

## Data Model

```python
from dataclasses import dataclass, field
from typing import List, Optional

from ccai.errors.exceptions import ConfigurationError


SUPPORTED_VPN_PROVIDERS = ("tailscale", "twingate")


@dataclass(frozen=True)
class VPNOverlayProfile:
    """
        Static configuration describing a single mesh-VPN overlay.

        :param name: Identifier used by landscape.yaml and VPNJoinSpec to
            reference this profile.
        :param provider: One of SUPPORTED_VPN_PROVIDERS.
        :param network: Tailnet name ("acme.ts.net") or Twingate network slug.
        :param tags: Default tags to advertise on devices joining the overlay.
        :param dns_suffix: DNS suffix to append to short names, or None.
        :param magic_dns_enabled: True when short-name resolution via the
            control plane is expected (Tailscale MagicDNS or Twingate FQDN
            resolution).
        :param acl_ref: Optional path / id of an ACL document the control
            plane should reconcile after first apply.
    """
    name: str
    provider: str
    network: str
    tags: List[str] = field(default_factory=list)
    dns_suffix: Optional[str] = None
    magic_dns_enabled: bool = False
    acl_ref: Optional[str] = None

    def __post_init__(self) -> None:
        if len(self.name) == 0:
            raise ConfigurationError(
                "VPNOverlayProfile 'name' must be a non-empty string."
            )
        if any(ch.isspace() for ch in self.name):
            raise ConfigurationError(
                "VPNOverlayProfile 'name' must contain no whitespace."
            )
        if self.provider not in SUPPORTED_VPN_PROVIDERS:
            raise ConfigurationError(
                "VPNOverlayProfile 'provider' must be one of "
                f"{SUPPORTED_VPN_PROVIDERS}; got {self.provider!r}."
            )
        return

    def effective_dns_suffix(self) -> Optional[str]:
        rtnval = self.dns_suffix
        return rtnval

    @classmethod
    def from_dict(cls, *, data: dict) -> "VPNOverlayProfile":
        required = ("name", "provider", "network")
        missing: List[str] = [k for k in required if k not in data]
        if len(missing) > 0:
            raise ConfigurationError(
                "VPNOverlayProfile.from_dict missing required keys: "
                f"{missing!r}"
            )
        rtnval = cls(
            name=data["name"],
            provider=data["provider"],
            network=data["network"],
            tags=list(data.get("tags", [])),
            dns_suffix=data.get("dns_suffix"),
            magic_dns_enabled=bool(data.get("magic_dns_enabled", False)),
            acl_ref=data.get("acl_ref"),
        )
        return rtnval
```

---

## Module Layout

```
codecraftai-networking/source/packages/ccai/networking/
  vpnoverlayprofile.py     <-- VPNOverlayProfile, SUPPORTED_VPN_PROVIDERS
  interfaces.py            (existing — extended by interface-class-vpn-overlay)
  resolution.py            (existing — extended by address-plane-resolution)
```

---

## See Also

- [vpn-client-protocol](../../../codecraftai-interfaces/specs/vpn-client-protocol/design.md)
  — `IVPNClient.bring_up` consumes the profile's `network` and `tags`.
- [vpn-control-plane-protocol](../../../codecraftai-interfaces/specs/vpn-control-plane-protocol/design.md)
  — `IVPNControlPlane.apply_acl` consumes `acl_ref`-resolved documents.
- [address-plane-resolution](../address-plane-resolution/design.md) —
  consumes `dns_suffix` + `magic_dns_enabled` when resolving overlay
  names.
- [interface-class-vpn-overlay](../interface-class-vpn-overlay/design.md)
  — `InterfaceClass.VPN_OVERLAY` is the per-NIC counterpart.

---

## Testing Strategy

- **Construction tests.** Class constructs with a complete payload;
  raises `ConfigurationError` for empty `name`, whitespace `name`,
  unknown `provider`.
- **`from_dict` tests.** Successful conversion with the YAML sample
  shape; raises with the missing-keys list when required keys are
  absent; ignores unknown keys with a warning.
- **Equality and hashing tests.** Two equally-constructed instances
  are equal and hash identically; usable as a `dict` key.
- **`effective_dns_suffix` tests.** Returns `dns_suffix` verbatim
  regardless of `magic_dns_enabled` (the flag controls overlay
  behaviour, not suffix string).
- **No property tests required** — the class is a frozen container
  with straightforward validation and no algebraic invariants. The
  derived computation that *is* property-tested lives in
  `address-plane-resolution` (`⊙`).
