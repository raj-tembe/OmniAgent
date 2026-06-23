import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class FrameworkIssue:
    """Framework validation issue"""
    severity: str  # "error", "warning", "info"
    category: str  # "configuration", "routing", "dependency", etc.
    message: str
    line_hint: Optional[str] = None


class WebFrameworkValidatorTool:
    """
    Web framework-specific validation tool.
    
    Responsibilities:
    - Validate Flask applications
    - Validate FastAPI applications
    - Check routing definitions
    - Verify middleware configuration
    - Check for common framework issues
    """

    # Framework patterns
    FLASK_PATTERNS = {
        "app_initialization": r"from\s+flask\s+import\s+Flask|Flask\s*\(",
        "routes": r"@app\.route\(",
        "blueprints": r"Blueprint\s*\(",
        "error_handlers": r"@app\.errorhandler",
        "before_request": r"@app\.before_request",
        "after_request": r"@app\.after_request",
    }

    FASTAPI_PATTERNS = {
        "app_initialization": r"from\s+fastapi\s+import\s+FastAPI|FastAPI\s*\(",
        "routes": r"@app\.(get|post|put|delete|patch)",
        "dependencies": r"from\s+fastapi\s+import\s+Depends",
        "middleware": r"@app\.middleware",
        "lifespan": r"lifespan\s*=",
    }

    DJANGO_PATTERNS = {
        "models": r"from\s+django\.db\s+import\s+models|class\s+.*\(models\.Model\)",
        "views": r"from\s+django\.views\s+import|def\s+\w+\(request\)",
        "urls": r"from\s+django\.urls\s+import",
        "settings": r"INSTALLED_APPS|DEBUG\s*=",
    }

    @staticmethod
    def detect_framework(code: str) -> Optional[str]:
        """
        Detect which web framework is used.
        
        Args:
            code: Python source code
            
        Returns:
            Framework name or None
        """
        if re.search(WebFrameworkValidatorTool.FASTAPI_PATTERNS["app_initialization"], code):
            return "fastapi"
        elif re.search(WebFrameworkValidatorTool.FLASK_PATTERNS["app_initialization"], code):
            return "flask"
        elif re.search(WebFrameworkValidatorTool.DJANGO_PATTERNS["models"], code):
            return "django"
        return None

    @staticmethod
    def validate_flask_app(code: str) -> Dict:
        """
        Validate Flask application.
        
        Args:
            code: Flask application code
            
        Returns:
            Validation result with issues and recommendations
        """
        issues: List[FrameworkIssue] = []
        features_found = {}

        # Check for Flask initialization
        if not re.search(WebFrameworkValidatorTool.FLASK_PATTERNS["app_initialization"], code):
            issues.append(FrameworkIssue(
                severity="error",
                category="initialization",
                message="Flask app not initialized with Flask() constructor"
            ))

        # Check for routes
        routes = re.findall(r"@app\.route\(['\"]([^'\"]+)['\"]\)", code)
        features_found["routes"] = len(routes)

        if not routes:
            issues.append(FrameworkIssue(
                severity="warning",
                category="routing",
                message="No routes defined in Flask application"
            ))

        # Check for missing app.run()
        if "app.run(" not in code:
            issues.append(FrameworkIssue(
                severity="warning",
                category="execution",
                message="No app.run() call found - application may not start"
            ))

        # Check for debug mode
        if "debug=True" in code:
            issues.append(FrameworkIssue(
                severity="warning",
                category="configuration",
                message="Debug mode enabled - disable in production"
            ))

        # Check for CORS
        has_cors = "CORS" in code or "cors" in code.lower()
        features_found["cors"] = has_cors

        # Check for error handlers
        error_handlers = len(re.findall(r"@app\.errorhandler", code))
        features_found["error_handlers"] = error_handlers

        return {
            "framework": "flask",
            "valid": len([i for i in issues if i.severity == "error"]) == 0,
            "issues": [
                {
                    "severity": issue.severity,
                    "category": issue.category,
                    "message": issue.message
                }
                for issue in issues
            ],
            "features_found": features_found
        }

    @staticmethod
    def validate_fastapi_app(code: str) -> Dict:
        """
        Validate FastAPI application.
        
        Args:
            code: FastAPI application code
            
        Returns:
            Validation result with issues and recommendations
        """
        issues: List[FrameworkIssue] = []
        features_found = {}

        # Check for FastAPI initialization
        if not re.search(WebFrameworkValidatorTool.FASTAPI_PATTERNS["app_initialization"], code):
            issues.append(FrameworkIssue(
                severity="error",
                category="initialization",
                message="FastAPI app not initialized with FastAPI() constructor"
            ))

        # Check for routes
        routes = re.findall(r"@app\.(get|post|put|delete|patch)\(", code)
        features_found["routes"] = len(routes)

        if not routes:
            issues.append(FrameworkIssue(
                severity="warning",
                category="routing",
                message="No routes defined in FastAPI application"
            ))

        # Check for uvicorn
        has_uvicorn = "uvicorn" in code
        features_found["uvicorn"] = has_uvicorn

        # Check for type hints
        type_hint_patterns = [
            r"def\s+\w+\([^)]*:\s*\w+[^)]*\)",  # Function parameters with type hints
            r"->\s*[A-Z]\w+",  # Return type hints
        ]
        has_type_hints = any(re.search(pattern, code) for pattern in type_hint_patterns)
        features_found["type_hints"] = has_type_hints

        # Check for response models
        has_response_models = "response_model=" in code
        features_found["response_models"] = has_response_models

        if not has_response_models:
            issues.append(FrameworkIssue(
                severity="info",
                category="best_practice",
                message="Consider using response_model for better API documentation"
            ))

        # Check for CORS
        has_cors = "CORSMiddleware" in code or "cors" in code.lower()
        features_found["cors"] = has_cors

        # Check for dependency injection
        has_dependencies = "Depends(" in code
        features_found["dependency_injection"] = has_dependencies

        return {
            "framework": "fastapi",
            "valid": len([i for i in issues if i.severity == "error"]) == 0,
            "issues": [
                {
                    "severity": issue.severity,
                    "category": issue.category,
                    "message": issue.message
                }
                for issue in issues
            ],
            "features_found": features_found
        }

    @staticmethod
    def validate_routing(code: str, framework: str) -> Dict:
        """
        Validate route definitions.
        
        Args:
            code: Application code
            framework: Web framework name
            
        Returns:
            Routing validation result
        """
        issues = []
        routes = []

        if framework == "flask":
            # Extract Flask routes
            pattern = r"@app\.route\(['\"]([^'\"]+)['\"]\s*(?:,\s*methods=\[([^\]]+)\])?\)"
            for match in re.finditer(pattern, code):
                path = match.group(1)
                methods = match.group(2)
                if methods:
                    methods = [m.strip().strip("'\"") for m in methods.split(",")]
                else:
                    methods = ["GET"]

                # Check for common issues
                if path.endswith("/"):
                    issues.append(f"Route '{path}' ends with trailing slash")

                if "//" in path:
                    issues.append(f"Route '{path}' has double slashes")

                routes.append({
                    "path": path,
                    "methods": methods
                })

        elif framework == "fastapi":
            # Extract FastAPI routes
            pattern = r"@app\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]\)"
            for match in re.finditer(pattern, code):
                method = match.group(1).upper()
                path = match.group(2)

                # Check for common issues
                if not path.startswith("/"):
                    issues.append(f"Route '{path}' should start with /")

                if path.endswith("/") and path != "/":
                    issues.append(f"Route '{path}' ends with trailing slash")

                routes.append({
                    "path": path,
                    "method": method
                })

        return {
            "framework": framework,
            "routes_found": len(routes),
            "routes": routes,
            "issues": issues,
            "valid": len(issues) == 0
        }

    @staticmethod
    def validate_middleware(code: str, framework: str) -> Dict:
        """
        Validate middleware configuration.
        
        Args:
            code: Application code
            framework: Web framework name
            
        Returns:
            Middleware validation result
        """
        middleware = []
        issues = []

        if framework == "flask":
            # Check for common middleware patterns
            middleware_patterns = {
                "session": r"from\s+flask_session|Session\(",
                "cors": r"from\s+flask_cors|CORS\(",
                "caching": r"from\s+flask_caching|Cache\(",
                "authentication": r"from\s+flask_login|LoginManager",
            }

            for name, pattern in middleware_patterns.items():
                if re.search(pattern, code):
                    middleware.append(name)

        elif framework == "fastapi":
            # Check for FastAPI middleware
            middleware_patterns = {
                "cors": r"CORSMiddleware",
                "gzip": r"GZipMiddleware",
                "trusted_host": r"TrustedHostMiddleware",
                "http_exception": r"HTTPException",
            }

            for name, pattern in middleware_patterns.items():
                if re.search(pattern, code):
                    middleware.append(name)

        return {
            "framework": framework,
            "middleware": middleware,
            "middleware_count": len(middleware),
            "issues": issues,
            "valid": True
        }

    @staticmethod
    def validate_full_app(code: str) -> Dict:
        """
        Perform full validation of a web application.
        
        Args:
            code: Application code
            
        Returns:
            Comprehensive validation result
        """
        framework = WebFrameworkValidatorTool.detect_framework(code)

        if not framework:
            return {
                "valid": False,
                "framework": None,
                "error": "Could not detect web framework",
                "sections": {}
            }

        result = {
            "valid": True,
            "framework": framework,
            "sections": {}
        }

        # Run framework-specific validation
        if framework == "flask":
            result["sections"]["framework"] = WebFrameworkValidatorTool.validate_flask_app(code)
        elif framework == "fastapi":
            result["sections"]["framework"] = WebFrameworkValidatorTool.validate_fastapi_app(code)

        # Validate routing
        result["sections"]["routing"] = WebFrameworkValidatorTool.validate_routing(code, framework)

        # Validate middleware
        result["sections"]["middleware"] = WebFrameworkValidatorTool.validate_middleware(code, framework)

        # Determine overall validity
        errors = []
        for section in result["sections"].values():
            if isinstance(section, dict) and not section.get("valid", True):
                errors.extend(section.get("issues", []))

        result["valid"] = len(errors) == 0
        result["total_issues"] = len(errors)

        return result
