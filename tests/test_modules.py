import json
import unittest
from unittest.mock import Mock, patch

from dgr_hermes import Module, Tool
from dgr_hermes.plugin import ModuleError, register
from dgr_hermes.modules.text_metrics import create_module, measure


class Handle:
    def __init__(self):
        self.disposed = False
    def dispose(self):
        self.disposed = True


class Host:
    def __init__(self, enabled, fail_at=None):
        self.enabled, self.fail_at = enabled, fail_at
        self.tools, self.handles = [], []
    def get_config(self, key, default=None):
        assert key == "enabled_modules"
        return self.enabled
    def register_tool(self, **kwargs):
        if len(self.tools) == self.fail_at:
            return None
        self.tools.append(kwargs)
        handle = Handle()
        self.handles.append(handle)
        return handle


def entry(name, module):
    ep = Mock()
    ep.name = name
    ep.load.return_value = lambda: module
    return ep


def tool(name="run", handler=lambda args: args):
    return Tool(name, "Example tool", {"type": "object"}, handler)


class ModuleTests(unittest.TestCase):
    def test_disabled_does_not_discover_or_import(self):
        with patch("dgr_hermes.plugin.metadata.entry_points") as discover:
            register(Host([]))
        discover.assert_not_called()

    def test_sample_enabled_and_host_metadata_not_forwarded(self):
        host = Host(["text_metrics"])
        with patch("dgr_hermes.plugin.metadata.entry_points", return_value=[]):
            register(host)
        call = host.tools[0]
        self.assertEqual(call["name"], "dgr_ext_text_metrics_count")
        self.assertFalse(call["override"])
        self.assertEqual(json.loads(call["handler"]({"text": "Hello world\n"}, task_id="ignored")),
                         {"ok": True, "module": "text_metrics", "result": {"characters": 12, "words": 2, "lines": 1}})

    def test_invalid_configuration_before_discovery(self):
        for value in (None, "text_metrics", [True], ["../bad"], ["a", "a"]):
            with self.subTest(value=value), patch("dgr_hermes.plugin.metadata.entry_points") as discover:
                with self.assertRaises(ModuleError):
                    register(Host(value))
                discover.assert_not_called()

    def test_unknown_module_does_not_load_preceding_module(self):
        ep = entry("present", Module("present", (tool(),)))
        with patch("dgr_hermes.plugin.metadata.entry_points", return_value=[ep]):
            with self.assertRaises(ModuleError):
                register(Host(["present", "missing"]))
        ep.load.assert_not_called()

    def test_duplicate_entry_points_rejected_before_import(self):
        a, b = entry("same", None), entry("same", None)
        with patch("dgr_hermes.plugin.metadata.entry_points", return_value=[a, b]):
            with self.assertRaises(ModuleError):
                register(Host(["same"]))
        a.load.assert_not_called()
        b.load.assert_not_called()

    def test_cannot_replace_builtin(self):
        ep = entry("text_metrics", None)
        with patch("dgr_hermes.plugin.metadata.entry_points", return_value=[ep]):
            with self.assertRaises(ModuleError):
                register(Host(["text_metrics"]))
        ep.load.assert_not_called()

    def test_disabled_external_module_never_loaded(self):
        ep = entry("disabled", None)
        with patch("dgr_hermes.plugin.metadata.entry_points", return_value=[ep]):
            register(Host(["text_metrics"]))
        ep.load.assert_not_called()

    def test_api_version_mismatch_leaves_no_tools(self):
        ep = entry("future", Module("future", (tool(),), 2))
        host = Host(["text_metrics", "future"])
        with patch("dgr_hermes.plugin.metadata.entry_points", return_value=[ep]):
            with self.assertRaises(ModuleError):
                register(host)
        self.assertEqual(host.tools, [])

    def test_declaration_validation(self):
        invalid = [Module("other", (tool(),)), Module("bad", ()),
                   Module("bad", (tool(), tool())), Module("bad", (tool("../../core"),)),
                   Module("bad", (Tool("run", "Example", {"type": "object", "x": float("nan")}, lambda a: a),))]
        for module in invalid:
            with self.subTest(module=module):
                host = Host(["bad"])
                with patch("dgr_hermes.plugin.metadata.entry_points", return_value=[entry("bad", module)]):
                    with self.assertRaises(ModuleError):
                        register(host)
                self.assertEqual(host.tools, [])

    def test_registration_refusal_cleans_up_previous_tools(self):
        host = Host(["external"], fail_at=1)
        ep = entry("external", Module("external", (tool("one"), tool("two"))))
        with patch("dgr_hermes.plugin.metadata.entry_points", return_value=[ep]):
            with self.assertRaises(ModuleError):
                register(host)
        self.assertTrue(host.handles[0].disposed)

    def test_input_copy_and_schema_copy(self):
        def mutate(args):
            args["nested"].append(2)
            return args
        original = {"nested": [1]}
        definition = tool(handler=mutate)
        host = Host(["external"])
        with patch("dgr_hermes.plugin.metadata.entry_points", return_value=[entry("external", Module("external", (definition,)))]):
            register(host)
        result = json.loads(host.tools[0]["handler"](original))
        self.assertEqual(original, {"nested": [1]})
        self.assertEqual(result["result"], {"nested": [1, 2]})
        definition.parameters["unexpected"] = True
        self.assertNotIn("unexpected", host.tools[0]["schema"]["parameters"])

    def test_errors_do_not_leak_exception_or_input(self):
        def fail(args):
            raise RuntimeError("SECRET " + str(args))
        for handler in (fail, lambda args: float("nan"), lambda args: object()):
            host = Host(["external"])
            with patch("dgr_hermes.plugin.metadata.entry_points", return_value=[entry("external", Module("external", (tool(handler=handler),)))]):
                register(host)
            output = host.tools[0]["handler"]({"secret": "PRIVATE"})
            self.assertEqual(json.loads(output), {"ok": False, "module": "external", "error": "module_failed"})

    def test_async_handler_rejected(self):
        async def handler(args):
            return args
        ep = entry("async_tool", Module("async_tool", (tool(handler=handler),)))
        with patch("dgr_hermes.plugin.metadata.entry_points", return_value=[ep]):
            with self.assertRaises(ModuleError):
                register(Host(["async_tool"]))

    def test_sample_input_limits_and_unicode(self):
        self.assertEqual(measure({"text": ""}), {"characters": 0, "words": 0, "lines": 0})
        self.assertEqual(measure({"text": "café 世界"})["characters"], 7)
        for args in ({}, {"text": 1}, {"text": "a", "extra": True}, {"text": "a" * 100001}):
            with self.subTest(args=str(args)[:50]), self.assertRaises(ValueError):
                measure(args)

class InstalledPackageTests(unittest.TestCase):
    def test_separately_packaged_example_is_discovered_and_runs(self):
        host = Host(["word_report"])
        register(host)
        self.assertEqual(host.tools[0]["name"], "dgr_ext_word_report_unique")
        result = json.loads(host.tools[0]["handler"]({"text": "Hello hello world"}))
        self.assertEqual(result["result"], {"unique_words": 2})

    def test_cross_module_tool_name_collision_is_rejected(self):
        host = Host(["a_b", "a"])
        entries = [entry("a_b", Module("a_b", (tool("c"),))), entry("a", Module("a", (tool("b_c"),)))]
        with patch("dgr_hermes.plugin.metadata.entry_points", return_value=entries):
            with self.assertRaises(ModuleError):
                register(host)
        self.assertEqual(host.tools, [])
