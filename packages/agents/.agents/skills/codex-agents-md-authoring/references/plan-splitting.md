# Plan Splitting Contract

Use split plans when a plan contains more than one major workflow type, subsystem, or phase transition contract.

## Parent Plan Must Include

- original request
- workflow axes
- child plan path list
- shared assumptions
- shared acceptance criteria
- implementation order
- approval boundaries

## Child Plan Must Include

- parent plan path
- subsystem or workflow type
- required inputs
- required outputs
- phase/step contract
- tests
- rollback or recovery path

## File Names

Use `.codex/plans/YYYYMMDDHH-{planname}.md`. `.codex/plans/**` can remain git ignored when the durable behavior is captured in skills, schemas, hooks, validators, and tests.

