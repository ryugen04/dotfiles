# Plan File Contract

Plan files preserve intent outside chat history.

## Required Fields

- original request
- workflow axes
- target root
- allowed paths
- forbidden paths
- phases and checkpoints
- subagents or owner roles
- outputs
- test plan
- approval gates
- rollback or recovery path
- current status

## Large Plans

When a plan has multiple workflow types or subsystems, create a parent plan with explicit child plan paths. Each child plan must reference the parent.

