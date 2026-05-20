# Design

## Overview

This feature is the descriptor-level peer to
`AddressPlane.OVERLAY`. It extends the existing
`InterfaceClass(IntEnum)` in
`automojo-networking/source/packages/automojo/networking/interfaces.py`
with `VPN_OVERLAY = 6`, introduces an `InterfaceDescriptor` dataclass
that carries an `Optional[str] provider` discriminator (mandatory for
overlay interfaces, forbidden for non-overlay), and adds a small
best-effort `detect_overlay_provider(name)` helper for discovery
routines.

The change is additive: every existing member of `InterfaceClass`
retains its integer value so serialised configs continue to load.

**See Also:** [address-plane-types](../../../automojo-interfaces/specs/address-plane-types/design.md),
[vpn-overlay-profile](../vpn-overlay-profile/design.md).

---

## Architecture

```
+---------------------------------------------+
| InterfaceClass (IntEnum)                    |
|   UNKNOWN   = 0    (unchanged)              |
|   LOOPBACK  = 1    (unchanged)              |
|   BRIDGE    = 2    (unchanged)              |
|   WIRED     = 3    (unchanged)              |
|   WIRELESS  = 4    (unchanged)              |
|   TUNNEL    = 5    (unchanged)              |
|   VPN_OVERLAY = 6  (NEW)                    |
+----------------+----------------------------+
                 |
                 v
+---------------------------------------------+
| InterfaceDescriptor (frozen dataclass)      |
|   name: str                                 |
|   interface_class: InterfaceClass           |
|   provider: Optional[str]                   |
|   __post_init__: enforces                   |
|     (VPN_OVERLAY <=> provider is not None)  |
+---------------------------------------------+
                 ^
                 |
+---------------------------------------------+
| detect_overlay_provider(name)               |
|  uses OVERLAY_INTERFACE_PATTERNS dict       |
|  returns "tailscale" / "twingate" / None    |
+---------------------------------------------+
```

---

## Data Model

```python
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, List, Optional

from automojo.errors.exceptions import ConfigurationError
from automojo.networking.vpnoverlayprofile import SUPPORTED_VPN_PROVIDERS


class InterfaceClass(IntEnum):
    """
        Enumeration of network interface classes.

        Integer values are stable across releases for serialisation
        compatibility. New members append; existing members never
        renumber.
    """
    UNKNOWN = 0
    LOOPBACK = 1
    BRIDGE = 2
    WIRED = 3
    WIRELESS = 4
    TUNNEL = 5
    VPN_OVERLAY = 6


OVERLAY_INTERFACE_PATTERNS: Dict[str, List[str]] = {
    "tailscale": [r"^tailscale\d+$", r"^utun\d+$"],
    "twingate":  [r"^sdwan\d*$",     r"^twingate\d*$"],
}


@dataclass(frozen=True)
class InterfaceDescriptor:
    """
        Describes a single network interface for landscape and
        discovery code.

        :param name: OS-level interface name (e.g. "eth0", "tailscale0").
        :param interface_class: One of InterfaceClass.
        :param provider: Required when interface_class == VPN_OVERLAY;
            must be None otherwise.
    """
    name: str
    interface_class: InterfaceClass
    provider: Optional[str] = None

    def __post_init__(self) -> None:
        is_overlay = self.interface_class == InterfaceClass.VPN_OVERLAY
        if is_overlay and self.provider is None:
            raise ConfigurationError(
                "InterfaceDescriptor with interface_class=VPN_OVERLAY requires "
                "a non-None 'provider'."
            )
        if not is_overlay and self.provider is not None:
            raise ConfigurationError(
                "InterfaceDescriptor 'provider' is only valid when "
                "interface_class == VPN_OVERLAY."
            )
        if is_overlay and self.provider not in SUPPORTED_VPN_PROVIDERS:
            raise ConfigurationError(
                "InterfaceDescriptor 'provider' must be one of "
                f"{SUPPORTED_VPN_PROVIDERS}; got {self.provider!r}."
            )
        return


def detect_overlay_provider(*, name: str) -> Optional[str]:
    """
        Best-effort: returns the overlay provider id for a well-known
        interface name pattern, or None.

        :param name: Interface name.

        :returns: "tailscale" / "twingate" / None.
    """
    import re
    rtnval: Optional[str] = None
    for provider, patterns in OVERLAY_INTERFACE_PATTERNS.items():
        for pat in patterns:
            if re.match(pat, name):
                rtnval = provider
                break
        if rtnval is not None:
            break
    return rtnval
```

---

## Module Layout

```
automojo-networking/source/packages/automojo/networking/
  interfaces.py     <-- extended in place: InterfaceClass.VPN_OVERLAY,
                        InterfaceDescriptor, OVERLAY_INTERFACE_PATTERNS,
                        detect_overlay_provider
  vpnoverlayprofile.py  (sibling spec — supplies SUPPORTED_VPN_PROVIDERS)
```

---

## See Also

- [address-plane-types](../../../automojo-interfaces/specs/address-plane-types/design.md)
  — `AddressPlane.OVERLAY` is the address-level peer of
  `InterfaceClass.VPN_OVERLAY`.
- [vpn-overlay-profile](../vpn-overlay-profile/design.md) —
  supplies `SUPPORTED_VPN_PROVIDERS`.
- [vpn-client-protocol](../../../automojo-interfaces/specs/vpn-client-protocol/design.md)
  — authoritative provider classification at runtime.

---

## Testing Strategy

- **Member presence test.** `InterfaceClass.VPN_OVERLAY` exists with
  integer value `6`.
- **Member stability test.** Each pre-existing member's integer value
  is unchanged.
- **Descriptor positive tests.** Construction succeeds for
  `(name="eth0", interface_class=WIRED, provider=None)` and for
  `(name="tailscale0", interface_class=VPN_OVERLAY,
  provider="tailscale")`.
- **Descriptor negative tests.** `ConfigurationError` raised when
  `VPN_OVERLAY` is paired with `provider=None`; when a non-overlay
  class is paired with a non-`None` provider; when `provider` is an
  unsupported string.
- **`detect_overlay_provider` table tests.** `tailscale0` →
  `"tailscale"`; `utun3` → `"tailscale"`; `sdwan0` → `"twingate"`;
  `twingate1` → `"twingate"`; `eth0` → `None`.
- **Serialisation round-trip tests.** `int(VPN_OVERLAY) == 6`;
  `InterfaceClass(6) is VPN_OVERLAY`;
  `InterfaceClass["VPN_OVERLAY"] is VPN_OVERLAY`.
- **No property tests required** — the dispatch is small, the
  pattern table is data, and there is no complex computation.
