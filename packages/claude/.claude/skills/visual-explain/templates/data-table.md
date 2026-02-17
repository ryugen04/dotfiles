# Requirements Audit

Reference template for data tables and comparison views in Markdown format. Demonstrates:
- KPI summary cards (using tables with bold values)
- Status indicators with emoji
- Detailed comparison tables
- Collapsible gap analysis sections
- Legend and summary rows

---

## 📊 Summary

| Metric | Value |
|--------|-------|
| Items Reviewed | **14** |
| Match | **13** ✅ |
| Gap | **1** ❌ |
| Partial | **0** ⚠️ |
| Coverage | **93%** |

---

## Legend

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| ✅ Match | Requirement fully addressed | None |
| ❌ Gap | Requirement not addressed | Must fix before ship |
| ⚠️ Partial | Partially addressed | Review and decide |

---

## Detailed Comparison

| # | Request | Plan | Status |
|---|---------|------|--------|
| 1 | Template: `yoth-special-edition` only | Plan scopes everything to this template | ✅ Match |
| 2 | EOD tomorrow (Friday), Tuesday AM launch | Plan header says same | ✅ Match |
| 3 | Update BIS button label and pop up text | Button text + modal description configurable via settings | ✅ Match |
| 4 | Use Stoq's API to trigger events | Uses `openInlineForm`, `openModal`, `removeInlineForm` | ✅ Match |
| 5 | Custom button + modal with text settings in buy buttons block | Schema settings in `buy_buttons` block | ✅ Match |
| 6 | Default values = current behavior when empty | Blank settings = Stoq default "Notify Me" behavior | ✅ Match |
| 7 | Only display for OOS variants | DOM-based sold-out detection | ✅ Match |
| 8 | Exclude products with `excludebis` tag | Checked in both PDP and PLP Liquid | ✅ Match |
| 9 | `openInlineForm` to load Stoq form in modal | PDP modal uses `openInlineForm` | ✅ Match |
| 10 | Updated Button Label: "Join the waitlist" | Pre-populated in template JSON | ✅ Match |
| 11 | Updated Pop Up Text: "Sign up to be notified when we restock..." | `bis_modal_description` setting | ✅ Match |
| 12 | Theme: Huha 2.0 - Giddy Up Collection D2C Launch | Clone ID `145580556374` | ✅ Match |
| 13 | Changes made locally | Local dev + theme push | ✅ Match |
| 14 | Run `stoq:restock-modal:submitted` when form is submitted | **Not mentioned in plan** | ❌ Gap |

---

## Summary by Category

| Category | Match | Gap | Partial |
|----------|-------|-----|---------|
| UI/UX Requirements | 5 | 0 | 0 |
| API Integration | 3 | 1 | 0 |
| Configuration | 3 | 0 | 0 |
| Deployment | 2 | 0 | 0 |
| **Total** | **13** | **1** | **0** |

---

## Gap Analysis

<details>
<summary>❌ Gap #1: `stoq:restock-modal:submitted` event</summary>

### Issue

Michael explicitly requests firing the `stoq:restock-modal:submitted` event on form submission. The plan uses Stoq's `openInlineForm` inside a custom modal, but doesn't address whether Stoq dispatches this event automatically in that context.

### Risk Assessment

| Factor | Level |
|--------|-------|
| Severity | 🟡 Medium |
| Likelihood | 🔴 High |
| Impact | Customer-facing analytics may break |

### Affected Systems

- Klaviyo email automation (listens for this event)
- Google Analytics enhanced ecommerce
- Theme JS showing success state

### Recommendation

Add an explicit `dispatchEvent` call as a safety net after the Stoq form submission callback:

```javascript
// After Stoq form submission succeeds
window.dispatchEvent(new CustomEvent('stoq:restock-modal:submitted', {
  detail: { productId, variantId, email }
}));
```

### Status

- [ ] Verify if Stoq fires event automatically with `openInlineForm`
- [ ] Add fallback `dispatchEvent` if not
- [ ] Test with Klaviyo integration

</details>

---

## Verification Steps

<details>
<summary>✅ How This Audit Was Conducted</summary>

1. **Source Documents**
   - Michael's email dated 2024-01-15
   - Implementation plan v2.1

2. **Methodology**
   - Each line item from the email extracted verbatim
   - Cross-referenced against plan sections
   - Status assigned based on explicit coverage

3. **Assumptions**
   - "Match" requires explicit mention in plan
   - Implicit coverage marked as "Partial"
   - No mention marked as "Gap"

4. **Reviewer**
   - Initial audit: AI Assistant
   - Verification: Pending human review

</details>

---

## Next Steps

| Priority | Action | Owner | Due |
|----------|--------|-------|-----|
| 🔴 High | Resolve Gap #1 (event dispatch) | Dev Team | Before merge |
| 🟡 Medium | Add integration test for Stoq events | QA | Before staging |
| 🔵 Low | Document event flow for future reference | Tech Writer | Post-launch |

---

> **Summary:** 14 items reviewed. 13 match (93%), 1 gap identified requiring resolution before ship. Overall coverage is good but the event dispatch gap is critical for downstream integrations.
