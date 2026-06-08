# Design

## Overview

`resolve_in_plane` is the single plane-aware host-resolution entry
point in `codecraftai-networking`. It is added to the existing
`resolution.py` module, alongside the IPv6 / IPv4 helpers already
there. The function dispatches on `AddressPlane`:

- `PUBLIC` → existing public DNS resolver path.
- `PRIVATE` → existing private DNS resolver path.
- `OVERLAY` → injected `IVPNClient.peer_addresses()` then the
  overlay DNS resolver, with no fall-through to other planes.

This honours two §1 design decisions:

1. The framework MUST NOT sniff overlay CIDRs; the caller declares
   the plane.
2. `OVERLAY` is a sealed dispatch — there is no implicit fall-back
   to `PUBLIC`, because that would mask configuration mistakes.

This spec is marked **⊙**. The plane-selection dispatch is small but
load-bearing: totality across the `AddressPlane` enum, isolation of
`OVERLAY` from public resolvers, and idempotence under repeated
queries are property-testable invariants and are listed below.

**See Also:** [address-plane-types](../../../codecraftai-interfaces/specs/address-plane-types/design.md),
[vpn-client-protocol](../../../codecraftai-interfaces/specs/vpn-client-protocol/design.md),
[vpn-overlay-profile](../vpn-overlay-profile/design.md),
[overlay-dns-resolver](../../../codecraftai-interfaces/specs/vpn-client-protocol/design.md).

---

## Architecture

```
                                resolve_in_plane(name, plane, aspects,
                                                  vpn_client=None)
                                          |
                +-------------------------+-------------------------+
                |                         |                         |
        plane == PUBLIC          plane == PRIVATE          plane == OVERLAY
                |                         |                         |
                v                         v                         v
   +---------------------+     +---------------------+   +-------------------------+
   | public DNS resolver |     | private DNS resolver|   | vpn_client.peer_        |
   | (existing)          |     | (existing)          |   |   addresses().get(name) |
   +---------------------+     +---------------------+   +-----------+-------------+
                                                                     | None
                                                                     v
                                                          +---------------------------+
                                                          | OverlayDnsResolver        |
                                                          | (registered separately by |
                                                          |  overlay-dns-resolver)    |
                                                          +-----------+---------------+
                                                                     | None
                                                                     v
                                                                  return None
                                                          (NO fallback to PUBLIC/PRIVATE)
```

---

## Data Model

```python
from typing import Optional

from ccai.aspects.aspects import Aspects
from ccai.errors.exceptions import SemanticError
from ccai.interfaces.iaddressplane import AddressPlane
from ccai.interfaces.ivpnclient import IVPNClient

# OverlayDnsResolver is registered via a small module-level setter
# by overlay-dns-resolver in codecraftai-interop.
_OVERLAY_DNS_RESOLVER = None


def register_overlay_dns_resolver(*, resolver) -> None:
    """
        Registers the overlay DNS resolver instance used by resolve_in_plane
        when plane == AddressPlane.OVERLAY and vpn_client lookup misses.
    """
    global _OVERLAY_DNS_RESOLVER
    _OVERLAY_DNS_RESOLVER = resolver
    return


def resolve_in_plane(
    *,
    name: str,
    plane: AddressPlane,
    aspects: Aspects,
    vpn_client: Optional[IVPNClient] = None,
) -> Optional[str]:
    """
        Resolves `name` to an address on the requested plane.

        :param name: Host name (short or FQDN) to resolve.
        :param plane: Which plane to consult.
        :param aspects: Behaviour controls (timeout, retries, logging).
        :param vpn_client: Optional overlay client to consult first when
            plane == OVERLAY.

        :returns: Address string, or None when no resolver answers.
        :raises: SemanticError when `plane` is an unknown AddressPlane member.
    """
    if len(name) == 0:
        raise SemanticError("resolve_in_plane requires a non-empty 'name'.")

    rtnval: Optional[str] = None

    if plane == AddressPlane.PUBLIC:
        rtnval = _resolve_public(name=name, aspects=aspects)
    elif plane == AddressPlane.PRIVATE:
        rtnval = _resolve_private(name=name, aspects=aspects)
    elif plane == AddressPlane.OVERLAY:
        rtnval = _resolve_overlay(name=name, aspects=aspects, vpn_client=vpn_client)
    else:
        raise SemanticError(
            f"resolve_in_plane has no branch for AddressPlane member {plane!r}."
        )

    return rtnval


def _resolve_overlay(
    *,
    name: str,
    aspects: Aspects,
    vpn_client: Optional[IVPNClient],
) -> Optional[str]:
    rtnval: Optional[str] = None
    if vpn_client is not None:
        peers = vpn_client.peer_addresses()
        if name in peers:
            rtnval = peers[name]
    if rtnval is None and _OVERLAY_DNS_RESOLVER is not None:
        rtnval = _OVERLAY_DNS_RESOLVER.resolve(name=name, aspects=aspects)
    return rtnval
```

