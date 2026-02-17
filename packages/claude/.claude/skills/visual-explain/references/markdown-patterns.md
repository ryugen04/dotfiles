# Markdown Patterns for Visual Documentation

Reusable patterns for creating visual documentation in Markdown format. These patterns work natively in GitHub, GitLab, VS Code, and most Markdown viewers.

## Status Indicators

Use emoji consistently for status badges. These render reliably across all platforms.

### Standard Status Set

| Emoji | Meaning | Usage |
|-------|---------|-------|
| ✅ | Match / Pass / Complete / Good | Confirmed, working, addressed |
| ❌ | Gap / Fail / Missing / Bad | Not addressed, broken, failed |
| ⚠️ | Partial / Warning / Ugly | Incomplete, needs attention, concern |
| ℹ️ | Info / Neutral / Context | Informational, current state |
| ❓ | Question / Unknown | Needs clarification |
| 🔄 | In Progress | Currently working on |
| 🚫 | Blocked | Cannot proceed |
| ✨ | New | Newly added |
| 📝 | Modified | Changed |
| 🗑️ | Deleted | Removed |

### Severity Indicators

| Emoji | Level | Usage |
|-------|-------|-------|
| 🔴 | High | Critical, must address |
| 🟡 | Medium | Should address |
| 🔵 | Low | Nice to have |

### Example Usage in Tables

```markdown
| Requirement | Status |
|-------------|--------|
| Authentication | ✅ Match |
| Authorization | ⚠️ Partial |
| Logging | ❌ Gap |
| Monitoring | 🔄 In Progress |
```

## Tables

### Basic Table

```markdown
| Column A | Column B | Column C |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |
```

### Column Alignment

```markdown
| Left Aligned | Center Aligned | Right Aligned |
|:-------------|:--------------:|--------------:|
| Text         | Text           | Numbers       |
| More text    | More text      | 1,234         |
```

### KPI / Metrics Dashboard

Use bold values and clear labels. This pattern replaces styled KPI cards:

```markdown
## 📊 Impact Dashboard

| Metric | Value |
|--------|-------|
| Lines Added | **+247** |
| Lines Removed | **-89** |
| Files Changed | **12** |
| Test Coverage | **94%** ✅ |
| CHANGELOG Updated | ✅ |
| Docs Updated | ⚠️ |
```

Alternative inline format for compact display:

```markdown
**Lines:** +247 / -89 | **Files:** 12 | **Tests:** 8 new | **Coverage:** 94% ✅
```

### Comparison Table

For before/after or side-by-side comparisons:

```markdown
| Aspect | Before | After |
|--------|--------|-------|
| Performance | 2.3s | **0.8s** ✅ |
| Bundle Size | 450KB | **320KB** ✅ |
| Dependencies | 24 | **18** ✅ |
| Complexity | Low | Medium ⚠️ |
```

### Wide Tables with Many Columns

For tables that might overflow, consider:
1. Abbreviate column headers
2. Use code blocks for long values
3. Split into multiple tables

```markdown
| File | Status | Lines | Notes |
|------|--------|-------|-------|
| `src/auth.ts` | 📝 | +45/-12 | Refactored token handling |
| `src/api.ts` | ✨ | +120 | New endpoint |
| `tests/auth.test.ts` | 📝 | +30 | Added test cases |
```

### Summary Row Pattern

Use a horizontal rule and bold to indicate totals:

```markdown
| Item | Count |
|------|-------|
| Matches | 13 |
| Gaps | 1 |
| Partial | 2 |
| **Total** | **16** |
```

## Collapsible Sections

The `<details>` tag works in GitHub, GitLab, and most Markdown viewers. Use for secondary content that shouldn't dominate the page.

### Basic Collapsible

```markdown
<details>
<summary>Click to expand</summary>

Content goes here. You can include:
- Lists
- Code blocks
- Tables
- More markdown

</details>
```

**Important:** Leave a blank line after `<summary>` and before `</details>` for proper Markdown rendering inside.

