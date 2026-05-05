# State File Schema

## .state/progress.json

| Field         | Type   | Values                                     |
|---------------|--------|--------------------------------------------|
| codelab       | string | Name of the codelab                        |
| total_steps   | int    | Number of parsed steps                     |
| current_step  | int    | Step being worked on (1-indexed)           |
| status        | string | running, blocked, completed, failed        |
| last_updated  | string | ISO 8601 timestamp                         |

## .state/step-NN.json

| Field                      | Type     | Description                           |
|----------------------------|----------|---------------------------------------|
| step                       | int      | Step number                           |
| title                      | string   | Short title                           |
| status                     | string   | pending, blocked, done, failed        |
| blocked_reason             | string?  | Reason for blocked status (e.g. "waiting for user") |
| execution_summary          | string?  | High-level summary of execution/issues (e.g. "User input needed") |
| instructions               | string   | Single interpreted instruction        |
| prerequisites              | string[] | List of conditions that must be met   |
| check_attempts             | int      | Times prerequisite was checked        |
| last_check                 | string?  | ISO 8601 of last check                |
| started_at                 | string?  | When step execution began             |
| completed_at               | string?  | When step finished                    |
| output                     | string?  | Last command output                   |
| error                      | string?  | Error details if failed               |

## .state/user_inputs.json

A JSON object where keys are the variable names identified in the codelab and
values are the user-provided inputs.

| Field         | Type   | Description                                |
|---------------|--------|--------------------------------------------|
| (variable_name)| string | The value provided by the user for this variable |
