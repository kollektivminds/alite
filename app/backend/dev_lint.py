"""
ALITE Unified Code Quality & Security Orchestrator.

Triggers backend checks via Poetry and frontend checks via npm.
Multiplexes output to both the console and a timestamped log file 
to ensure long outputs remain scrollable and auditable.
"""

from datetime import datetime
from pathlib import Path
import subprocess
import sys
from typing import TextIO


def execute_and_log(command: list[str], cwd: Path, description: str, log_file: TextIO) -> bool:
    """
    Executes a shell command and multiplexes its output to the console and a log file.

    Args:
        command: List of command arguments (e.g., ["npm", "run", "lint"]).
        cwd: Directory path in which to execute the process.
        description: Human-readable task label.
        log_file: An open file handle for writing the log output.

    Returns:
        Boolean indicating process success (True) or failure (False).
    """
    # Create a clear visual separator for both console and log readability
    header = f"\n{'='*70}\n--- Running: {description} ---\n{'='*70}\n"
    print(header, end="")
    log_file.write(header)

    try:
        # capture_output=True intercepts stdout and stderr instead of printing directly
        # text=True decodes the byte streams into strings
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        
        # If the tool generated output, route it to both destinations
        if result.stdout:
            print(result.stdout, end="")
            log_file.write(result.stdout)
            
        # Linters sometimes write to stderr even if they don't hard-crash.
        # We must capture this to ensure we don't miss critical vulnerability warnings.
        if result.stderr:
            print(result.stderr, end="")
            log_file.write(result.stderr)

        return result.returncode == 0

    except FileNotFoundError:
        error_msg = f"Error: Executable '{command[0]}' not found in environment.\n"
        print(error_msg)
        log_file.write(error_msg)
        return False


def main() -> None:
    """Orchestrates static analysis and handles log file generation."""
    # 1. Path Resolution
    root_dir = Path(__file__).resolve().parent.parent
    backend_dir = root_dir / "backend"
    frontend_dir = root_dir / "frontend"

    # 2. Log Directory Initialization
    logs_dir = root_dir / ".logs"
    logs_dir.mkdir(parents=True, exist_ok=True) # Ensure directory exists safely
    
    # Generate timestamp (e.g., 20260807_175132_audit.log)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = logs_dir / f"{timestamp}_audit.log"

    success = True

    # 3. Execute Suite with an open log file handle
    print(f"Initializing ALITE Audit. Logs will be saved to: {log_file_path.relative_to(root_dir)}")
    
    with open(log_file_path, "w", encoding="utf-8") as log_file:
        
        # Log environment metadata for debugging context
        log_file.write(f"ALITE Code Quality Audit Log\n")
        log_file.write(f"Date: {datetime.now().isoformat()}\n\n")

        # Backend Checks
        success &= execute_and_log(
            ["poetry", "run", "ruff", "check", "."],
            cwd=backend_dir,
            description="Backend Linter & Security (Ruff)",
            log_file=log_file
        )
        success &= execute_and_log(
            ["poetry", "run", "mypy", "."],
            cwd=backend_dir,
            description="Backend Type Checking (Mypy)",
            log_file=log_file
        )

        # Frontend Checks
        success &= execute_and_log(
            ["pnpm", "run", "lint"],
            cwd=frontend_dir,
            description="Frontend Linter & Security (ESLint)",
            log_file=log_file
        )

        # 4. Final Result Aggregation
        footer = "\n" + "="*70 + "\n"
        if not success:
            footer += "[FAIL] Code quality and security checks failed. Please fix errors.\n"
            print(footer)
            log_file.write(footer)
            sys.exit(1)

        footer += "[SUCCESS] All full-stack quality checks passed!\n"
        print(footer)
        log_file.write(footer)
        sys.exit(0)


if __name__ == "__main__":
    main()