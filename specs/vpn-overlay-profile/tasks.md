# Implementation Plan — VPN Overlay Profile

## Module and Models

- [x] 1. Create `automojo-networking/source/packages/automojo/networking/vpnoverlayprofile.py`.
- [x] 2. Add `SUPPORTED_VPN_PROVIDERS = ("tailscale", "twingate")`
  module constant.
- [x] 3. Define `VPNOverlayProfile(frozen=True)` dataclass with the
  seven fields listed in the design.
- [x] 4. Add Sphinx-style module and class docstrings.

## VPNOverlayProfile — To Implement

- [x] 5. Implement `__post_init__` validating `name` (non-empty,
  no whitespace) and `provider` (in `SUPPORTED_VPN_PROVIDERS`); raise
  `ConfigurationError` with descriptive messages.
- [x] 6. Implement `effective_dns_suffix() -> Optional[str]` returning
  `dns_suffix` verbatim (assigned to a local before returning).
- [x] 7. Implement `classmethod from_dict(cls, *, data: dict)` that
  validates required keys (`name`, `provider`, `network`), constructs
  the instance, ignores unknown keys (with a logger warning).
- [x] 8. Confirm dataclass is `frozen=True` (hashable, equal-by-value).
- [x] 9. Add `__all__ = ["VPNOverlayProfile", "SUPPORTED_VPN_PROVIDERS"]`.

## Testing

- [x] 10. `test_construction_with_complete_payload`.
- [x] 11. `test_construction_empty_name_raises`.
- [x] 12. `test_construction_whitespace_name_raises`.
- [x] 13. `test_construction_unknown_provider_raises`.
- [x] 14. `test_from_dict_round_trip`.
- [x] 15. `test_from_dict_missing_keys_raises_with_list`.
- [x] 16. `test_from_dict_ignores_unknown_keys_with_warning`.
- [x] 17. `test_equal_profiles_hash_identically`.
- [x] 18. `test_effective_dns_suffix_returns_field_verbatim`.
- [x] 19. `test_magic_dns_enabled_with_no_suffix_accepted`.
