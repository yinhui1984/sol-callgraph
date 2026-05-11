import os

from sol_callgraph import slither_env


def _write_executable(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    path.chmod(0o755)


def test_fallback_homebrew_slither_used_when_path_is_minimal(tmp_path, monkeypatch):
    python = tmp_path / "cellar" / "libexec" / "bin" / "python"
    slither = tmp_path / "opt" / "homebrew" / "bin" / "slither"
    _write_executable(python, "#!/bin/sh\n")
    _write_executable(slither, f"#!{python}\n")

    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    monkeypatch.setattr(slither_env, "FALLBACK_SLITHER_BINS", [str(slither)])
    monkeypatch.setattr(slither_env, "FALLBACK_PYTHON_BINS", [])
    monkeypatch.setattr(slither_env, "validate_slither_python", lambda path: path == str(python))

    slither_path, resolved_path, python_path = slither_env.detect_slither_env()

    assert slither_path == str(slither)
    assert resolved_path == os.path.realpath(slither)
    assert python_path == str(python)


def test_pyenv_slither_shell_wrapper_is_not_inferred_as_python(tmp_path, monkeypatch):
    shim = tmp_path / "pyenv" / "shims" / "slither"
    _write_executable(shim, "#!/usr/bin/env bash\nexec slither \"$@\"\n")

    monkeypatch.setenv("PATH", "")
    monkeypatch.setattr(slither_env, "FALLBACK_SLITHER_BINS", [str(shim)])
    monkeypatch.setattr(slither_env, "FALLBACK_PYTHON_BINS", [])
    monkeypatch.setattr(slither_env.shutil, "which", lambda name: None)

    assert slither_env.infer_python_from_shebang(str(shim)) is None
    assert slither_env.detect_slither_env() == (None, None, None)


def test_skips_invalid_candidate_and_uses_first_valid_python(tmp_path, monkeypatch):
    bad_python = tmp_path / "bad" / "python"
    good_python = tmp_path / "good" / "python"
    bad_slither = tmp_path / "path" / "slither"
    good_slither = tmp_path / "opt" / "homebrew" / "bin" / "slither"
    _write_executable(bad_python, "#!/bin/sh\n")
    _write_executable(good_python, "#!/bin/sh\n")
    _write_executable(bad_slither, f"#!{bad_python}\n")
    _write_executable(good_slither, f"#!{good_python}\n")

    monkeypatch.setenv("PATH", str(bad_slither.parent))
    monkeypatch.setattr(slither_env, "FALLBACK_SLITHER_BINS", [str(good_slither)])
    monkeypatch.setattr(slither_env, "FALLBACK_PYTHON_BINS", [])
    monkeypatch.setattr(slither_env, "validate_slither_python", lambda path: path == str(good_python))

    slither_path, resolved_path, python_path = slither_env.detect_slither_env()

    assert slither_path == str(good_slither)
    assert resolved_path == os.path.realpath(good_slither)
    assert python_path == str(good_python)


def test_path_slither_keeps_priority_over_fallback(tmp_path, monkeypatch):
    path_python = tmp_path / "path-python" / "python"
    fallback_python = tmp_path / "fallback-python" / "python"
    path_slither = tmp_path / "path-bin" / "slither"
    fallback_slither = tmp_path / "opt" / "homebrew" / "bin" / "slither"
    _write_executable(path_python, "#!/bin/sh\n")
    _write_executable(fallback_python, "#!/bin/sh\n")
    _write_executable(path_slither, f"#!{path_python}\n")
    _write_executable(fallback_slither, f"#!{fallback_python}\n")

    monkeypatch.setenv("PATH", str(path_slither.parent))
    monkeypatch.setattr(slither_env, "FALLBACK_SLITHER_BINS", [str(fallback_slither)])
    monkeypatch.setattr(slither_env, "FALLBACK_PYTHON_BINS", [])
    monkeypatch.setattr(slither_env, "validate_slither_python", lambda path: True)

    slither_path, resolved_path, python_path = slither_env.detect_slither_env()

    assert slither_path == str(path_slither)
    assert resolved_path == os.path.realpath(path_slither)
    assert python_path == str(path_python)


def test_build_toolchain_env_appends_foundry(tmp_path, monkeypatch):
    foundry_bin = tmp_path / ".foundry" / "bin"
    foundry_bin.mkdir(parents=True)
    
    # Mock expanduser and isdir
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(foundry_bin) if "~/.foundry" in p else p)
    
    def mock_isdir(path):
        if path == str(foundry_bin): return True
        if path in ("/usr/bin", "/bin"): return True
        return False
        
    monkeypatch.setattr(os.path, "isdir", mock_isdir)
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    
    env = slither_env.build_toolchain_env()
    path = env["PATH"]
    
    assert "/usr/bin" in path
    assert "/bin" in path
    assert str(foundry_bin) in path
    # With our mock, only /usr/bin, /bin, and foundry_bin exist.
    # So path should be exactly this:
    assert path == f"/usr/bin:/bin:{foundry_bin}"


def test_build_toolchain_env_deduplicates_and_preserves_order(tmp_path, monkeypatch):
    foundry_bin = tmp_path / ".foundry" / "bin"
    foundry_bin.mkdir(parents=True)
    
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(foundry_bin) if "~/.foundry" in p else p)
    
    def mock_isdir(path):
        if path == str(foundry_bin): return True
        if path in ("/usr/bin", "/bin"): return True
        return False
        
    monkeypatch.setattr(os.path, "isdir", mock_isdir)
    # Put foundry_bin in the middle
    monkeypatch.setenv("PATH", f"/usr/bin:{foundry_bin}:/bin")
    
    env = slither_env.build_toolchain_env()
    path = env["PATH"]
    
    # Should stay where it was, and no extra paths added because they don't "exist"
    assert path == f"/usr/bin:{foundry_bin}:/bin"


def test_augment_process_path_updates_environ(tmp_path, monkeypatch):
    foundry_bin = tmp_path / ".foundry" / "bin"
    foundry_bin.mkdir(parents=True)
    
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(foundry_bin) if "~/.foundry" in p else p)
    monkeypatch.setattr(os.path, "isdir", lambda p: True) # Everything exists
    monkeypatch.setenv("PATH", "/usr/bin")
    
    slither_env.augment_process_path()
    
    assert str(foundry_bin) in os.environ["PATH"]
