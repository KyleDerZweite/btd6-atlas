"""Check that invalid downloads or schema drift cannot replace a validator."""

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import zipfile


spec = importlib.util.spec_from_file_location("installer", Path(__file__).with_name("install-validator.py"))
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def test_verified_native_archives_and_rejected_changes(self):
        for target, (extension, _) in installer.ARCHIVES.items():
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                schemas = root / "profile/schemas/game-data"
                schemas.mkdir(parents=True)
                schema = schemas / "tower.schema.json"
                schema.write_bytes(b"{}\n")
                (root / "profile/manifest.json").write_text('{"validatorFormatVersion":5}')
                binary = "validator.exe" if target.startswith("windows-") else "validator"
                bundle = f"td-profile-{installer.RELEASE}-{target}"
                files = {
                    binary: b"verified binary",
                    "profile/schemas/game-data/tower.schema.json": schema.read_bytes(),
                    "release.json": json.dumps({"checkerInterface": 5}).encode(),
                    "LICENSE": b"license",
                    "NOTICE.md": b"notice",
                    "licenses/jsonschema-go.LICENSE": b"dependency license",
                }
                output = io.BytesIO()
                if extension == "zip":
                    with zipfile.ZipFile(output, "w") as archive:
                        for name, data in files.items():
                            archive.writestr(f"{bundle}/{name}", data)
                else:
                    with tarfile.open(fileobj=output, mode="w:gz") as archive:
                        for name, data in files.items():
                            member = tarfile.TarInfo(f"{bundle}/{name}")
                            member.size = len(data)
                            archive.addfile(member, io.BytesIO(data))
                data = output.getvalue()
                checksum = hashlib.sha256(data).hexdigest()
                with patch.dict(installer.ARCHIVES, {target: (extension, checksum)}), \
                     patch.object(installer, "urlopen", side_effect=lambda *args, **kwargs: io.BytesIO(data)):
                    alternate = root / "profile" / ("validator" if binary == "validator.exe" else "validator.exe")
                    alternate.write_bytes(b"old platform binary")
                    installer.install(root, target)
                    executable = root / "profile" / binary
                    self.assertEqual(executable.read_bytes(), b"verified binary")
                    self.assertFalse(alternate.exists())
                    self.assertFalse((root / "bin").exists())
                    self.assertTrue((root / "profile/licenses/jsonschema-go.LICENSE").is_file())
                    metadata = json.loads((root / "profile/validator-release.json").read_text())
                    self.assertEqual(metadata["executableSha256"], hashlib.sha256(b"verified binary").hexdigest())
                    (root / "profile/manifest.json").write_text('{"validatorFormatVersion":99}')
                    with self.assertRaisesRegex(ValueError, "interface does not match"):
                        installer.install(root, target)
                    self.assertEqual(executable.read_bytes(), b"verified binary")
                    (root / "profile/manifest.json").write_text('{"validatorFormatVersion":5}')
                    schema.write_bytes(b'{"type":"object"}\n')
                    with self.assertRaisesRegex(ValueError, "schemas differ.*tower.schema.json"):
                        installer.install(root, target)
                    self.assertEqual(executable.read_bytes(), b"verified binary")
                    data = b"damaged archive"
                    with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                        installer.install(root, target)
                    self.assertEqual(executable.read_bytes(), b"verified binary")


if __name__ == "__main__":
    unittest.main()
