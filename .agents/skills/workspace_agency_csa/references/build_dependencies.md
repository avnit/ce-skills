# BUILD Dependencies Reference

To build a custom CE Jetski agent that natively compiles stubs for `ContextServiceAgent`, include the following dependency targets in your Blaze `py_library` BUILD rules:

```starlark
py_library(
    name = "ce_campaign_agent",
    srcs = ["ce_campaign_agent.py"],
    deps = [
        "//apps/intelligence/context/context_engine/lib/api:context_service_py_pb2",
        "//apps/intelligence/context/context_engine/lib/api:corpus_py_pb2",
        "//apps/intelligence/gen_ai/agency/common/python:py_base_workspace_agent",
        "//assistant/bard/agents/framework/agents/experimental/context_service:context_service_agent",
        "//assistant/bard/agents/framework/proto:agent_py_pb2",
        "//assistant/bard/agents/framework/proto/workspace:context_service_agent_config_py_pb2",
    ],
)
```
