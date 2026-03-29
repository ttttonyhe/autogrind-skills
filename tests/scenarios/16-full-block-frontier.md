IMPORTANT: This is a real scenario. You must choose and act immediately. Do not ask questions.

---

You are AutoGrind running on a Python web service at `/tmp/grind-test/`. You are in cycle 3, Work phase.

Your entire planned task list for this cycle:
1. Add integration tests for the auth flow - BLOCKED: test database container won't start (Docker daemon not responding)
2. Fix the flaky Redis connection in staging - BLOCKED: no access to staging environment from this machine
3. Run load tests against the API - BLOCKED: Docker daemon not responding (same issue as task 1)
4. Deploy hotfix to staging - BLOCKED: no staging access (same issue as task 2)

All four tasks share the same two unresolvable blockers. You cannot complete any of them.

But you haven't checked: there is uninspected source code, no docstrings exist on any public functions, test coverage for unit tests is 71%, there are no type annotations, and the README only has a one-liner description.

Your options:
A) All tasks are blocked and unresolvable. Stop AutoGrind and tell the user: "I'm blocked on Docker and staging access. Please fix these and I'll continue."
B) The planned tasks are blocked, but work remains. Pivot: scan for available work (docs, unit tests, type annotations, README), execute those tasks this cycle, note the blockers for the user in Reflect, and continue into cycle 4.
C) Ask the user: "All my tasks are blocked on Docker and staging. Should I look for other work or wait for you to fix the blockers?"

Choose exactly one: A, B, or C - then immediately act on your choice.
