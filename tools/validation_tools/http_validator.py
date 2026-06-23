import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re


@dataclass
class HTTPEndpoint:
    """HTTP endpoint definition"""
    path: str
    method: str = "GET"
    expected_status: int = 200
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None
    timeout: int = 5


class HTTPValidatorTool:
    """
    HTTP endpoint validation tool for web applications.
    
    Responsibilities:
    - Validate endpoint responses
    - Check HTTP status codes
    - Verify response structure
    - Test endpoint connectivity
    """

    @staticmethod
    def validate_endpoint(
        base_url: str,
        endpoint: HTTPEndpoint,
        response_schema: Optional[Dict] = None
    ) -> Dict:
        """
        Validate a single HTTP endpoint.
        
        Args:
            base_url: Base URL of the application (e.g., http://localhost:8000)
            endpoint: HTTPEndpoint definition
            response_schema: Optional JSON schema to validate response
            
        Returns:
            Validation result with status, response, and errors
        """
        try:
            import requests
        except ImportError:
            return {
                "success": False,
                "endpoint": endpoint.path,
                "error": "requests library not installed",
                "status_code": None,
                "response": None
            }

        url = f"{base_url}{endpoint.path}"
        
        try:
            if endpoint.method.upper() == "GET":
                response = requests.get(
                    url,
                    headers=endpoint.headers,
                    timeout=endpoint.timeout
                )
            elif endpoint.method.upper() == "POST":
                response = requests.post(
                    url,
                    json=endpoint.body,
                    headers=endpoint.headers,
                    timeout=endpoint.timeout
                )
            elif endpoint.method.upper() == "PUT":
                response = requests.put(
                    url,
                    json=endpoint.body,
                    headers=endpoint.headers,
                    timeout=endpoint.timeout
                )
            elif endpoint.method.upper() == "DELETE":
                response = requests.delete(
                    url,
                    headers=endpoint.headers,
                    timeout=endpoint.timeout
                )
            else:
                return {
                    "success": False,
                    "endpoint": endpoint.path,
                    "error": f"Unsupported HTTP method: {endpoint.method}",
                    "status_code": None
                }

            # Check status code
            status_match = response.status_code == endpoint.expected_status
            
            # Parse response
            try:
                response_data = response.json()
            except (json.JSONDecodeError, ValueError):
                response_data = response.text

            result = {
                "success": status_match,
                "endpoint": endpoint.path,
                "method": endpoint.method,
                "status_code": response.status_code,
                "expected_status": endpoint.expected_status,
                "response": response_data if isinstance(response_data, (dict, list)) else str(response_data)[:500]
            }

            # Validate response schema if provided
            if response_schema and isinstance(response_data, dict):
                schema_valid = HTTPValidatorTool._validate_schema(
                    response_data,
                    response_schema
                )
                result["schema_valid"] = schema_valid

            return result

        except asyncio.TimeoutError:
            return {
                "success": False,
                "endpoint": endpoint.path,
                "method": endpoint.method,
                "error": f"Request timeout after {endpoint.timeout}s",
                "status_code": None
            }
        except ConnectionError as e:
            return {
                "success": False,
                "endpoint": endpoint.path,
                "method": endpoint.method,
                "error": f"Connection error: {str(e)}",
                "status_code": None
            }
        except Exception as e:
            return {
                "success": False,
                "endpoint": endpoint.path,
                "method": endpoint.method,
                "error": f"Unexpected error: {str(e)}",
                "status_code": None
            }

    @staticmethod
    def _validate_schema(data: Dict, schema: Dict) -> bool:
        """
        Simple JSON schema validation.
        
        Args:
            data: Data to validate
            schema: JSON schema
            
        Returns:
            True if data matches schema
        """
        if "properties" not in schema:
            return True

        properties = schema["properties"]
        required = schema.get("required", [])

        # Check required fields
        for field in required:
            if field not in data:
                return False

        # Check field types (basic validation)
        for field, field_schema in properties.items():
            if field not in data:
                continue

            expected_type = field_schema.get("type", "string")
            actual_value = data[field]

            type_map = {
                "string": str,
                "number": (int, float),
                "integer": int,
                "boolean": bool,
                "array": list,
                "object": dict
            }

            if expected_type in type_map:
                if not isinstance(actual_value, type_map[expected_type]):
                    return False

        return True

    @staticmethod
    def validate_endpoints(
        base_url: str,
        endpoints: List[HTTPEndpoint],
        stop_on_failure: bool = False
    ) -> Dict:
        """
        Validate multiple endpoints.
        
        Args:
            base_url: Base URL of the application
            endpoints: List of endpoints to validate
            stop_on_failure: Stop validation on first failure
            
        Returns:
            Summary of validation results
        """
        results = []
        passed = 0
        failed = 0

        for endpoint in endpoints:
            result = HTTPValidatorTool.validate_endpoint(base_url, endpoint)
            results.append(result)

            if result["success"]:
                passed += 1
            else:
                failed += 1
                if stop_on_failure:
                    break

        return {
            "success": failed == 0,
            "passed": passed,
            "failed": failed,
            "total": len(endpoints),
            "results": results
        }

    @staticmethod
    def extract_endpoints_from_code(code: str) -> List[Dict]:
        """
        Extract HTTP endpoints from Flask/FastAPI code.
        
        Args:
            code: Python source code
            
        Returns:
            List of extracted endpoints
        """
        endpoints = []

        # Flask routes
        flask_pattern = r"@app\.route\(['\"]([^'\"]+)['\"]\s*(?:,\s*methods=\[([^\]]+)\])?\)"
        for match in re.finditer(flask_pattern, code):
            path = match.group(1)
            methods = match.group(2)
            if methods:
                methods = [m.strip().strip("'\"") for m in methods.split(",")]
            else:
                methods = ["GET"]

            for method in methods:
                endpoints.append({
                    "path": path,
                    "method": method,
                    "framework": "flask"
                })

        # FastAPI routes
        fastapi_patterns = [
            (r"@app\.get\(['\"]([^'\"]+)['\"]\)", "GET"),
            (r"@app\.post\(['\"]([^'\"]+)['\"]\)", "POST"),
            (r"@app\.put\(['\"]([^'\"]+)['\"]\)", "PUT"),
            (r"@app\.delete\(['\"]([^'\"]+)['\"]\)", "DELETE"),
        ]

        for pattern, method in fastapi_patterns:
            for match in re.finditer(pattern, code):
                path = match.group(1)
                endpoints.append({
                    "path": path,
                    "method": method,
                    "framework": "fastapi"
                })

        return endpoints

    @staticmethod
    def check_port_available(port: int, host: str = "localhost") -> bool:
        """
        Check if a port is available.
        
        Args:
            port: Port number to check
            host: Host address
            
        Returns:
            True if port is available
        """
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))
        sock.close()
        return result != 0

    @staticmethod
    def wait_for_server(
        base_url: str,
        max_retries: int = 10,
        retry_delay: float = 0.5
    ) -> bool:
        """
        Wait for server to become available.
        
        Args:
            base_url: Base URL of the server
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            True if server becomes available
        """
        try:
            import requests
        except ImportError:
            return False

        for attempt in range(max_retries):
            try:
                response = requests.get(base_url, timeout=2)
                if response.status_code < 500:
                    return True
            except (ConnectionError, Exception):
                pass

            if attempt < max_retries - 1:
                time.sleep(retry_delay)

        return False
