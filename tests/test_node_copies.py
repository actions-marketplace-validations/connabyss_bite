"""Where Bite makes its copies of a JavaScript project. No network.

Copies used to go inside the project's node_modules/, so Node found its packages above them. But tools that skip
anything under node_modules (jest, @babel/register, tap) skipped the copy too: on validator.js every commit showed
as "tests already fail" though its tests pass (the 11-03 hunt). Now each copy sits outside the project, with a link
to the project's node_modules."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

KIT = Path(__file__).parent.parent
sys.path.insert(0, str(KIT))

import recent  # noqa: E402
import repo  # noqa: E402

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]


def make(tmp_path):
    root = tmp_path / "proj"
    (root / "packages" / "app").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / ".gitignore").write_text("node_modules\n")
    (root / "shop.js").write_text("module.exports = require('left-pad');\n")
    (root / "packages" / "app" / "index.js").write_text("module.exports = require('app-dep');\n")
    pkg = root / "node_modules" / "left-pad"
    pkg.mkdir(parents=True)
    (pkg / "index.js").write_text("module.exports = 'padded';\n")
    dep = root / "packages" / "app" / "node_modules" / "app-dep"
    dep.mkdir(parents=True)
    (dep / "index.js").write_text("module.exports = 'dep';\n")
    subprocess.run([*GIT, "add", "-A"], cwd=root, check=True)
    subprocess.run([*GIT, "commit", "-q", "-m", "start"], cwd=root, check=True)
    return root


def test_node_copies_sit_outside_node_modules_and_see_the_packages(tmp_path):
    root = make(tmp_path)
    cfg = repo.load_cfg(root)
    dest = recent.export(root, "HEAD", cfg)
    try:
        assert "node_modules" not in dest.resolve().parts, dest
        assert not dest.resolve().is_relative_to(root.resolve()), dest
        assert (dest / "node_modules" / "left-pad" / "index.js").read_text() == "module.exports = 'padded';\n"
        assert (dest / "packages" / "app" / "node_modules" / "app-dep" / "index.js").is_file()
        assert not any(p.startswith(".") for p in dest.resolve().relative_to(dest.parent.parent.resolve()).parts)
    finally:
        shutil.rmtree(dest.parent, ignore_errors=True)
    # Removing the copy removes only the links, never the project's packages.
    assert (root / "node_modules" / "left-pad" / "index.js").is_file()
    assert (root / "packages" / "app" / "node_modules" / "app-dep" / "index.js").is_file()


@pytest.mark.skipif(sys.platform != "win32", reason="junctions are Windows only")
def test_a_junction_is_removed_without_its_contents(tmp_path, monkeypatch):
    # Without the right to make symlinks, Windows gets a junction, which any user can make.
    root = make(tmp_path)
    monkeypatch.setattr(repo.os, "symlink", lambda *a, **k: (_ for _ in ()).throw(OSError("no right")))
    dest = recent.export(root, "HEAD", repo.load_cfg(root))
    assert (dest / "node_modules" / "left-pad" / "index.js").is_file()
    shutil.rmtree(dest.parent, ignore_errors=True)
    assert (root / "node_modules" / "left-pad" / "index.js").is_file()


@pytest.mark.skipif(shutil.which("node") is None, reason="needs Node.js")
def test_node_finds_the_packages_in_a_copy(tmp_path):
    root = make(tmp_path)
    dest = recent.export(root, "HEAD", repo.load_cfg(root))
    try:
        out = subprocess.run(["node", "-e", "console.log(require('./shop.js'), require('./packages/app'))"], cwd=dest,
                             capture_output=True, text=True, timeout=60)
        assert out.stdout.strip() == "padded dep", out.stderr
    finally:
        shutil.rmtree(dest.parent, ignore_errors=True)
