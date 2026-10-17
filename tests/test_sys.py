import pytest

import _sys


@pytest.fixture
def no_tools(monkeypatch):
    """Pretend no package managers are on PATH so detection relies on os-release."""
    monkeypatch.setattr(_sys.shutil, "which", lambda name: None)


def fake_linux(monkeypatch, os_release: dict):
    monkeypatch.setattr(_sys, "system", lambda: "Linux")
    monkeypatch.setattr(_sys, "read_os_release", lambda: os_release)


def test_read_os_release(tmp_path):
    path = tmp_path / "os-release"
    path.write_text('NAME="Ubuntu"\nID=ubuntu\nID_LIKE=debian\n# comment\n\n')
    assert _sys.read_os_release(str(path)) == {
        "NAME": "Ubuntu",
        "ID": "ubuntu",
        "ID_LIKE": "debian",
    }


def test_read_os_release_missing_file(tmp_path):
    assert _sys.read_os_release(str(tmp_path / "missing")) == {}


@pytest.mark.parametrize(
    "os_release, expected",
    [
        ({"ID": "debian"}, "debian"),
        ({"ID": "ubuntu", "ID_LIKE": "debian"}, "debian"),
        ({"ID": "linuxmint", "ID_LIKE": "ubuntu debian"}, "debian"),
        ({"ID": "rhel", "ID_LIKE": "fedora"}, "rhel"),
        ({"ID": "rocky", "ID_LIKE": "rhel centos fedora"}, "rhel"),
        ({"ID": "fedora"}, "rhel"),
        ({"ID": "arch"}, "unsupported"),
        ({}, "unsupported"),
    ],
)
def test_detect_platform_linux(monkeypatch, no_tools, os_release, expected):
    fake_linux(monkeypatch, os_release)
    assert _sys.detect_platform() == expected


@pytest.mark.parametrize("tool, expected", [("apt-get", "debian"), ("dnf", "rhel"), ("yum", "rhel")])
def test_detect_platform_falls_back_to_package_manager(monkeypatch, tool, expected):
    fake_linux(monkeypatch, {"ID": "unknown"})
    monkeypatch.setattr(_sys.shutil, "which", lambda name: f"/usr/bin/{name}" if name == tool else None)
    assert _sys.detect_platform() == expected


@pytest.mark.parametrize("name, expected", [("Darwin", "macos"), ("Windows", "unsupported")])
def test_detect_platform_other_os(monkeypatch, name, expected):
    monkeypatch.setattr(_sys, "system", lambda: name)
    assert _sys.detect_platform() == expected


def commands(capsys):
    return [line[2:] for line in capsys.readouterr().out.splitlines() if line.startswith("+ ")]


def test_install_debian_as_root(monkeypatch, capsys):
    monkeypatch.setattr(_sys.os, "geteuid", lambda: 0)
    _sys.install_debian(_sys.Installer(dry_run=True))
    cmds = commands(capsys)
    assert cmds[0] == "apt-get update"
    assert cmds[1].startswith("env DEBIAN_FRONTEND=noninteractive apt-get install -y")
    for package in _sys.APT_PACKAGES:
        assert package in cmds[1]


def test_install_debian_uses_sudo_when_not_root(monkeypatch, capsys):
    monkeypatch.setattr(_sys.os, "geteuid", lambda: 1000)
    _sys.install_debian(_sys.Installer(dry_run=True))
    assert all(cmd.startswith("sudo ") for cmd in commands(capsys))


@pytest.mark.parametrize("available, expected", [("dnf", "dnf"), (None, "yum")])
def test_install_rhel(monkeypatch, capsys, available, expected):
    monkeypatch.setattr(_sys.os, "geteuid", lambda: 0)
    monkeypatch.setattr(_sys.shutil, "which", lambda name: name if name == available else None)
    _sys.install_rhel(_sys.Installer(dry_run=True))
    cmds = commands(capsys)
    assert cmds[0].startswith(f"{expected} install -y ")
    joined = "\n".join(cmds)
    assert f"leptonica-{_sys.LEPTONICA_VERSION}" in joined
    assert f"tesseract-{_sys.TESSERACT_VERSION}" in joined
    assert "ldconfig" in joined
    assert cmds[-1].endswith(f"{_sys.PREFIX}/share/tessdata/eng.traineddata")


def test_install_python_requirements(capsys):
    _sys.install_python_requirements(_sys.Installer(dry_run=True))
    (cmd,) = commands(capsys)
    assert cmd.endswith(f"-m pip install -r {_sys.REPO_DIR / 'requirements.txt'}")


def test_main_unsupported_platform_exits(monkeypatch):
    monkeypatch.setattr(_sys, "detect_platform", lambda: "unsupported")
    monkeypatch.setattr(_sys.sys, "argv", ["_sys.py", "--dry-run"])
    with pytest.raises(SystemExit) as exc:
        _sys.main()
    assert "unsupported platform" in str(exc.value.code)


def test_main_skip_everything_dry_run(monkeypatch, capsys):
    monkeypatch.setattr(_sys.sys, "argv", ["_sys.py", "--dry-run", "--skip-system", "--skip-pip"])
    _sys.main()
    assert commands(capsys) == []
