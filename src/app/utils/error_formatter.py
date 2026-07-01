"""
Error formatting and parsing for novice-friendly messages.
"""

import re
from typing import Optional, Dict, Any


class ErrorFormatter:
    """Format execution errors for novice users"""

    @staticmethod
    def format_syntax_error(logs: str) -> Dict[str, Any]:
        """Parse syntax error and extract line number"""
        lines = logs.split("\n")

        # Look for SyntaxError line
        for i, line in enumerate(lines):
            if "SyntaxError" in line:
                line_num = ErrorFormatter._extract_line_number(line)
                message = ErrorFormatter._extract_error_message(line)
                hint = ErrorFormatter._get_syntax_error_hint(message, logs)

                return {
                    "type": "SyntaxError",
                    "message": message,
                    "line": line_num,
                    "hint": hint,
                    "stackTrace": None
                }

        return {
            "type": "SyntaxError",
            "message": "Syntax error in your code",
            "line": None,
            "hint": "Check for missing colons, brackets, or parentheses",
            "stackTrace": None
        }

    @staticmethod
    def format_import_error(logs: str) -> Dict[str, Any]:
        """Parse import error"""
        lines = logs.split("\n")

        for line in lines:
            if "ModuleNotFoundError" in line or "ImportError" in line:
                message = line.strip()
                module_name = ErrorFormatter._extract_module_name(message)

                return {
                    "type": "ImportError",
                    "message": f"Cannot import '{module_name}'",
                    "line": None,
                    "hint": f"Make sure '{module_name}' is installed or spelled correctly",
                    "stackTrace": None
                }

        return {
            "type": "ImportError",
            "message": "Import error - module not found",
            "line": None,
            "hint": "Check that all imports are correctly spelled and available",
            "stackTrace": None
        }

    @staticmethod
    def format_runtime_error(logs: str) -> Dict[str, Any]:
        """Parse runtime error with context"""
        lines = logs.split("\n")
        error_type = None
        error_message = None
        line_num = None

        # Extract error info
        for i, line in enumerate(lines):
            if "Error" in line and ":" in line:
                parts = line.split(":", 1)
                error_type = parts[0].strip()
                error_message = parts[1].strip() if len(parts) > 1 else "Unknown error"

                # Try to find line number in previous lines
                for j in range(max(0, i - 5), i):
                    line_num = ErrorFormatter._extract_line_number(lines[j])
                    if line_num:
                        break

        if not error_type:
            error_type = "RuntimeError"
            error_message = "An error occurred during execution"

        hint = ErrorFormatter._get_runtime_error_hint(error_type, error_message)

        return {
            "type": error_type,
            "message": error_message,
            "line": line_num,
            "hint": hint,
            "stackTrace": ErrorFormatter._extract_stack_trace(logs)
        }

    @staticmethod
    def format_test_failure(test_name: str, logs: str) -> Dict[str, Any]:
        """Format test failure with assertion details"""
        # Try to extract assertion error
        assertion_error = None
        for line in logs.split("\n"):
            if "AssertionError" in line or "assert" in line.lower():
                assertion_error = line.strip()
                break

        hint = "Check that your function returns the expected value"
        if assertion_error:
            hint = f"Expected assertion to pass: {assertion_error[:100]}"

        return {
            "name": test_name,
            "status": "Failed",
            "error": assertion_error or "Test assertion failed",
            "hint": hint
        }

    @staticmethod
    def format_timeout_error() -> Dict[str, Any]:
        """Format timeout error"""
        return {
            "type": "TimeoutError",
            "message": "Code execution exceeded 5 second timeout",
            "line": None,
            "hint": "Your code might have an infinite loop or is taking too long. Check for loops that never exit.",
            "stackTrace": None
        }

    @staticmethod
    def format_docker_error(error_message: str) -> Dict[str, Any]:
        """Format Docker-related errors"""
        return {
            "type": "ExecutionError",
            "message": "Failed to execute code in container",
            "line": None,
            "hint": "The execution environment encountered an error. Try running your code locally first.",
            "stackTrace": None
        }

    # Helper methods

    @staticmethod
    def _extract_line_number(line: str) -> Optional[int]:
        """Extract line number from error message"""
        # Look for patterns like "line 5" or ", 5,"
        match = re.search(r'line (\d+)', line, re.IGNORECASE)
        if match:
            return int(match.group(1))

        match = re.search(r', (\d+),', line)
        if match:
            return int(match.group(1))

        return None

    @staticmethod
    def _extract_error_message(line: str) -> str:
        """Extract clean error message"""
        # Remove file paths and line numbers
        message = re.sub(r'File ".*".*', '', line)
        message = re.sub(r'line \d+', '', message, flags=re.IGNORECASE)
        message = message.replace(",", "").strip()
        return message or "Unknown error"

    @staticmethod
    def _extract_module_name(error_line: str) -> str:
        """Extract module name from import error"""
        match = re.search(r"'([^']+)'", error_line)
        if match:
            return match.group(1)
        return "unknown_module"

    @staticmethod
    def _extract_stack_trace(logs: str) -> Optional[str]:
        """Extract stack trace for display"""
        lines = logs.split("\n")
        stack_lines = []

        in_traceback = False
        for line in lines:
            if "Traceback" in line:
                in_traceback = True
            if in_traceback:
                stack_lines.append(line)
                if "Error:" in line:
                    break

        if stack_lines:
            return "\n".join(stack_lines[:10])  # Limit to first 10 lines
        return None

    @staticmethod
    def _get_syntax_error_hint(error_message: str, logs: str) -> str:
        """Provide hint for common syntax errors"""
        error_lower = error_message.lower()

        hints = {
            "unexpected eof": "Missing closing bracket or parenthesis",
            "invalid syntax": "Check for missing colons (:) at end of lines or unmatched brackets",
            "unexpected indent": "Check indentation - lines should be indented with spaces after ':' ",
            "expected ':'": "Missing colon (:) - did you forget it after def, if, for, or while?",
            "unexpected token": "Check for typos or invalid characters",
        }

        for key, hint in hints.items():
            if key in error_lower:
                return hint

        return "Check your code syntax - missing colons, brackets, or quotes?"

    @staticmethod
    def _get_runtime_error_hint(error_type: str, error_message: str) -> str:
        """Provide hint for common runtime errors"""
        hints = {
            "NameError": "You used a variable that doesn't exist. Did you spell it correctly?",
            "TypeError": "You used a function or operator with the wrong type of data",
            "ValueError": "You passed an invalid value to a function",
            "ZeroDivisionError": "You tried to divide by zero - check your math operations",
            "IndexError": "You tried to access a list index that doesn't exist",
            "KeyError": "You tried to access a dictionary key that doesn't exist",
            "AttributeError": "You tried to access an attribute that doesn't exist on an object",
            "FileNotFoundError": "The file you tried to open doesn't exist",
        }

        for error, hint in hints.items():
            if error in error_type:
                return hint

        return "Check your code logic and data types"
