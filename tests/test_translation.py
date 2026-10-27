import hashlib
import io
import json
import tempfile
import urllib.error
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.translate import apply_glossary, input_signature, restore_glossary, sign, translate_file, validate_placeholders
from scripts.translate import youdao
from scripts.check_upstream import needs_update


class TranslationTests(unittest.TestCase):
    def test_dynamic_navigation_and_configuration_labels_are_catalogued(self):
        root = Path(__file__).resolve().parents[1]
        translations = json.loads((root / "translations/zh-CN.json").read_text(encoding="utf-8"))
        memory = json.loads((root / "translations/memory.json").read_text(encoding="utf-8"))
        expected = {
            ("ui/src/components/ConfigurationDrawerContent.vue", "configuration:boolean:true", "true"): "是",
            ("ui/src/components/ConfigurationDrawerContent.vue", "configuration:boolean:false", "false"): "否",
            ("ui/src/components/NavigationDrawer.vue", "script:userRole.display:admin", "admin"): "管理员",
            ("ui/src/components/NavigationDrawer.vue", "script:userRole.display:rw", "rw"): "读写",
            ("ui/src/components/NavigationDrawer.vue", "script:userRole.display:ro", "ro"): "只读",
            ("ui/src/components/NavigationDrawer.vue", "script:logout.error:Error when trying to logout (", "Error when trying to logout ("): "退出登录时出错（",
            ("ui/src/components/NavigationDrawer.vue", "script:logout.error:)", ")"): "）",
            ("ui/src/components/NavigationDrawer.vue", "script:demo.switch:Switched to demo user: ", "Switched to demo user: "): "已切换到演示用户：",
            ("ui/src/components/NavigationDrawer.vue", "script:demo.switch: (", " ("): "（",
            ("ui/src/components/NavigationDrawer.vue", "script:demo.switch:)", ")"): "）",
            ("ui/src/components/ConfigurationDrawerContent.vue", "script:configuration.copy.success: copied to clipboard", " copied to clipboard"): " 已复制到剪贴板",
            ("ui/src/components/ConfigurationDrawerContent.vue", "script:configuration.copy.failure:Unable to copy ", "Unable to copy "): "无法复制 ",
            ("ui/src/components/ConfigurationDrawerContent.vue", "script:configuration.copy.failure: to clipboard", " to clipboard"): " 到剪贴板",
        }
        for (source_file, context, source), translation in expected.items():
            key = hashlib.sha256(f"{source_file}\0{context}\0{source}".encode()).hexdigest()
            self.assertEqual(translations[key], translation)
            self.assertEqual(memory[key]["source"], source)
            self.assertEqual(memory[key]["translation"], translation)

    def test_role_display_mapping_falls_back_to_original_role(self):
        root = Path(__file__).resolve().parents[1]
        script = (root / "scripts/i18n.mjs").read_text(encoding="utf-8")
        self.assertIn("labels[role] ?? role", script)
        self.assertIn("props.user.role, ${roleMap}", script)

    def test_youdao_v3_signature_input_rules(self):
        self.assertEqual(input_signature("short text"), "short text")
        self.assertEqual(input_signature("0123456789abcdefghijXYZ"), "012345678923defghijXYZ")
        expected = hashlib.sha256(b"appqsalt1secret").hexdigest()
        self.assertEqual(sign("app", "secret", "q", "salt", "1"), expected)

    def test_placeholder_validation(self):
        self.assertTrue(validate_placeholders("Hello {name} %s", "你好 {name} %s"))
        self.assertFalse(validate_placeholders("Hello {name}", "你好"))

    def test_release_version_comparison_never_rebuilds_same_version(self):
        self.assertFalse(needs_update("9.6.0", "9.6.0"))
        self.assertFalse(needs_update("9.6.0", "9.5.0"))
        self.assertTrue(needs_update("9.5.0", "9.6.0"))

    def test_api_retries_transient_timeout_and_never_sends_secret_as_a_field(self):
        calls = []

        class Response(io.BytesIO):
            pass

        def opener(request, timeout):
            calls.append(request)
            if len(calls) < 3:
                raise urllib.error.URLError("timeout")
            return Response('{"errorCode":"0","translation":["容器"]}'.encode("utf-8"))

        result = youdao("Container", "app-id", "top-secret", opener=opener, sleep=lambda _: None)
        self.assertEqual(result, "容器")
        self.assertEqual(len(calls), 3)
        self.assertNotIn(b"top-secret", calls[-1].data)

    def test_api_balance_error_fails_without_exposing_credentials(self):
        def opener(*_args, **_kwargs):
            return io.BytesIO('{"errorCode":"401","translation":[]}'.encode("utf-8"))

        with self.assertRaisesRegex(RuntimeError, "401") as error:
            youdao("Container", "app-id", "top-secret", opener=opener, sleep=lambda _: None)
        self.assertNotIn("top-secret", str(error.exception))

    def test_cached_offline_and_failed_translation_does_not_pollute_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "manifest.json"
            memory = root / "memory.json"
            output = root / "zh.json"
            manifest.write_text(json.dumps([
                {"id": "cached", "text": "Container", "context": "span:text"},
                {"id": "new", "text": "New item", "context": "button:text"},
            ]), encoding="utf-8")
            memory.write_text(json.dumps({"cached": {"source": "Container", "translation": "容器"}}), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                translate_file(manifest, memory, output, "9.6.0", "app", "secret",
                               translate=lambda *_: (_ for _ in ()).throw(RuntimeError("API failed")))
            self.assertEqual(json.loads(memory.read_text(encoding="utf-8")), {"cached": {"source": "Container", "translation": "容器"}})
            self.assertFalse(output.exists())

    def test_glossary_allows_offline_translation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest, memory, output, glossary = (root / name for name in ("manifest.json", "memory.json", "zh.json", "glossary.json"))
            manifest.write_text(json.dumps([{"id": "term", "text": "Container", "context": "span:text"}]), encoding="utf-8")
            glossary.write_text(json.dumps({"Container": "容器"}), encoding="utf-8")
            result = translate_file(manifest, memory, output, "9.6.0", glossary_path=glossary)
            self.assertEqual(result["translated"], 1)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), {"term": "容器"})
            self.assertEqual(json.loads(memory.read_text(encoding="utf-8"))["term"]["origin"], "glossary")

    def test_glossary_terms_are_protected_inside_sentences(self):
        query, protected = apply_glossary("Container Image", {"Container": "容器", "Image": "镜像"})
        self.assertEqual(query, "WUDTERM0TOKEN WUDTERM1TOKEN")
        self.assertEqual(restore_glossary("WUDTERM0TOKEN WUDTERM1TOKEN", protected), "容器 镜像")


if __name__ == "__main__":
    unittest.main()
