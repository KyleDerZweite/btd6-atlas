"""Exercise Atlas acceptance scenarios with the shipped checker, without downloads."""

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "profile"
CAPTURE = ROOT / "data/56.3-build-24829026/game-data"
DART = "Towers/DartMonkey/DartMonkey.json"


class ProfileAcceptanceTests(unittest.TestCase):
    def run_checker(self, data=CAPTURE, *, score=False, expected_exit=0):
        command = [str(PROFILE / "validator")]
        if score:
            command += ["score-tower", "--tower", DART]
        command += ["--profile", str(PROFILE), "--game-data", str(data), "--format", "json"]
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)
        self.assertEqual(result.returncode, expected_exit, result.stderr or result.stdout)
        return json.loads(result.stdout)

    def test_shipped_checker_identity(self):
        release = json.loads((PROFILE / "validator-release.json").read_text())
        manifest = json.loads((PROFILE / "manifest.json").read_text())
        self.assertEqual(release["goos"], "linux")
        self.assertEqual(release["goarch"], "amd64")
        self.assertEqual(release["checkerInterface"], manifest["validatorFormatVersion"])
        self.assertEqual(
            hashlib.sha256((PROFILE / "validator").read_bytes()).hexdigest(),
            release["executableSha256"],
        )

    def test_capture_retains_only_known_duplicate(self):
        report = self.run_checker(expected_exit=1)
        self.assertFalse(report["valid"])
        self.assertTrue(report["integrityValid"])
        self.assertFalse(report["rulesValid"])
        self.assertEqual(report["filesChecked"], 10053)
        self.assertEqual(report["referencesChecked"], 65854)
        self.assertEqual(report["coverage"]["unboundModelInstances"], 0)
        self.assertEqual(report["errors"], [{
            "file": "Towers/BoomerangMonkey/BoomerangMonkey-012.json",
            "pointer": "/upgrades/2/tower",
            "code": "duplicate-purchase",
            "message": "purchase transition to build 0-1-3 is repeated",
            "rule": "ordinary-tower-progression",
        }])

    def test_dart_score_and_missing_required_state(self):
        report = self.run_checker(score=True)
        self.assertTrue(report["valid"])
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["score"]["points"], 100)
        self.assertTrue(report["score"]["complete"])
        self.assertEqual(report["filesChecked"], 99)
        self.assertEqual(report["referencesChecked"], 1001)

        # Copy bytes rather than links so deleting a state cannot alter the capture.
        with tempfile.TemporaryDirectory(prefix="btd6-atlas-profile-") as temporary:
            data = Path(temporary) / "game-data"
            shutil.copytree(CAPTURE, data)
            (data / "Towers/DartMonkey/DartMonkey-100.json").unlink()
            broken = self.run_checker(data, score=True, expected_exit=1)
        self.assertFalse(broken["valid"])
        self.assertLess(broken["score"]["points"], 100)
        self.assertFalse(broken["score"]["complete"])
        codes = {error["code"] for error in broken["errors"]}
        self.assertIn("missing_reference", codes)
        self.assertIn("missing-build", codes)

    def test_exporter_version_matches_project_metadata(self):
        project = ET.parse(ROOT / "mod/Btd6Atlas.csproj")
        source = (ROOT / "mod/AtlasExporter.cs").read_text()
        version = re.search(r'public const string ModVersion = "([^"]+)";', source)
        self.assertIsNotNone(version)
        self.assertEqual(project.findtext("PropertyGroup/Version"), version.group(1))


if __name__ == "__main__":
    unittest.main()
