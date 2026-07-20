# State File Schema

## `.tester_state/progress.json`

| Field        | Type   | Values                                                |
| ------------ | ------ | ----------------------------------------------------- |
| codelab      | string | Name of the codelab markdown file                     |
| total_steps  | int    | Total number of parsed steps                          |
| current_step | int    | Step index currently executing (1-indexed)            |
| status       | string | Overall status (`IN PROGRESS`, `COMPLETED`, `FAILED`) |

## `.tester_state/step-NNN.json`

| Field         | Type     | Description                                                               |
| ------------- | -------- | ------------------------------------------------------------------------- |
| num           | int      | Step number (1-indexed)                                                   |
| title         | string   | Short title of the step                                                   |
| status        | string   | `PENDING`, `RUNNING`, `DONE`, `FAILED`, `SKIPPED/NO-OP`, `DEFERRED`       |
| instructions  | string   | Step instruction text                                                     |
| prerequisites | string[] | List of prerequisite condition strings                                    |
| commands      | string[] | List of bash command blocks parsed from the step                          |
| output        | string?  | Captured stdout/stderr output from command execution                      |
| error         | string?  | Detailed error message if status is `FAILED`                              |
| has_gui       | bool     | Indicates if step requires browser or manual UI interaction               |
| is_cleanup    | bool     | Indicates if step is marked as a cleanup step (`<!-- phase: cleanup -->`) |

## `.tester_state/user_inputs.json`

A JSON object where keys are variable names identified in the codelab and values are the mapped baseline values.

| Field             | Type   | Description                                      |
| ----------------- | ------ | ------------------------------------------------ |
| `(variable_name)` | string | Baseline value provided or resolved for variable |
