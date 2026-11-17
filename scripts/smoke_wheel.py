"""Install the built wheel into a clean venv and exercise both entry points."""

import json
import os
import subprocess
import tarfile
import tempfile
import venv
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sdists = list((root / "dist").glob("*.tar.gz"))
if len(sdists) != 1:
    raise SystemExit("Build exactly one source distribution before this check.")
with tarfile.open(sdists[0]) as archive:
    expected_examples = {".env.example", "complete.env", "drift.env"}
    examples = {
        "/".join(Path(name).parts[2:])
        for name in archive.getnames()
        if len(Path(name).parts) > 2 and Path(name).parts[1] == "examples"
    }
    if examples != expected_examples:
        raise SystemExit("Source archive must include only the three public example fixtures.")
wheels = list((root / "dist").glob("*.whl"))
if len(wheels) != 1:
    raise SystemExit("Build exactly one wheel before running this smoke check.")

with tempfile.TemporaryDirectory() as temp:
    location = Path(temp)
    venv.EnvBuilder(with_pip=True).create(location / "venv")
    binaries = location / "venv" / ("Scripts" if os.name == "nt" else "bin")
    python = binaries / ("python.exe" if os.name == "nt" else "python")
    cli = binaries / ("dotenv-audit.exe" if os.name == "nt" else "dotenv-audit")
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    subprocess.run(
        [str(python), "-m", "pip", "install", "--no-index", "--no-deps", str(wheels[0])],
        cwd=location,
        env=environment,
        check=True,
    )
    common = ["--example", str(root / "examples" / ".env.example")]
    good = subprocess.run(
        [str(cli), *common, "--env", str(root / "examples" / "complete.env")],
        cwd=location,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )
    if "PASS" not in good.stdout:
        raise SystemExit("Installed console script did not produce a successful audit.")
    bad = subprocess.run(
        [
            str(python),
            "-m",
            "dotenv_audit",
            *common,
            "--env",
            str(root / "examples" / "drift.env"),
            "--check-empty",
            "--strict",
            "--format",
            "json",
        ],
        cwd=location,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    data = json.loads(bad.stdout)
    if bad.returncode != 1 or data["ok"] or data["summary"]["errors"] != 4:
        raise SystemExit("Installed module did not reject the drift fixture correctly.")
    print("Installed wheel smoke check passed: console script, module, JSON, and exit codes.")
