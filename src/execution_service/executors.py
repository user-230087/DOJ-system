import abc
import os
import subprocess
import tempfile
from typing import Dict, List, Optional

class BaseLanguageExecutor(abc.ABC):
    """
    Template Method Pattern: Defines the skeletal execution flow across test cases,
    delegating language-specific hooks (compilation and run commands) to subclasses.
    """
    def execute(self, source_code: str, test_cases: List[dict], time_limit_ms: int) -> dict:
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Prepare source files
            self.prepare_source(tmpdir, source_code)

            # 2. Optional compilation step (e.g., C++)
            compilation_result = self.compile_code(tmpdir)
            if compilation_result and compilation_result.get("status") != "SUCCESS":
                return compilation_result

            # 3. Execution pipeline against test cases
            timeout_sec = time_limit_ms / 1000.0
            for i, tc in enumerate(test_cases):
                run_cmd = self.get_run_command(tmpdir)
                
                try:
                    result = subprocess.run(
                        run_cmd,
                        input=tc["input"],
                        text=True,
                        capture_output=True,
                        timeout=timeout_sec
                    )
                except subprocess.TimeoutExpired:
                    return {"status": "TIME_LIMIT_EXCEEDED", "failedTestCaseIndex": i}
                
                if result.returncode != 0:
                    return {
                        "status": "RUNTIME_ERROR",
                        "failedTestCaseIndex": i,
                        "stderr": result.stderr
                    }
                
                actual = result.stdout.replace("\r\n", "\n").strip()
                expected = tc["expectedOutput"].replace("\r\n", "\n").strip()
                
                if actual != expected:
                    return {
                        "status": "WRONG_ANSWER",
                        "failedTestCaseIndex": i,
                        "actualOutput": actual,
                        "expectedOutput": expected
                    }

            return {"status": "ACCEPTED"}

    @abc.abstractmethod
    def prepare_source(self, tmpdir: str, source_code: str):
        """Write source code to the appropriate file in the temp directory."""
        pass

    def compile_code(self, tmpdir: str) -> Optional[dict]:
        """Optional compilation step. Default returns None (no compilation needed)."""
        return None

    @abc.abstractmethod
    def get_run_command(self, tmpdir: str) -> List[str]:
        """Return the subprocess list command to execute the solution."""
        pass


class PythonExecutor(BaseLanguageExecutor):
    def prepare_source(self, tmpdir: str, source_code: str):
        self.src_path = os.path.join(tmpdir, "solution.py")
        with open(self.src_path, "w") as f:
            f.write(source_code)

    def get_run_command(self, tmpdir: str) -> List[str]:
        return [
            "docker", "run", "--rm", "-i",
            "--network=none",
            "--memory=128m",
            "--cpus=1.0",
            "--pids-limit=64",
            "-v", f"{tmpdir}:/workspace",
            "python:3.10-slim",
            "python", "/workspace/solution.py"
        ]


class CPlusPlusExecutor(BaseLanguageExecutor):
    def prepare_source(self, tmpdir: str, source_code: str):
        self.src_path = os.path.join(tmpdir, "solution.cpp")
        with open(self.src_path, "w") as f:
            f.write(source_code)

    def compile_code(self, tmpdir: str) -> Optional[dict]:
        compile_cmd = [
            "docker", "run", "--rm",
            "--network=none",
            "--memory=256m",
            "--cpus=1.0",
            "-v", f"{tmpdir}:/workspace",
            "gcc:latest",
            "g++", "-O3", "/workspace/solution.cpp", "-o", "/workspace/solution"
        ]
        res = subprocess.run(compile_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            return {
                "status": "COMPILATION_ERROR",
                "stderr": res.stderr
            }
        return {"status": "SUCCESS"}

    def get_run_command(self, tmpdir: str) -> List[str]:
        return [
            "docker", "run", "--rm", "-i",
            "--network=none",
            "--memory=128m",
            "--cpus=1.0",
            "--pids-limit=64",
            "-v", f"{tmpdir}:/workspace",
            "gcc:latest",
            "/workspace/solution"
        ]


class ExecutorFactory:
    _executors: Dict[str, BaseLanguageExecutor] = {
        "PYTHON": PythonExecutor(),
        "CPP": CPlusPlusExecutor(),
    }

    @classmethod
    def get_executor(cls, language: str) -> BaseLanguageExecutor:
        executor = cls._executors.get(language.upper())
        if not executor:
            raise ValueError(f"Unsupported language: {language}")
        return executor