### File Map Pattern

```markdown
<details>
<summary>📁 File Map (14 files changed)</summary>

| File | Status | Changes |
|------|--------|---------|
| `src/index.ts` | 📝 | +25/-10 |
| `src/utils.ts` | ✨ | +80 |
| `src/deprecated.ts` | 🗑️ | -120 |
| `tests/index.test.ts` | 📝 | +40/-5 |

</details>
```

### Before/After Comparison

```markdown
<details>
<summary>📋 Before (Previous Implementation)</summary>

```typescript
// Old approach using callbacks
function processData(data, callback) {
  fetchData(data, (err, result) => {
    if (err) callback(err);
    else callback(null, transform(result));
  });
}
```

</details>

<details>
<summary>📋 After (New Implementation)</summary>

```typescript
// New approach using async/await
async function processData(data) {
  const result = await fetchData(data);
  return transform(result);
}
```

</details>
```

### Decision Log Card

```markdown
<details>
<summary>🔹 Decision: Use PostgreSQL over MongoDB</summary>

**Decision:** Chose PostgreSQL as the primary database.

**Rationale:** Strong ACID compliance needed for financial transactions. Better support for complex queries and joins.

**Alternatives Considered:**
- **MongoDB:** Rejected due to eventual consistency model not suitable for financial data
- **MySQL:** Considered but PostgreSQL has better JSON support for flexible schemas

**Confidence:** ✅ High (explicitly discussed in architecture review)

</details>
```

### Nested Collapsibles

```markdown
<details>
<summary>📁 Module A</summary>

Overview of Module A...

<details>
<summary>📄 Component Details</summary>

Detailed component information...

</details>

</details>
```

## Code Blocks

### With Language Highlighting

````markdown
```typescript
function greet(name: string): string {
  return `Hello, ${name}!`;
}
```
````

### Diff Format

Show changes inline:

````markdown
```diff
- const oldValue = 'before';
+ const newValue = 'after';
  const unchanged = 'same';
```
````

### File Path Header

```markdown
**`src/components/Button.tsx`**
```typescript
export function Button({ onClick, children }) {
  return <button onClick={onClick}>{children}</button>;
}
```
```

### Inline Code References

```markdown
Use `functionName()` to call the method.
The file is located at `src/components/Button.tsx`.
See `processData` in `worker.ts:45`.
```

## Blockquotes

### Simple Callout

```markdown
> **Note:** This is an important note about the implementation.
```

### Warning Callout

```markdown
> ⚠️ **Warning:** This operation cannot be undone.
```

### Multi-line Callout

```markdown
> **Important:** This affects multiple systems.
>
> - System A depends on this value
> - System B caches this result
> - Changes require coordinated deployment
```

### Nested Quotes for Attribution

```markdown
> The implementation follows the specification:
>
> > "All requests must include a valid authentication token."
> > — API Documentation v2.3
```

## Lists

### Structured Information

```markdown
- **Key invariants:**
  - Cleanup must be called before session switch
  - Token refresh happens automatically after 50 minutes
  - Cache invalidation is eventual (up to 5 seconds)

- **Non-obvious coupling:**
  - Feed renderer reads events from overlay module
  - Config changes require server restart
  - Database migrations run before app startup
```

### Task Lists

```markdown
- [x] Implement authentication
- [x] Add unit tests
- [ ] Update documentation
- [ ] Deploy to staging
```

### Numbered Steps

```markdown
1. Clone the repository
2. Install dependencies: `npm install`
3. Configure environment variables
4. Run migrations: `npm run migrate`
5. Start the server: `npm start`
```

## Headings Structure

Use consistent heading hierarchy:

```markdown
# Document Title

Brief introduction or context.

## 1. First Major Section

Content...

### 1.1 Subsection

More detail...

## 2. Second Major Section

Content...
```

## Horizontal Rules

Use to separate major sections:

```markdown
## Section One

Content...

---

## Section Two

Content...
```

## Links and References

