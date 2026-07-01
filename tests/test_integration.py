"""
Integration tests for the execution engine.
Tests the complete workflow from API request to execution result.
"""

import pytest
import os
import asyncio
from fastapi.testclient import TestClient
from pathlib import Path

# Setup environment - matches .env dev key
os.environ["EXECUTOR_API_KEY"] = "dev_key_12345678901234567890CHANGE_IN_PROD"

from src.app.main import app

client = TestClient(app)


class TestExecuteEndpoint:
    """Test the POST /execute endpoint"""

    def test_valid_python_execution(self):
        """Test complete Python execution workflow"""
        code = """
def add(a, b):
    return a + b
"""
        tests = """
from user_code import add
def test_add():
    assert add(2, 3) == 5
"""        
        response = client.post(
            "/execute",
            json={
                "language": "python",
                "exerciseId": "test_valid_python",
                "code": code,
                "tests": tests
            },
            headers={"X-API-Key": "dev_key_12345678901234567890CHANGE_IN_PROD"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["passed"] == True
        assert data["totalTests"] == 1
        assert data["passedTests"] == 1
        assert data["failedTests"] == 0

    def test_python_execution_with_multiple_tests(self):
        """Test Python execution with multiple tests"""
        code = """
def multiply(a, b):
    return a * b
"""
        tests = """
from user_code import multiply

def test_positive():
    assert multiply(3, 4) == 12

def test_zero():
    assert multiply(5, 0) == 0

def test_negative():
    assert multiply(-2, 3) == -6
"""
        response = client.post(
            "/execute",
            json={
                "language": "python",
                "exerciseId": "test_multiple",
                "code": code,
                "tests": tests
            },
            headers={"X-API-Key": "dev_key_12345678901234567890CHANGE_IN_PROD"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["passed"] == True
        assert data["totalTests"] == 3
        assert data["passedTests"] == 3

    def test_python_with_failing_tests(self):
        """Test Python execution with failing tests"""
        code = """
def is_even(n):
    return n % 2 == 0
"""
        tests = """
from user_code import is_even

def test_even():
    assert is_even(4) == True

def test_odd():
    assert is_even(3) == True

def test_zero():
    assert is_even(0) == True
"""
        response = client.post(
            "/execute",
            json={
                "language": "python",
                "exerciseId": "test_failing",
                "code": code,
                "tests": tests
            },
            headers={"X-API-Key": "dev_key_12345678901234567890CHANGE_IN_PROD"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["passed"] == False
        assert data["totalTests"] == 3
        assert data["failedTests"] == 1
        assert data["passedTests"] == 2

    def test_syntax_error_in_code(self):
        """Test syntax error handling in user code during import"""
        code = """
def broken(
    pass
"""
        tests = """
from user_code import broken

def test_import():
    pass
"""
        response = client.post(
            "/execute",
            json={
                "language": "python",
                "exerciseId": "test_syntax_error",
                "code": code,
                "tests": tests
            },
            headers={"X-API-Key": "dev_key_12345678901234567890CHANGE_IN_PROD"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["passed"] == False
        assert data["totalTests"] == 0
        assert data["error"] is not None

    def test_import_error_in_test(self):
        """Test import error handling"""
        code = """
def dummy():
    pass
"""
        tests = """
from missing_module import something

def test_dummy():
    pass
"""
        response = client.post(
            "/execute",
            json={
                "language": "python",
                "exerciseId": "test_import_error",
                "code": code,
                "tests": tests
            },
            headers={"X-API-Key": "dev_key_12345678901234567890CHANGE_IN_PROD"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["passed"] == False
        assert data["totalTests"] == 0
        assert data["error"] is not None
        assert data["error"]["type"] == "ImportError"

    def test_runtime_error(self):
        """Test runtime error handling"""
        code = """
def divide(a, b):
    return a / b
"""
        tests = """
from user_code import divide

def test_division():
    assert divide(10, 0) == float('inf')
"""
        response = client.post(
            "/execute",
            json={
                "language": "python",
                "exerciseId": "test_runtime_error",
                "code": code,
                "tests": tests
            },
            headers={"X-API-Key": "dev_key_12345678901234567890CHANGE_IN_PROD"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["passed"] == False


class TestAuthentication:
    """Test API key authentication"""

    def test_missing_api_key(self):
        """Missing API key should return 401"""
        response = client.post(
            "/execute",
            json={
                "language": "python",
                "exerciseId": "test_no_key",
                "code": "def f(): pass",
                "tests": "def t(): pass"
            }
        )
        assert response.status_code == 401

    def test_invalid_api_key(self):
        """Invalid API key should return 401"""
        response = client.post(
            "/execute",
            json={
                "language": "python",
                "exerciseId": "test_bad_key",
                "code": "def f(): pass",
                "tests": "def t(): pass"
            },
            headers={"X-API-Key": "wrong_key"}
        )
        assert response.status_code == 401

    def test_health_check_no_auth(self):
        """Health check should work without authentication"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "running"


class TestValidation:
    """Test request validation"""

    def test_invalid_language(self):
        """Invalid language should return 422"""
        response = client.post(
            "/execute",
            json={
                "language": "ruby",
                "exerciseId": "test_invalid_lang",
                "code": "def f(): pass",
                "tests": "def t(): pass"
            },
            headers={"X-API-Key": "dev_key_12345678901234567890CHANGE_IN_PROD"}
        )
        assert response.status_code == 422

    def test_missing_code_field(self):
        """Missing code field should return 422"""
        response = client.post(
            "/execute",
            json={
                "language": "python",
                "exerciseId": "test_no_code",
                "tests": "def t(): pass"
            },
            headers={"X-API-Key": "dev_key_12345678901234567890CHANGE_IN_PROD"}
        )
        assert response.status_code == 422

    def test_missing_tests_field(self):
        """Missing tests field should return 422"""
        response = client.post(
            "/execute",
            json={
                "language": "python",
                "exerciseId": "test_no_tests",
                "code": "def f(): pass"
            },
            headers={"X-API-Key": "dev_key_12345678901234567890CHANGE_IN_PROD"}
        )
        assert response.status_code == 422

    def test_invalid_exercise_id(self):
        """Invalid exerciseId format should return 422"""
        response = client.post(
            "/execute",
            json={
                "language": "python",
                "exerciseId": "Test-Invalid",  # Contains uppercase and dash
                "code": "def f(): pass",
                "tests": "def t(): pass"
            },
            headers={"X-API-Key": "dev_key_12345678901234567890CHANGE_IN_PROD"}
        )
        assert response.status_code == 422


class TestResponseFormat:
    """Test response format compliance"""

    def test_response_contains_all_fields(self):
        """Response should contain all required fields"""
        code = """
def f():
    pass
"""
        tests = """
def test_f():
    pass
"""
        response = client.post(
            "/execute",
            json={
                "language": "python",
                "exerciseId": "test_format",
                "code": code,
                "tests": tests
            },
            headers={"X-API-Key": "dev_key_12345678901234567890CHANGE_IN_PROD"}
        )

        data = response.json()
        required_fields = [
            "passed",
            "totalTests",
            "passedTests",
            "failedTests",
            "executionTime",
            "memory",
            "stdout",
            "stderr",
            "tests",
            "error"
        ]

        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_test_result_format(self):
        """Test results should have correct format"""
        code = """
def add(a, b):
    return a + b
"""
        tests = """
from user_code import add

def test_add():
    assert add(1, 2) == 3
"""
        response = client.post(
            "/execute",
            json={
                "language": "python",
                "exerciseId": "test_result_format",
                "code": code,
                "tests": tests
            },
            headers={"X-API-Key": "dev_key_12345678901234567890CHANGE_IN_PROD"}
        )

        data = response.json()
        assert len(data["tests"]) > 0

        test_result = data["tests"][0]
        assert "name" in test_result
        assert "status" in test_result
        assert test_result["status"] in ["Passed", "Failed"]

    def test_execution_time_is_number(self):
        """Execution time should be a number"""
        code = """
def f():
    pass
"""
        tests = """
def t():
    pass
"""
        response = client.post(
            "/execute",
            json={
                "language": "python",
                "exerciseId": "test_time",
                "code": code,
                "tests": tests
            },
            headers={"X-API-Key": "dev_key_12345678901234567890CHANGE_IN_PROD"}
        )

        data = response.json()
        assert isinstance(data["executionTime"], (int, float))
        assert data["executionTime"] >= 0
        assert data["executionTime"] < 5  # Should be < 5 seconds


class TestResourceCleanup:
    """Test that resources are properly cleaned up"""

    def test_workspace_cleanup_on_success(self):
        """Workspace should be cleaned up after successful execution"""
        code = """
def f():
    pass
"""
        tests = """
def t():
    pass
"""
        response = client.post(
            "/execute",
            json={
                "language": "python",
                "exerciseId": "test_cleanup_success",
                "code": code,
                "tests": tests
            },
            headers={"X-API-Key": "dev_key_12345678901234567890CHANGE_IN_PROD"}
        )

        assert response.status_code == 200

    def test_workspace_cleanup_on_error(self):
        """Workspace should be cleaned up even on error"""
        code = """
import non_existent
"""
        tests = """
def t():
    pass
"""
        response = client.post(
            "/execute",
            json={
                "language": "python",
                "exerciseId": "test_cleanup_error",
                "code": code,
                "tests": tests
            },
            headers={"X-API-Key": "dev_key_12345678901234567890CHANGE_IN_PROD"}
        )

        assert response.status_code == 200


class TestErrorMessages:
    """Test error message quality for novice users"""

    def test_syntax_error_includes_hint(self):
        """Syntax error should include helpful hint"""
        code = """
def greet(name)
    print(f'Hello {name}')
"""
        tests = """
from user_code import greet

def test_greet():
    pass
"""
        response = client.post(
            "/execute",
            json={
                "language": "python",
                "exerciseId": "test_syntax_hint",
                "code": code,
                "tests": tests
            },
            headers={"X-API-Key": "dev_key_12345678901234567890CHANGE_IN_PROD"}
        )

        data = response.json()
        assert data["passed"] == False
        if data["error"]:
            assert data["error"]["type"] == "SyntaxError"
            assert "hint" in data["error"]
            assert data["error"]["hint"] is not None

    def test_import_error_includes_hint(self):
        """Import error should include helpful hint"""
        code = """
def f():
    pass
"""
        tests = """
from missing_module import something

def t():
    pass
"""
        response = client.post(
            "/execute",
            json={
                "language": "python",
                "exerciseId": "test_import_hint",
                "code": code,
                "tests": tests
            },
            headers={"X-API-Key": "dev_key_12345678901234567890CHANGE_IN_PROD"}
        )

        data = response.json()
        assert data["passed"] == False
        if data["error"]:
            assert data["error"]["type"] == "ImportError"
            assert "hint" in data["error"]
            assert "installed" in data["error"]["hint"].lower() or "spelled" in data["error"]["hint"].lower()

    def test_runtime_error_includes_hint(self):
        """Runtime error should include helpful hint"""
        code = """
def divide(a, b):
    return a / b
"""
        tests = """
from user_code import divide

def test_divide():
    divide(10, 0)
"""
        response = client.post(
            "/execute",
            json={
                "language": "python",
                "exerciseId": "test_runtime_hint",
                "code": code,
                "tests": tests
            },
            headers={"X-API-Key": "dev_key_12345678901234567890CHANGE_IN_PROD"}
        )

        data = response.json()
        assert data["passed"] == False
        if data["error"]:
            assert "hint" in data["error"]


if __name__ == "__main__":
    # Run with: pytest tests/test_integration.py -v
    pytest.main([__file__, "-v"])
