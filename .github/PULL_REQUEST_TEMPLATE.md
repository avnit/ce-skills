<!-- Title: conventional-commit style, e.g. `fix: <summary>` -->

Fixes #<!-- issue number -->

### Summary

<!-- One line: what changed and why. -->

### How the test proves the fix

<!-- Name the regression test and how it goes red→green. -->

### Checklist

- [ ] Linked issue referenced above (`Fixes #<n>`)
- [ ] Root cause fixed, not just the symptom
- [ ] Regression test added — fails before, passes after
- [ ] All CI gates green (format, lint, manifest, unit tests)
- [ ] No Claude attribution; authored as `Shachar Bobrovskye <shacharb@google.com>`
- [ ] Diff scoped to this one issue
