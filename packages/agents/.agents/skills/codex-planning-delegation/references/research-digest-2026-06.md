# Research Digest: Agent Planning And Delegation, 2026-06

observed_at: 2026-06-16

This digest summarizes a 61-item research pass across official docs, recent
papers, recent articles, and community workflow repositories. The strongest
practical conclusion is that high-quality agentic coding needs explicit planner
roles, critique gates, visible goal ledgers, and default delegation policies.

## Key Findings

- Codex skills are the right durable surface for reusable planning and
  delegation workflows.
- Codex subagents are useful for parallel complex work, but public docs say they
  run when explicitly asked; the controller should explicitly delegate instead
  of asking the user to choose.
- Claude Code documents automatic delegation from subagent descriptions and has
  built-in Explore/Plan/general-purpose patterns that are useful design
  references for Codex workflows.
- Claude `/goal` is a useful model for persistence: a separate evaluator checks
  completion after each turn, but it can only judge surfaced evidence.
- Recent goal-persistence research shows agents can stop early, duplicate work,
  or drift unless progress is externally verified.
- Agent skills reduce repeated prompting but become a security surface,
  especially when they include executable scripts.
- Community frameworks such as BMAD, SuperClaude, context-engineering PRPs, and
  Taskmaster externalize planning, tasks, critique, and validation into durable
  artifacts.
- Exact `grill-me` searches did not find a reliable canonical source. Treat the
  underlying pattern as adversarial critique, confidence checks, reviewer
  agents, and validation gates.

## Source Set

### Official Codex And OpenAI

1. https://developers.openai.com/codex/skills
2. https://developers.openai.com/codex/subagents
3. https://developers.openai.com/codex/hooks
4. https://developers.openai.com/codex/config-reference
5. https://developers.openai.com/codex/rules
6. https://developers.openai.com/codex/agents-md
7. https://developers.openai.com/codex/workflows
8. https://developers.openai.com/codex/memories
9. https://developers.openai.com/codex/best-practices
10. https://developers.openai.com/codex/cookbook/agent-improvement-loop
11. https://developers.openai.com/codex/cookbook/iterative-repair-loops
12. https://developers.openai.com/codex/building-ai-teams

### Official Claude Code

13. https://code.claude.com/docs/en/sub-agents
14. https://code.claude.com/docs/en/hooks
15. https://code.claude.com/docs/en/memory
16. https://code.claude.com/docs/en/goal
17. https://code.claude.com/docs/en/slash-commands
18. https://code.claude.com/docs/en/settings
19. https://code.claude.com/docs/en/agents-and-parallel-work
20. https://code.claude.com/docs/en/dynamic-workflows
21. https://code.claude.com/docs/en/worktrees
22. https://code.claude.com/docs/en/schedules
23. https://code.claude.com/docs/en/sdk

### Recent And Relevant Papers

24. https://arxiv.org/abs/2605.23574
25. https://arxiv.org/abs/2606.10489
26. https://arxiv.org/abs/2604.14228
27. https://arxiv.org/abs/2604.04978
28. https://arxiv.org/abs/2602.14690
29. https://arxiv.org/abs/2605.07358
30. https://arxiv.org/abs/2603.07670
31. https://arxiv.org/abs/2606.01199
32. https://arxiv.org/abs/2603.19685
33. https://arxiv.org/abs/2606.11447
34. https://arxiv.org/abs/2606.11456
35. https://arxiv.org/abs/2605.25438
36. https://arxiv.org/abs/2606.13763
37. https://arxiv.org/abs/2606.09180
38. https://arxiv.org/abs/2604.13109
39. https://arxiv.org/abs/2601.10338
40. https://arxiv.org/abs/2509.14744

### Articles And Industry Reporting

41. https://www.techradar.com/pro/openais-latest-acquisition-could-see-big-changes-on-the-way-for-its-codex-coding-assistant
42. https://m.economictimes.com/tech/artificial-intelligence/openai-to-acquire-ona-to-strengthen-codex-cloud-capabilities/articleshow/131664834.cms
43. https://www.wired.com/story/how-ai-agents-plunged-tech-world-into-chaos
44. https://www.theverge.com/tech/930447/microsoft-claude-code-discontinued-notepad
45. https://www.windowscentral.com/microsoft/microsoft-cancels-claude-code-licenses-shifting-developers-to-github-copilot-cli-a-move-likely-driven-by-financial-motives
46. https://www.techradar.com/pro/from-code-first-to-intent-first-microsoft-build-2026-could-be-the-end-of-programming-as-we-know-it
47. https://timesofindia.indiatimes.com/technology/tech-news/google-antigravity-2-0-goes-after-claude-code-and-openai-codex-with-a-full-agent-first-rebuild/articleshow/131209670.cms
48. https://www.techradar.com/pro/codex-can-now-operate-your-computer-alongside-you-openai-takes-major-shot-at-claude-code-with-major-workplace-updates
49. https://www.theverge.com/ai-artificial-intelligence/913034/openai-codex-updates-use-macos
50. https://www.itpro.com/software/development/openais-skills-in-codex-service-aims-to-supercharge-agent-efficiency-for-developers
51. https://www.theverge.com/news/873665/github-claude-codex-ai-agents
52. https://www.techradar.com/pro/github-integrates-claude-and-codex-ai-coding-agents-directly-into-github
53. https://www.wired.com/story/openai-codex-race-claude-code
54. https://www.pcgamer.com/software/ai/anthropic-introduces-claude-code-review-so-you-dont-even-need-to-check-all-of-your-own-ai-slop/
55. https://www.itpro.com/technology/artificial-intelligence/four-things-you-need-to-know-about-openais-new-workspace-agents-for-chatgpt-including-how-to-build-your-own

### Community Workflow Repositories

56. https://github.com/SuperClaude-Org/SuperClaude_Framework
57. https://github.com/bmad-code-org/BMAD-METHOD
58. https://github.com/hesreallyhim/awesome-claude-code
59. https://github.com/coleam00/context-engineering-intro
60. https://github.com/eyaltoledano/claude-task-master
61. https://github.com/JayLZhou/Awesome-Agent-Skills

## Practical Backlog

1. Add planner/delegation skill first.
2. Probe current Codex runtime before adding custom subagent definitions.
3. Add planner, researcher, reviewer, and verifier subagent role files only after
   the discovery path and schema are confirmed.
4. Add hooks only for mechanical checks that can be deterministic, such as
   missing plan/order/result detection or quantitative ledger count validation.
5. Keep `.codex/rules` limited to command approval policy.
