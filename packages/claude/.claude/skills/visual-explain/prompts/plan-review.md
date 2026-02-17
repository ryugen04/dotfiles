---
description: Generate a visual Markdown plan review — current codebase state vs. proposed implementation plan
skill: visual-explain
---
Generate a comprehensive visual plan review as a Markdown document, comparing the current codebase against a proposed implementation plan. **Output must be written in Japanese.**

Follow the visual-explain skill workflow. Read the reference template, Markdown patterns, and Mermaid syntax references before generating.

**Inputs:**
- Plan file: `$1` (path to a markdown plan, spec, or RFC document)
- Codebase: `$2` if provided, otherwise the current working directory

**Data gathering phase** — read and cross-reference these before generating:

1. **Read the plan file in full.** Extract:
   - The problem statement and motivation
   - Each proposed change (files to modify, new files, deletions)
   - Rejected alternatives and their reasoning
   - Any explicit scope boundaries or non-goals

2. **Read every file the plan references.** For each file mentioned in the plan, read the current version in full. Also read files that import or depend on those files — the plan may not mention all ripple effects.

3. **Map the blast radius.** From the codebase, identify:
   - What imports/requires the files being changed (grep for import paths)
   - What tests exist for the affected files (look for corresponding `.test.*` / `.spec.*` files)
   - Config files, types, or schemas that might need updates
   - Public API surface that callers depend on

4. **Cross-reference plan vs. code.** For each change the plan proposes, verify:
   - Does the file/function/type the plan references actually exist in the current code?
   - Does the plan's description of current behavior match what the code actually does?
   - Are there implicit assumptions about code structure that don't hold?

**Verification checkpoint** — before generating Markdown, produce a structured fact sheet of every claim you will present in the review:
- Every quantitative figure: file counts, estimated lines, function counts, test counts
- Every function, type, and module name you will reference from both the plan and the codebase
- Every behavior description: what the code currently does vs. what the plan proposes
- For each, cite the source: the plan section or the file:line where you read it
Verify each claim against the code and the plan. If something cannot be verified, mark it as uncertain rather than stating it as fact. This fact sheet is your source of truth during Markdown generation — do not deviate from it.

**Document structure** — the Markdown file should include:

1. **計画概要 (Plan summary)** — lead with the *intuition*: what problem does this plan solve, and what's the core insight behind the approach? Then the scope: how many files touched, estimated scale of changes, new modules or tests planned. A reader who only sees this section should understand the plan's essence. *This is the visual anchor — use larger headings, bold key points.*

2. **影響指標 (Impact dashboard)** — files to modify, files to create, files to delete, estimated lines added/removed, new test files planned, dependencies affected. Include a **completeness** indicator: whether the plan covers tests (✅/❌), docs updates (✅/⚠️/❌), and migration/rollback (✅/N/A).

3. **現在のアーキテクチャ (Current architecture)** — Mermaid diagram of how the affected subsystem works *today*. Focus only on the parts the plan touches — don't diagram the entire codebase. Show the data flow, dependencies, and call paths that will change. *Use matching Mermaid layout direction and node names as section 4 so the visual diff is obvious.*

4. **計画後のアーキテクチャ (Planned architecture)** — Mermaid diagram of how the subsystem will work *after* the plan is implemented. Use the same node names and layout direction as the current architecture diagram so the differences are visually obvious. *Highlight new nodes with different styling, note removed nodes.*

5. **変更詳細 (Change-by-change breakdown)** — for each change in the plan, a collapsible `<details>` section:
   - **現状 (Current):** what the code does now, with relevant snippets or function signatures
   - **計画 (Planned):** what the plan proposes, with the plan's own code examples if provided
   - **根拠 (Rationale):** below each panel, extract _why_ the plan chose this approach. Pull from the plan's reasoning, rejected alternatives section, or inline justifications. If the plan includes a "rejected alternatives" section, map those rejections to the specific changes they apply to. Flag changes where the plan says _what_ to do but not _why_ — these are pre-implementation cognitive debt.
   - Flag any discrepancies where the plan's description of current behavior doesn't match the actual code

6. **依存関係分析 (Dependency & ripple analysis)** — *use `<details>` collapsed by default.* What other code depends on the files being changed. Table or Mermaid graph showing callers, importers, and downstream effects the plan may not explicitly address. Color-code: ✅ covered by plan, ⚠️ not mentioned but likely affected, ❌ definitely missed.

7. **リスク評価 (Risk assessment)** — structured sections for:
   - **Edge cases** the plan doesn't address
   - **Assumptions** the plan makes about the codebase that should be verified
   - **Ordering risks** if changes need to be applied in a specific sequence
   - **Rollback complexity** if things go wrong
   - **Cognitive complexity** — areas where the plan introduces non-obvious coupling, action-at-a-distance behavior, implicit ordering requirements, or contracts that exist only in the developer's memory. Distinct from bug risk — these are "you'll forget how this works in a month" risks. Each cognitive complexity flag gets a brief mitigation suggestion (e.g., "add a comment explaining the ordering requirement" or "consider a runtime assertion that validates the invariant"). Note: cognitive complexity flags belong here when they're about specific code patterns; broader concerns about the plan's overall approach (overengineering, lock-in, maintenance burden) belong in section 8's Ugly category.
   - Each risk gets a severity indicator (🔴 High / 🟡 Medium / 🔵 Low)

8. **計画レビュー (Plan review)** — structured Good/Bad/Ugly analysis of the plan itself:
   - **✅ Good**: Solid design decisions, things the plan gets right, well-reasoned tradeoffs
   - **❌ Bad**: Gaps in the plan — missing files, unaddressed edge cases, incorrect assumptions about current code
   - **⚠️ Ugly**: Subtle concerns — complexity being introduced, maintenance burden, things that will work initially but cause problems at scale
   - **❓ Questions**: Ambiguities that need the plan author's clarification before implementation begins
   - Each item should reference specific plan sections and code files. If nothing to flag in a category, say "None found" rather than omitting the section.

9. **理解ギャップ (Understanding gaps)** — a closing dashboard that rolls up decision-rationale gaps from section 5 and cognitive complexity flags from section 7:
   - Count of changes with clear rationale vs. missing rationale (use a simple table or list)
   - List of cognitive complexity flags with severity
   - Explicit recommendations: "Before implementing, document the rationale for changes X and Y — the plan doesn't explain why these approaches were chosen over alternatives"
   - This section makes cognitive debt visible _before_ the work starts, when it's cheapest to address.

**Visual hierarchy**: Sections 1-4 should be prominent (larger headings, more detail visible). Sections 6+ are reference material and should use collapsible `<details>` sections where appropriate.

Use a current-vs-planned visual language throughout: ℹ️ for current state, ✅ for planned additions, ⚠️ for areas of concern, ❌ for gaps or risks.

Write to `~/.agent/diagrams/` with a descriptive filename and tell the user the file path.

Ultrathink.

$@
