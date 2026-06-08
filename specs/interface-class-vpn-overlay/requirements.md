# Requirements

## Introduction

The `interface-class-vpn-overlay` feature extends the existing
`InterfaceClass(IntEnum)` in
`codecraftai-networking/source/packages/ccai/networking/interfaces.py`
with a new `VPN_OVERLAY` member, and adds a `provider: Optional[str]`
discriminator on the interface descriptor for overlay interfaces.
This is the descriptor-level counterpart to the
`AddressPlane.OVERLAY` member added in `address-plane-types`.

Today's `InterfaceClass` covers `LOOPBACK`, `BRIDGE`, `WIRED`,
`WIRELESS`, `TUNNEL`. Tailscale's `tailscale0` interface and
Twingate's connector veth pair sit awkwardly under `TUNNEL` —
useful at the kernel level but uninformative when the framework
wants to ask "is this a mesh-VPN overlay?". Adding the
`VPN_OVERLAY` member lets device-enumeration code answer that
question directly.

**See Also:** [address-plane-types](../../../codecraftai-interfaces/specs/address-plane-types/design.md),
[vpn-overlay-profile](../vpn-overlay-profile/design.md),
[vpn-client-protocol](../../../codecraftai-interfaces/specs/vpn-client-protocol/design.md).

---

## Requirements

### Requirement 1: VPN_OVERLAY Member Added

**User Story:** As an interface-classification consumer, I want a
distinct enum value for mesh-VPN overlays so I do not have to
pattern-match interface names.

#### Acceptance Criteria

1. THE SYSTEM SHALL add `VPN_OVERLAY = 6` to `InterfaceClass`.
2. THE SYSTEM SHALL preserve every existing member's integer
   value to avoid breaking serialised configs.
3. THE SYSTEM SHALL document the integer-value-stability rule in
   the enum docstring.

---

### Requirement 2: Interface Descriptor Provider Discriminator

**User Story:** As a landscape coordinator, I want overlay
interfaces to carry their provider id so I can route to the right
`IVPNClient` without parsing the interface name.

#### Acceptance Criteria

1. THE SYSTEM SHALL add an `InterfaceDescriptor` dataclass in
   `interfaces.py` with fields:
   - `name: str`
   - `interface_class: InterfaceClass`
   - `provider: Optional[str] = None`
2. WHEN `interface_class == InterfaceClass.VPN_OVERLAY` and
   `provider` is `None` THE SYSTEM SHALL raise
   `ConfigurationError` in `__post_init__`.
3. WHEN `interface_class != InterfaceClass.VPN_OVERLAY` and
   `provider` is not `None` THE SYSTEM SHALL raise
   `ConfigurationError` (provider is only meaningful for overlays).
4. THE SYSTEM SHALL accept provider values `"tailscale"` and
   `"twingate"` from the
   `SUPPORTED_VPN_PROVIDERS` constant in
   `vpnoverlayprofile.py`.

---

### Requirement 3: Detection Helper

**User Story:** As a discovery routine, I want a small helper that
returns the `VPN_OVERLAY` class plus provider id for a given
interface name when the name is one of the well-known overlay
patterns.

#### Acceptance Criteria

1. THE SYSTEM SHALL declare
   `detect_overlay_provider(name: str) -> Optional[str]` returning
   `"tailscale"` for names matching `tailscale0` / `tailscale\\d+`
   / `utun\\d+` (macOS Tailscale), `"twingate"` for names
   matching `sdwan0` / `twingate\\d*`, and `None` otherwise.
2. THE SYSTEM SHALL document this helper as a *best-effort* hint —
   authoritative classification is the caller's responsibility
   (e.g. by consulting `IVPNClient.status`).
3. WHEN extending the pattern set THE SYSTEM SHALL keep the
   recognised-pattern list as a module-level constant
   `OVERLAY_INTERFACE_PATTERNS: Dict[str, List[str]]`.

---

### Requirement 4: No Behaviour Change for Existing Members

**User Story:** As an existing consumer of `InterfaceClass`, I want
my code to keep working unchanged.

#### Acceptance Criteria

1. THE SYSTEM SHALL leave `UNKNOWN`, `LOOPBACK`, `BRIDGE`, `WIRED`,
   `WIRELESS`, `TUNNEL` members and integer values unchanged.
2. THE SYSTEM SHALL leave existing helper functions
   (`encode_address`, `get_all_ipv4_interfaces`,
   `get_all_ipv6_interfaces`) unchanged.

---

### Requirement 5: Serialisation Round-Trip

**User Story:** As a config-loader, I want the new member to
round-trip through int / string serialisation cleanly.

#### Acceptance Criteria

1. WHEN `InterfaceClass.VPN_OVERLAY` is serialised to its integer
   value THE SYSTEM SHALL produce `6`.
2. WHEN `InterfaceClass(6)` is constructed THE SYSTEM SHALL return
   `InterfaceClass.VPN_OVERLAY`.
3. WHEN the string `"VPN_OVERLAY"` is looked up via
   `InterfaceClass["VPN_OVERLAY"]` THE SYSTEM SHALL return the
   member.
