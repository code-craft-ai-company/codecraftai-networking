# Requirements

## Introduction

The `address-plane-resolution` feature adds plane-aware host
resolution to `automojo-networking`. It introduces the
`resolve_in_plane(name, plane, aspects)` helper and the local
`AddressPlane` re-export, so call sites can ask "give me a reachable
address for `name` on plane `OVERLAY`" without hard-wiring Tailscale
CIDR detection or any other vendor specifics.

Per §1 of `PLAN-VPN-AND-CLOUD-PROVISIONING.md`, the framework MUST
NOT hard-wire `100.64.0.0/10` detection. Instead, the caller
declares which plane it wants and the helper delegates: `PUBLIC` and
`PRIVATE` resolve through existing DNS/host resolvers (already in
`resolution.py`); `OVERLAY` delegates to an injected `IVPNClient` or
to the overlay DNS resolver.

This feature is marked **⊙** — property tests are required. The
plane-selection logic is total and ordering-sensitive (fall-through
through resolvers), which calls for hypothesis coverage.

**See Also:** [address-plane-types](../../../automojo-interfaces/specs/address-plane-types/design.md),
[vpn-client-protocol](../../../automojo-interfaces/specs/vpn-client-protocol/design.md),
[vpn-overlay-profile](../vpn-overlay-profile/design.md).

---

## Requirements

### Requirement 1: `resolve_in_plane` Entry Point

**User Story:** As an SSH/DNS/file-ops caller, I want a single
function that returns a reachable address for a name on a chosen
plane.

#### Acceptance Criteria

1. THE SYSTEM SHALL declare
   `resolve_in_plane(name, plane, aspects, vpn_client=None) -> Optional[str]`
   in `automojo-networking/source/packages/automojo/networking/resolution.py`.
2. THE SYSTEM SHALL require `name: str` non-empty.
3. THE SYSTEM SHALL require `plane: AddressPlane`.
4. THE SYSTEM SHALL require `aspects: Aspects`.
5. THE SYSTEM SHALL accept an optional
   `vpn_client: Optional[IVPNClient] = None` keyword.

---

### Requirement 2: Plane Selection — PUBLIC

**User Story:** As a caller asking for `PUBLIC` resolution, I want
public DNS / hostname lookup behaviour unchanged from today.

#### Acceptance Criteria

1. WHEN `plane == AddressPlane.PUBLIC` THE SYSTEM SHALL delegate to
   the existing public DNS resolver (`socket.gethostbyname` /
   `getaddrinfo` patterns already present in `resolution.py`).
2. WHEN the public resolver returns no answer THE SYSTEM SHALL
   return `None` (no exception; callers decide).
3. THE SYSTEM SHALL NOT consult the overlay resolver under
   `PUBLIC`.

---

### Requirement 3: Plane Selection — PRIVATE

**User Story:** As a caller asking for `PRIVATE` resolution, I want
private-DNS / VPC lookup behaviour unchanged from today.

#### Acceptance Criteria

1. WHEN `plane == AddressPlane.PRIVATE` THE SYSTEM SHALL delegate
   to the existing private-DNS resolver path.
2. THE SYSTEM SHALL NOT consult the overlay resolver under
   `PRIVATE`.

---

### Requirement 4: Plane Selection — OVERLAY

**User Story:** As a caller asking for `OVERLAY` resolution, I want
the overlay DNS / control-plane lookup to drive the answer.

#### Acceptance Criteria

1. WHEN `plane == AddressPlane.OVERLAY` and `vpn_client is not None`
   THE SYSTEM SHALL consult `vpn_client.peer_addresses().get(name)`
   first.
2. WHEN `plane == AddressPlane.OVERLAY` and the peer lookup returns
   nothing THE SYSTEM SHALL consult the overlay DNS resolver
   (registered separately by `overlay-dns-resolver`).
3. WHEN `plane == AddressPlane.OVERLAY` and `vpn_client is None`
   and no overlay resolver is registered THE SYSTEM SHALL return
   `None`.
4. THE SYSTEM SHALL NOT fall through from `OVERLAY` to public or
   private resolution — if the caller asked for `OVERLAY`, an
   answer outside the overlay is wrong.

---

### Requirement 5: Plane Totality

**User Story:** As a caller, I want the function to be defined for
every `AddressPlane` value.

#### Acceptance Criteria

1. THE SYSTEM SHALL accept every member of `AddressPlane`.
2. IF a future `AddressPlane` member is added that has no resolver
   branch THEN THE SYSTEM SHALL raise `SemanticError` (this is API
   misuse — the framework must be updated).

---

### Requirement 6: No Hard-Wired Overlay CIDR Detection

**User Story:** As a framework maintainer, I want plane selection
to be driven by the caller's declaration, not by sniffing the
returned address.

#### Acceptance Criteria

1. THE SYSTEM SHALL NOT inspect any candidate address's CIDR to
   decide which plane it belongs to.
2. IF a future change adds CIDR-based plane sniffing to
   `resolve_in_plane` THEN THE SYSTEM SHALL be considered non-
   conformant per §1 of the design plan.

---

### Requirement 7: Aspects Passthrough

**User Story:** As a caller, I want timeouts and retries on the
underlying resolvers to be controlled by my `aspects`.

#### Acceptance Criteria

1. THE SYSTEM SHALL pass `aspects` to every underlying resolver
   call that accepts one.
2. IF a resolver does not accept Aspects (e.g. `socket.getaddrinfo`)
   THEN THE SYSTEM SHALL honour
   `aspects.connection_timeout` by wrapping the call with the
   standard timeout helper used elsewhere in `resolution.py`.
