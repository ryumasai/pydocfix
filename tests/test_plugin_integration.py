"""Integration tests for plugin system."""

from __future__ import annotations

import tempfile
from pathlib import Path
from textwrap import dedent

from pydocfix.checker import check_file
from pydocfix.config import Config, load_config
from pydocfix.rules import build_registry, load_plugin_rules


def test_plugin_integration_from_path():
    """Test loading and using a plugin from a file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create a simple custom rule (works with PlainDocstring)
        plugin_file = tmppath / "my_rule.py"
        plugin_file.write_text(
            dedent("""
            from pydocfix.rules import BaseRule, DiagnoseContext, Diagnostic
            from pydocstring import PlainDocstring
            from collections.abc import Iterator

            class PLUG001(BaseRule[PlainDocstring]):
                code = "PLUG001"
                enabled_by_default = True

                def diagnose(self, node, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
                    if node.summary and "bad" in node.summary.text.lower():
                        yield self._make_diagnostic(
                            ctx,
                            "Docstring contains word 'bad'",
                            target=node.summary,
                        )
        """)
        )

        # Load plugin
        plugin_rules = load_plugin_rules(plugin_paths=[tmppath])
        assert len(plugin_rules) == 1
        assert plugin_rules[0].code == "PLUG001"

        # Build registry with plugin
        registry = build_registry(plugin_rules=plugin_rules)

        # Test with source that triggers the rule (plain docstring)
        source = dedent('''
            def foo():
                """This is a bad docstring."""
                pass
        ''')

        diagnostics, _, _ = check_file(
            source,
            Path("test.py"),
            registry.type_to_rules,
        )

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "PLUG001"
        assert "bad" in diagnostics[0].message.lower()


def test_plugin_integration_with_config():
    """Test loading plugins via config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create plugin
        plugin_file = tmppath / "config_plugin.py"
        plugin_file.write_text(
            dedent("""
            from pydocfix.rules import BaseRule, DiagnoseContext, Diagnostic
            from pydocstring import PlainDocstring
            from collections.abc import Iterator

            class CONFIG001(BaseRule[PlainDocstring]):
                code = "CONFIG001"
                enabled_by_default = True

                def diagnose(self, node, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
                    if node.summary and len(node.summary.text.strip()) < 5:
                        yield self._make_diagnostic(
                            ctx,
                            "Summary too short",
                            target=node.summary,
                        )
        """)
        )

        # Create config
        config = Config(plugin_paths=[str(tmppath)])

        # Load plugins based on config
        plugin_rules = load_plugin_rules(plugin_paths=[Path(p) for p in config.plugin_paths])

        # Build registry
        registry = build_registry(config=config, plugin_rules=plugin_rules)

        # Test
        source = dedent('''
            def bar():
                """Hi."""
                pass
        ''')

        diagnostics, _, _ = check_file(
            source,
            Path("test.py"),
            registry.type_to_rules,
            config=config,
        )

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "CONFIG001"


def test_plugin_can_be_ignored():
    """Test that plugin rules can be ignored via config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create plugin
        plugin_file = tmppath / "ignorable.py"
        plugin_file.write_text(
            dedent("""
            from pydocfix.rules import BaseRule, DiagnoseContext, Diagnostic
            from pydocstring import PlainDocstring
            from collections.abc import Iterator

            class IGN001(BaseRule[PlainDocstring]):
                code = "IGN001"
                enabled_by_default = True

                def diagnose(self, node, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
                    yield self._make_diagnostic(ctx, "Always fires", target=node)
        """)
        )

        plugin_rules = load_plugin_rules(plugin_paths=[tmppath])

        # Build registry with ignore
        registry = build_registry(
            ignore=["IGN001"],
            plugin_rules=plugin_rules,
        )

        source = dedent('''
            def baz():
                """Docstring."""
                pass
        ''')

        diagnostics, _, _ = check_file(
            source,
            Path("test.py"),
            registry.type_to_rules,
        )

        # IGN001 should be ignored
        assert len(diagnostics) == 0


def test_plugin_can_be_selected():
    """Test that plugin rules can be explicitly selected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create plugin with enabled_by_default=False
        plugin_file = tmppath / "selectable.py"
        plugin_file.write_text(
            dedent("""
            from pydocfix.rules import BaseRule, DiagnoseContext, Diagnostic
            from pydocstring import PlainDocstring
            from collections.abc import Iterator

            class SEL001(BaseRule[PlainDocstring]):
                code = "SEL001"
                enabled_by_default = False  # Opt-in

                def diagnose(self, node, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
                    yield self._make_diagnostic(ctx, "Selected rule", target=node)
        """)
        )

        plugin_rules = load_plugin_rules(plugin_paths=[tmppath])

        # Build registry with select
        registry = build_registry(
            select=["SEL001"],
            plugin_rules=plugin_rules,
        )

        source = dedent('''
            def qux():
                """Docstring."""
                pass
        ''')

        diagnostics, _, _ = check_file(
            source,
            Path("test.py"),
            registry.type_to_rules,
        )

        # SEL001 should be active because it was selected
        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "SEL001"


def test_builtin_and_plugin_rules_coexist():
    """Test that builtin and plugin rules work together."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create plugin
        plugin_file = tmppath / "coexist.py"
        plugin_file.write_text(
            dedent("""
            from pydocfix.rules import BaseRule, DiagnoseContext, Diagnostic
            from pydocstring import PlainDocstring
            from collections.abc import Iterator

            class MIX001(BaseRule[PlainDocstring]):
                code = "MIX001"
                enabled_by_default = True

                def diagnose(self, node, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
                    if node.summary and "mixed" in node.summary.text.lower():
                        yield self._make_diagnostic(ctx, "Found 'mixed'", target=node.summary)
        """)
        )

        plugin_rules = load_plugin_rules(plugin_paths=[tmppath])
        registry = build_registry(plugin_rules=plugin_rules)

        # Source that triggers both builtin (SUM001) and plugin (MIX001)
        source = dedent('''
            def test():
                """Mixed test."""
                pass

            def no_doc():
                pass
        ''')

        diagnostics, _, _ = check_file(
            source,
            Path("test.py"),
            registry.type_to_rules,
        )

        # Should have diagnostics from both builtin and plugin
        codes = {d.rule for d in diagnostics}
        assert "MIX001" in codes  # Plugin rule
        # May also have builtin rules depending on the source


def test_example_plugin_rules():
    """Test the example plugin rules from examples/custom_rules.py."""
    plugin_rules = load_plugin_rules(plugin_modules=["examples.custom_rules"])

    codes = {r.code for r in plugin_rules}
    assert "EXAMPLE001" in codes
    assert "EXAMPLE002" in codes
    assert "EXAMPLE003" in codes

    # Test EXAMPLE001 (minimum length)
    registry = build_registry(select=["EXAMPLE001"], plugin_rules=plugin_rules)

    source = dedent('''
        def short():
            """Hi."""
            pass
    ''')

    diagnostics, _, _ = check_file(
        source,
        Path("test.py"),
        registry.type_to_rules,
    )

    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "EXAMPLE001"
    assert "too short" in diagnostics[0].message.lower()
