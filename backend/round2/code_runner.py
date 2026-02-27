import subprocess
import tempfile
import os
import shlex
from typing import Tuple


def run_python_code(code: str, timeout: int = 5) -> Tuple[int, str, str]:
    # write to temp file
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
        tf.write(code)
        path = tf.name
    try:
        proc = subprocess.run(["python3", path], capture_output=True, text=True, timeout=timeout)
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    finally:
        try:
            os.remove(path)
        except Exception:
            pass


def run_code(language: str, code: str, timeout: int = 5):
    if language.lower() == "python":
        return run_python_code(code, timeout=timeout)
    elif language.lower() == "java":
        # Placeholder: Java execution not implemented in this runner for security.
        return -2, "", "java-runner-not-implemented"
    else:
        return -2, "", "language-not-supported"
