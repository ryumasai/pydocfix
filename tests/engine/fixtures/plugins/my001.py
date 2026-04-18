from pydocfix.rules._base import BaseRule


class MY001(BaseRule):
    code = "MY001"
    enabled_by_default = True

    def diagnose(self, node, ctx):
        return iter([])
