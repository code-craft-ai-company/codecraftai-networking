# Implementation Plan — Interface Class VPN Overlay

## Module and Models

- [x] 1. Open `codecraftai-networking/source/packages/ccai/networking/interfaces.py`
  for in-place extension.
- [x] 2. Add `VPN_OVERLAY = 6` member to `InterfaceClass`; preserve
  every existing member's integer value.
- [x] 3. Update `InterfaceClass` docstring to declare the integer-
  value-stability rule for downstream serialisation.
- [x] 4. Add `OVERLAY_INTERFACE_PATTERNS: Dict[str, List[str]]`
  module constant seeded with Tailscale and Twingate patterns.
- [x] 5. Define `InterfaceDescriptor(frozen=True)` dataclass with
  `name`, `interface_class`, `provider`.

## InterfaceDescriptor — To Implement

- [x] 6. Implement `__post_init__` enforcing the bidirectional
  invariant: `interface_class == VPN_OVERLAY` <=> `provider is not None`;
  and `provider in SUPPORTED_VPN_PROVIDERS` when set. Raise
  `ConfigurationError` on any violation with descriptive messages.
- [x] 7. Add Sphinx-style class docstring.

## detect_overlay_provider — To Implement

- [x] 8. Implement `detect_overlay_provider(*, name)` matching the
  patterns in `OVERLAY_INTERFACE_PATTERNS` and returning the first
  matching provider id, or `None`.
- [x] 9. Add Sphinx-style docstring noting this is a best-effort
  hint, not authoritative classification.

## Testing

- [x] 10. `test_vpn_overlay_member_present_with_value_6`.
- [x] 11. `test_existing_members_unchanged`.
- [x] 12. `test_descriptor_wired_no_provider_ok`.
- [x] 13. `test_descriptor_overlay_with_provider_ok`.
- [x] 14. `test_descriptor_overlay_without_provider_raises`.
- [x] 15. `test_descriptor_non_overlay_with_provider_raises`.
- [x] 16. `test_descriptor_overlay_unsupported_provider_raises`.
- [x] 17. `test_detect_overlay_provider_table` — table-driven test
  for `tailscale0`, `utun3`, `sdwan0`, `twingate1`, `eth0`.
- [x] 18. `test_interface_class_serialisation_round_trip`.