`_resolve_public` and `_resolve_private` wrap the existing public /
private DNS code already in `resolution.py`; they are factored out
to local helpers so the dispatch is the only thing tested.

---

## Module Layout

```
codecraftai-networking/source/packages/ccai/networking/
  resolution.py     <-- extended with resolve_in_plane,
                        register_overlay_dns_resolver,
                        _resolve_overlay, _resolve_public, _resolve_private
```

---

## See Also

- [address-plane-types](../../../codecraftai-interfaces/specs/address-plane-types/design.md)
  — supplies the `AddressPlane` enum dispatched on here.
- [vpn-client-protocol](../../../codecraftai-interfaces/specs/vpn-client-protocol/design.md)
  — `IVPNClient.peer_addresses()` is the first-class overlay source.
- [vpn-overlay-profile](../vpn-overlay-profile/design.md) — the
  static configuration whose `dns_suffix` the overlay DNS resolver
  may consult.
- [interface-class-vpn-overlay](../interface-class-vpn-overlay/design.md)
  — descriptor-level peer to this resolver-level feature.

---

## Testing Strategy

This feature is marked **⊙** — property tests are required.

### Example-based tests

- `test_public_plane_delegates_to_public_resolver`.
- `test_private_plane_delegates_to_private_resolver`.
- `test_overlay_plane_consults_vpn_client_first`.
- `test_overlay_plane_falls_through_to_overlay_dns_resolver`.
- `test_overlay_plane_returns_none_when_no_resolver_available`.
- `test_overlay_plane_does_not_fall_through_to_public`.
- `test_empty_name_raises_semantic_error`.
- `test_unknown_plane_raises_semantic_error`.
- `test_no_cidr_sniffing_in_dispatch` — review-style test asserting
  that no branch reads CIDR ranges from the resolved address.

### Property-based tests (hypothesis)

Generators:

- `plane_strategy = sampled_from(list(AddressPlane))`
- `name_strategy = text(min_size=1, max_size=64)`
- `mock_peer_map = dictionaries(name_strategy, text(min_size=1, max_size=39))`

Properties:

- **P1 — Totality.** For any `plane ∈ AddressPlane` and any
  non-empty `name`, `resolve_in_plane` returns `Optional[str]` and
  does not raise.
- **P2 — Plane isolation.** For any `name`, asking for `OVERLAY`
  with a mock `vpn_client` that has no entry for `name` and no
  overlay DNS resolver registered returns `None` even if the
  public resolver mock would have returned a value for the same
  name. (`OVERLAY` MUST NOT fall through.)
- **P3 — Idempotence.** For any input tuple
  `(name, plane, vpn_client_state)`, repeated calls to
  `resolve_in_plane` with the same inputs return the same value
  (read-only mocks).
- **P4 — vpn_client first.** For any `name` that exists in the mock
  `peer_addresses()` map, asking for `OVERLAY` returns the value
  from the map regardless of whether an overlay DNS resolver is
  registered.
- **P5 — Public resolver not consulted under OVERLAY.** Build a
  mock public resolver that records calls; for any `name` and
  `OVERLAY`, the call count on that mock remains zero.

`hypothesis` is added to the test-only dependency set for this
package.
