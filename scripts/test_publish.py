import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent


def snapshot(**over):
    snap = {"schema_version": 1, "generated_at": "2026-10-02T00:00:00Z", "prior": 3.5, "weight": 5, "min_ratings": 3,
            "models": [{"model": "qwen2.5-coder-7b-instruct", "format": "gguf", "quantization": "Q4_K_M", "runtime": "llamacpp", "backend": "metal",
                        "cohorts": [{"tier": "family", "cohort": "apple:m4-max", "ratings": 5, "average": 4.2, "weighted_score": 3.85, "confidence": "early"},
                                    {"tier": "global", "ratings": 9, "average": 3.7, "weighted_score": 3.63, "confidence": "early"}]}]}
    snap.update(over)
    return snap


class Publish(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp())
        shutil.copytree(HERE.parent / "schema", self.root / "schema")
        shutil.copytree(HERE, self.root / "scripts")

    def tearDown(self):
        shutil.rmtree(self.root)

    def run_publish(self, snap):
        p = self.root / "in.json"
        p.write_text(json.dumps(snap))
        return subprocess.run([sys.executable, str(self.root / "scripts" / "publish.py"), str(p)], capture_output=True, text=True)

    def test_lays_out_files(self):
        r = self.run_publish(snapshot())
        self.assertEqual(r.returncode, 0, r.stderr)
        f = self.root / "models" / "qwen2.5-coder-7b-instruct" / "q4_k_m-llamacpp-metal-gguf.json"
        self.assertTrue(f.exists())
        self.assertEqual(json.loads(f.read_text())["cohorts"][0]["cohort"], "apple:m4-max")
        self.assertTrue((self.root / "snapshots" / "2026-10-02.json").exists())
        self.assertTrue((self.root / "ratings" / "summary.json").exists())

    def test_refuses_small_or_exact_cohorts(self):
        s = snapshot()
        s["models"][0]["cohorts"][0]["ratings"] = 2
        self.assertNotEqual(self.run_publish(s).returncode, 0)
        s = snapshot()
        s["models"][0]["cohorts"][0]["tier"] = "exact"
        self.assertNotEqual(self.run_publish(s).returncode, 0)

    def test_refuses_off_schema(self):
        s = snapshot()
        s["models"][0]["cohorts"][0]["client_id"] = "abc"
        self.assertNotEqual(self.run_publish(s).returncode, 0)
        self.assertNotEqual(self.run_publish(snapshot(schema_version=2)).returncode, 0)

    def test_removes_configurations_no_longer_published(self):
        self.assertEqual(self.run_publish(snapshot()).returncode, 0)
        self.assertEqual(self.run_publish(snapshot(models=[])).returncode, 0)
        self.assertFalse((self.root / "models" / "qwen2.5-coder-7b-instruct").exists())


if __name__ == "__main__":
    unittest.main()
