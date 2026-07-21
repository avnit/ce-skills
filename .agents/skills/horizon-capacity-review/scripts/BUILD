load("//devtools/python/blaze:pytype.bzl", "pytype_strict_binary")

package(default_visibility = ["//visibility:public"])

pytype_strict_binary(
    name = "demand_validator",
    srcs = ["demand_validator.py"],
    deps = [
        "//third_party/py/absl:app",
        "//third_party/py/absl/flags",
    ],
)
