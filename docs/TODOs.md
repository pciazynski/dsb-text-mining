# TODOs

That's a TODO list for humans not agents. It might be stale or incomplete.

## Search behavior and consistency

- Standardize exact semantics (`exact=1` exact, `exact=0` ambiguous).
- Roll standardized exact handling to sibling non-regex endpoints.
- Decide whether ambiguous-regex matching should also apply to bwword regex endpoints.
- Document final regex/exact/ambiguous behavior in one canonical place.

## Security and robustness

- Bind and validate remaining year filters (`urn*`, `*tokenperyear`, `*countdaterange`).
- Audit `REGEXP` callback usage for ReDoS and full-scan risk.

## Quality and maintenance

- Add smoke tests for key PHP endpoints.
- Track and fix the drjowk vs drjewk case.
