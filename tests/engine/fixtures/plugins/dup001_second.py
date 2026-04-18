from pydocfix.rules._base import BaseRule


class DUPSECOND(BaseRule):
    code = "DUP001"
    enabled_by_default = True

    def diagnose(self, node, ctx):
        return iter([])
