from pydocfix.rules._base import BaseRule


class PATHRULE(BaseRule):
    code = "CROSS001"
    enabled_by_default = True

    def diagnose(self, node, ctx):
        return iter([])
