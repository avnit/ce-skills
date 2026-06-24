# Test Plan: Publish Artifact Skill

This test plan verifies that the `publish-artifact` skill deterministically clones, structures, and pushes an artifact without affecting the production `ce-skills-artifacts` repository.

## Verification Strategy

We use a mock local bare Git repository as the remote destination. By overriding the `CE_ARTIFACTS_REPO_URL` environment variable, we force the `publish.sh` script to push to our local mock repository instead of GitHub. We then clone the mock repository to verify the internal file structure matches the expected format: `<username>/<category>/<subject>/<filename>`.

## Automated Test Script

You can run the automated deterministic test by executing the following script:

```bash
bash .agents/skills/publish-artifact/scripts/test_publish.sh
```

### Expected Output

The script will output:

1. The creation of the mock remote.
2. The execution logs of `publish.sh`.
3. An `ls` output showing the successfully pushed file in the correct directory.
4. A "✅ Test Passed" message if the structure is correct.
