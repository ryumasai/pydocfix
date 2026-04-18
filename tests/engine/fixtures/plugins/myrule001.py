from pydocfix.rules._base import BaseRule


class MYRULE001(BaseRule):
    code = "MYRULE001"
    enabled_by_default = True

    def diagnose(self, node, ctx):
        return iter([])
