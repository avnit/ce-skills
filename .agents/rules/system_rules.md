# System-Wide & General Execution Rules

This file contains general, repository-wide constraints and guidelines for development and orchestration. If a new rule is introduced that does not belong to a dedicated rule file (such as task tracking or environment configuration), it must be appended here.

## 1. Lab Creation Constraints
- **No Cloning from Development Labs (`labs/dev/`)**: When creating a new codelab, agents MUST NOT copy, reference, clone, or use any in-progress or scratchpad codelabs located under the `labs/dev/` directory as a base or template. New codelabs must always be initialized using official templates, standard workflows, or built from scratch to avoid propagating incomplete/scratch code.