### Internal Document Links

```markdown
See [Architecture Overview](#architecture-overview) for details.
Jump to [Risk Assessment](#risk-assessment).
```

### External Links

```markdown
Based on [RFC 7231](https://tools.ietf.org/html/rfc7231).
See the [official documentation](https://docs.example.com).
```

### Reference-style Links

For documents with many repeated links:

```markdown
The [implementation][impl] follows the [specification][spec].
See also the [API docs][api] and [examples][examples].

[impl]: ./src/index.ts
[spec]: https://example.com/spec
[api]: https://api.example.com/docs
[examples]: ./examples/
```

## Combined Patterns

### Review Section (Good/Bad/Ugly)

```markdown
### ✅ Good

- **Clean separation of concerns** — `src/handlers/auth.ts:45-89`
  - Authentication logic isolated from business logic
  - Easy to test in isolation

- **Proper error handling** — `src/utils/errors.ts`
  - Custom error classes with appropriate HTTP status codes
  - Consistent error response format

### ❌ Bad

- **Missing input validation** — `src/handlers/users.ts:23`
  - User input not sanitized before database query
  - Potential SQL injection vulnerability

- **Hardcoded configuration** — `src/config.ts:12`
  - API endpoint hardcoded instead of using environment variable

### ⚠️ Ugly

- **Growing complexity** — `src/services/payment.ts`
  - File has grown to 500+ lines
  - Multiple responsibilities mixed together
  - Candidate for refactoring

### ❓ Questions

- Is the rate limiting configured correctly for production load?
- Should we add retry logic for external API calls?
- What's the expected behavior when the cache is cold?
```

### Risk Assessment

```markdown
## 🔍 Risk Assessment

### 🔴 High Severity

**Edge case: Concurrent modifications**
- Risk: Two users editing same resource simultaneously
- Impact: Data corruption, lost updates
- Mitigation: Add optimistic locking with version field

### 🟡 Medium Severity

**Assumption: Database availability**
- Risk: Plan assumes 99.9% database uptime
- Impact: Service degradation during outages
- Mitigation: Add circuit breaker and fallback behavior

### 🔵 Low Severity

**Ordering dependency**
- Risk: Migration must run before deployment
- Impact: Temporary errors during rollout
- Mitigation: Document deployment sequence
```

### File Tree Pattern

```markdown
<details>
<summary>📁 Project Structure</summary>

```
src/
├── components/
│   ├── Button.tsx      (📝 modified)
│   ├── Input.tsx       (✨ new)
│   └── Form.tsx
├── hooks/
│   ├── useForm.ts      (📝 modified)
│   └── useAuth.ts
├── utils/
│   ├── validation.ts   (✨ new)
│   └── helpers.ts
└── index.ts
```

</details>
```

### State Dashboard

```markdown
## 📊 Current State

| Area | Status | Notes |
|------|--------|-------|
| Authentication | ✅ Working | Shipped in v1.2 |
| User Management | 🔄 In Progress | PR #123 open |
| Notifications | ❌ Broken | Issue #456 |
| Analytics | 🚫 Blocked | Waiting on API access |
```

### Cognitive Debt Hotspots

```markdown
## ⚠️ Cognitive Debt Hotspots

### 🔴 High Priority

**`buildCoordinationInstructions` function** — `src/coordinator.ts:145`
- Changed recently but has no documented rationale
- Called from 3 different places with different parameters
- **Suggestion:** Add JSDoc explaining the 4 coordination levels and when each is used

### 🟡 Medium Priority

**Event handling flow** — `src/events/`
- Multiple files with similar names (`handler.ts`, `handlers.ts`, `eventHandler.ts`)
- Unclear which is the entry point
- **Suggestion:** Consolidate or add README explaining the architecture

### 🔵 Low Priority

**Test coverage gap** — `src/utils/crypto.ts`
- Complex module with no unit tests
- Only tested indirectly through integration tests
- **Suggestion:** Add unit tests before next modification
```
