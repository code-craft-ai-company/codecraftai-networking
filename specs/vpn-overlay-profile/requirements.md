# Requirements

## Introduction

The `vpn-overlay-profile` feature adds the `VPNOverlayProfile`
data class to `codecraftai-networking`. A profile describes a mesh-VPN
overlay (provider, network/tailnet identifier, default tags, DNS
suffix, MagicDNS toggle, ACL reference) and is consumed by landscape
and provisioning code to bring hosts onto the correct overlay
without scattering vendor strings through call sites.

The class is data-only — no I/O, no credentials, no client
references. Credentials are looked up by category from
`codecraftai-credentials` at use time (per §8 commitment "Credentials
are values, not strings").

**See Also:** [vpn-client-protocol](../../../codecraftai-interfaces/specs/vpn-client-protocol/design.md),
[address-plane-resolution](../address-plane-resolution/design.md),
[interface-class-vpn-overlay](../interface-class-vpn-overlay/design.md).

---

## Requirements

### Requirement 1: Overlay Profile Data Model

**User Story:** As a landscape author, I want a single typed value
that captures an overlay so I can reference it by name from
`landscape.yaml` and from `VPNJoinSpec`.

#### Acceptance Criteria

1. THE SYSTEM SHALL define `VPNOverlayProfile` as a frozen
   `@dataclass` with the following fields:
   - `name: str`
   - `provider: str` (one of `"tailscale"`, `"twingate"`)
   - `network: str` (tailnet name or Twingate network slug)
   - `tags: List[str]`
   - `dns_suffix: Optional[str]`
   - `magic_dns_enabled: bool = False`
   - `acl_ref: Optional[str] = None`
2. THE SYSTEM SHALL place the class in
   `codecraftai-networking/source/packages/ccai/networking/vpnoverlayprofile.py`.

---

### Requirement 2: Provider Validation

**User Story:** As a config-loader, I want construction to fail
loudly when the provider string is unknown so typos do not silently
fall through.

#### Acceptance Criteria

1. WHEN `provider` is not one of the known values (`"tailscale"`,
   `"twingate"`) THE SYSTEM SHALL raise `ConfigurationError` in
   `__post_init__` with a message listing the supported providers.
2. THE SYSTEM SHALL declare the supported set as a module-level
   constant `SUPPORTED_VPN_PROVIDERS = ("tailscale", "twingate")`.

---

### Requirement 3: Name Validation

**User Story:** As a config-loader, I want construction to fail
when the profile name is empty or non-DNS-label-shaped so YAML
references behave predictably.

#### Acceptance Criteria

1. WHEN `name` is empty THE SYSTEM SHALL raise `ConfigurationError`.
2. WHEN `name` contains whitespace THE SYSTEM SHALL raise
   `ConfigurationError`.
3. THE SYSTEM SHALL document that the name is used as a YAML
   reference key elsewhere (e.g. `devices[*].vpn_join.profile_name`).

---

### Requirement 4: MagicDNS / DNS Suffix Coherence

**User Story:** As a network resolver, I want the profile to make
the MagicDNS-vs-DNS-suffix interaction explicit so I do not have to
infer it.

#### Acceptance Criteria

1. WHEN `magic_dns_enabled` is `True` and `dns_suffix` is `None`
   THE SYSTEM SHALL accept the profile (MagicDNS supplies its own
   suffix).
2. WHEN `magic_dns_enabled` is `False` and the caller queries
   `effective_dns_suffix()` THE SYSTEM SHALL return `dns_suffix`
   verbatim (which may be `None`).
3. WHERE `provider == "twingate"` THE SYSTEM SHALL allow
   `magic_dns_enabled=True` to mean "use Twingate-resolved FQDNs"
   even though Twingate does not literally use MagicDNS — the flag
   names the behaviour, not the implementation.

---

### Requirement 5: Frozen, Hashable, Equal-By-Fields

**User Story:** As a registry maintainer, I want profiles to be
usable as dict keys and compared by value, so I can dedupe.

#### Acceptance Criteria

1. THE SYSTEM SHALL declare the dataclass as `frozen=True`.
2. THE SYSTEM SHALL declare the dataclass as `eq=True` (default).
3. THE SYSTEM SHALL be hashable (a consequence of `frozen=True`).

---

### Requirement 6: From-Dict Constructor

**User Story:** As a YAML loader, I want a single classmethod that
converts a parsed dict into a `VPNOverlayProfile`.

#### Acceptance Criteria

1. THE SYSTEM SHALL provide
   `classmethod from_dict(cls, data: dict) -> VPNOverlayProfile`.
2. THE SYSTEM SHALL raise `ConfigurationError` listing every
   missing required key when `data` is incomplete.
3. THE SYSTEM SHALL ignore unknown keys (forward-compat) but log a
   warning via the standard logger.
