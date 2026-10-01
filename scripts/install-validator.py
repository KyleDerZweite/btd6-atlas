#!/usr/bin/env python3
"""Place one pinned native td-profile binary beside the BTD6 Profile."""

import hashlib
import io
import json
from pathlib import Path
import platform
import sys
import tarfile
from urllib.request import urlopen
import zipfile


RELEASE = "v1.0.2"
ARCHIVES = {
    "linux-amd64": ("tar.gz", "830f263683bbe895ed0be51a2e1c9afd4b9cc30b5d93d57d3ad33fb6dfdadd20"),
    "darwin-arm64": ("tar.gz", "9590a5dd0093660465aaa9b37437add42ccad990a9482f0f551941753669ff96"),
    "windows-amd64": ("zip", "eba43fe422d77eb22c5d049f59e9bf96edbd11b21c40548e6ae694a0ec369832"),
}


def native_target():
    machine = platform.machine().lower()
    architecture = {"x86_64": "amd64", "aarch64": "arm64"}.get(machine, machine)
    target = f"{platform.system().lower()}-{architecture}"
    if target not in ARCHIVES:
        raise ValueError(f"No pinned binary for {target}; supported targets: {', '.join(ARCHIVES)}")
    return target


def install(root, target):
    extension, checksum = ARCHIVES[target]
    bundle = f"td-profile-{RELEASE}-{target}"
    destination = root / "profile"
    asset = f"{bundle}.{extension}"
    url = f"https://github.com/mardwerk/td-profile/releases/download/{RELEASE}/{asset}"
    print(f"Downloading {url}", flush=True)
    with urlopen(url, timeout=30) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != checksum:
        raise ValueError(f"Archive checksum mismatch: {asset}")

    if extension == "zip":
        archive = zipfile.ZipFile(io.BytesIO(data))
        names = archive.namelist()
        read = archive.read
    else:
        archive = tarfile.open(fileobj=io.BytesIO(data), mode="r:gz")
        names = archive.getnames()

        def read(name):
            member = archive.getmember(name)
            if not member.isfile():
                raise ValueError(f"Expected a regular archive file: {name}")
            return archive.extractfile(member).read()

    with archive:
        # Compare local copies; never replace game settings with the starter Profile.
        prefix = f"{bundle}/profile/schemas/"
        schemas = {name[len(prefix):]: read(name) for name in names
                   if name.startswith(prefix) and name.endswith(".json")}
        local_schemas = {path.relative_to(root / "profile/schemas").as_posix(): path.read_bytes()
                         for path in (root / "profile/schemas").rglob("*.json")}
        differences = sorted(name for name in schemas.keys() | local_schemas.keys()
                             if schemas.get(name) != local_schemas.get(name))
        if not schemas or differences:
            raise ValueError(f"Profile schemas differ from {RELEASE}: {', '.join(differences)}")

        release = json.loads(read(f"{bundle}/release.json"))
        manifest = json.loads((root / "profile/manifest.json").read_text())
        if release["checkerInterface"] != manifest["validatorFormatVersion"]:
            raise ValueError("Pinned checker interface does not match the BTD6 Profile")

        binary = "validator.exe" if target.startswith("windows-") else "validator"
        executable = read(f"{bundle}/{binary}")
        notices = {
            "td-profile.LICENSE": read(f"{bundle}/LICENSE"),
            "td-profile.NOTICE.md": read(f"{bundle}/NOTICE.md"),
            "jsonschema-go.LICENSE": read(f"{bundle}/licenses/jsonschema-go.LICENSE"),
        }

    # Release metadata describes the checker, not the upstream starter Profile.
    release.pop("profile", None)
    release["archiveSha256"] = checksum
    release["executableSha256"] = hashlib.sha256(executable).hexdigest()
    (destination / "licenses").mkdir(exist_ok=True)
    for name, content in notices.items():
        path = destination / "licenses" / name
        path.write_bytes(content)
    (destination / "validator-release.json").write_text(json.dumps(release, indent=2) + "\n")
    temporary = destination / f"{binary}.tmp"
    temporary.write_bytes(executable)
    temporary.chmod(0o755)
    temporary.replace(destination / binary)
    alternate = destination / ("validator" if binary == "validator.exe" else "validator.exe")
    alternate.unlink(missing_ok=True)
    print(f"Installed {RELEASE} to {destination / binary}")


if __name__ == "__main__":
    try:
        install(Path(__file__).resolve().parents[1], native_target())
    except (OSError, ValueError, KeyError, tarfile.TarError, zipfile.BadZipFile) as error:
        sys.exit(f"install-validator: {error}")
