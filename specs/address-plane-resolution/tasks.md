# Implementation Plan — Address Plane Resolution

## Module and Models

- [x] 1. Open `codecraftai-networking/source/packages/ccai/networking/resolution.py`
  for in-place extension.
- [x] 2. Add module-level `_OVERLAY_DNS_RESOLVER = None`.
- [x] 3. Add `register_overlay_dns_resolver(*, resolver)` setter.
- [x] 4. Add Sphinx-style docstrings on every new public symbol.

## resolve_in_plane — To Implement

- [x] 5. Implement `resolve_in_plane(*, name, plane, aspects,
  vpn_client=None) -> Optional[str]` with the four-branch dispatch
  (`PUBLIC` / `PRIVATE` / `OVERLAY` / `else: raise SemanticError`).
- [x] 6. Implement `_resolve_overlay(*, name, aspects, vpn_client)`
  consulting `vpn_client.peer_addresses()` first, then
  `_OVERLAY_DNS_RESOLVER` if registered.
- [x] 7. Factor existing public-DNS code into `_resolve_public(*,
  name, aspects)` and existing private-DNS code into
  `_resolve_private(*, name, aspects)` without behaviour change.
- [x] 8. Confirm `OVERLAY` never falls back to public or private.
- [x] 9. Wrap underlying resolvers that do not natively accept
  Aspects with the standard timeout helper, honouring
  `aspects.connection_timeout`.

## Testing

- [x] 10. `test_public_plane_delegates_to_public_resolver`.
- [x] 11. `test_private_plane_delegates_to_private_resolver`.
- [x] 12. `test_overlay_plane_consults_vpn_client_first`.
- [x] 13. `test_overlay_plane_falls_through_to_overlay_dns_resolver`.
- [x] 14. `test_overlay_plane_returns_none_when_no_resolver_available`.
- [x] 15. `test_overlay_plane_does_not_fall_through_to_public`.
- [x] 16. `test_empty_name_raises_semantic_error`.
- [x] 17. `test_unknown_plane_raises_semantic_error`.
- [x] 18. `test_no_cidr_sniffing_in_dispatch` (review-style).
- [x] 19. Add `hypothesis` to the test-only dependency set.
- [x] 20. **Property P1 — Totality** (hypothesis).
- [x] 21. **Property P2 — Plane isolation (OVERLAY no fall-through)**
  (hypothesis).
- [x] 22. **Property P3 — Idempotence under repeated calls** (hypothesis).
- [x] 23. **Property P4 — vpn_client consulted before DNS resolver**
  (hypothesis).
- [x] 24. **Property P5 — Public resolver never consulted under OVERLAY**
  (hypothesis).
