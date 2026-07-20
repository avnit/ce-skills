load("//learning/gemini/agents/skill_rules:skills.bzl", "agent_skill")
load("//learning/gemini/agents/skills/skill_creator/scripts:skill_defs.bzl", "validate_skill_test")

package(default_visibility = ["//visibility:public"])

agent_skill(
    name = "skill-review",
    srcs = ["SKILL.md"],
    scripts = [
        "//experimental/users/shacharb/skills/skill_review/scripts:check_skill_links",
    ],
    deps = [],
)

validate_skill_test(
    name = "validate_skill_review_test",
)

validate_skill_test(
    name = "validate_skill_review_skill_test",
)
