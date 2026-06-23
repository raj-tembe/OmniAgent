import os
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class EnvironmentConfigValidator:
    """
    Environment and configuration validation tool.
    
    Responsibilities:
    - Validate .env files
    - Check environment variables
    - Verify configuration files
    - Detect missing required configurations
    """

    # Common required environment variables for web apps
    COMMON_ENV_VARS = {
        "DATABASE_URL": "Database connection string",
        "SECRET_KEY": "Application secret key",
        "API_KEY": "External API key",
        "DEBUG": "Debug mode flag",
        "HOST": "Server host address",
        "PORT": "Server port number",
        "LOG_LEVEL": "Logging level",
    }

    FRAMEWORK_SPECIFIC_VARS = {
        "fastapi": ["API_KEY", "SECRET_KEY", "DATABASE_URL"],
        "flask": ["SECRET_KEY", "DATABASE_URL", "DEBUG"],
        "django": ["SECRET_KEY", "DEBUG", "ALLOWED_HOSTS", "DATABASE_URL"],
    }

    @staticmethod
    def validate_env_file(env_path: str) -> Dict:
        """
        Validate .env file format and content.
        
        Args:
            env_path: Path to .env file
            
        Returns:
            Validation result
        """
        if not os.path.exists(env_path):
            return {
                "valid": False,
                "error": f".env file not found at {env_path}",
                "variables": [],
                "issues": ["Missing .env file"]
            }

        variables = {}
        issues = []

        try:
            with open(env_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    # Parse variable
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip("\"'")

                        # Check for issues
                        if not key:
                            issues.append(f"Line {line_num}: Empty variable name")

                        if not value:
                            issues.append(f"Line {line_num}: Empty value for {key}")

                        # Check for exposed secrets
                        if key in ["SECRET_KEY", "API_KEY", "PASSWORD", "TOKEN"] and value:
                            if value in ["example", "test", "demo", ""]:
                                issues.append(
                                    f"Line {line_num}: {key} contains placeholder value"
                                )

                        variables[key] = value
                    else:
                        issues.append(f"Line {line_num}: Invalid format (missing =)")

        except Exception as e:
            return {
                "valid": False,
                "error": f"Error reading .env file: {str(e)}",
                "variables": {},
                "issues": [str(e)]
            }

        return {
            "valid": len([i for i in issues if "placeholder" not in i]) == 0,
            "variables": variables,
            "issues": issues,
            "variable_count": len(variables)
        }

    @staticmethod
    def validate_requirements_txt(requirements_path: str) -> Dict:
        """
        Validate requirements.txt format and versions.
        
        Args:
            requirements_path: Path to requirements.txt
            
        Returns:
            Validation result
        """
        if not os.path.exists(requirements_path):
            return {
                "valid": False,
                "error": f"requirements.txt not found at {requirements_path}",
                "packages": [],
                "issues": []
            }

        packages = []
        issues = []

        try:
            with open(requirements_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    # Parse package specification
                    package_info = {
                        "raw": line,
                        "line": line_num
                    }

                    # Check format
                    if any(op in line for op in ["==", ">=", "<=", ">", "<", "~="]):
                        # Has version specification
                        match = re.match(r"([a-zA-Z0-9\-_.]+)\s*([>=<~!]+)\s*([0-9.]+)", line)
                        if match:
                            package_info["package"] = match.group(1)
                            package_info["operator"] = match.group(2)
                            package_info["version"] = match.group(3)
                        else:
                            issues.append(f"Line {line_num}: Invalid version specification: {line}")
                    else:
                        # No version
                        match = re.match(r"([a-zA-Z0-9\-_.]+)", line)
                        if match:
                            package_info["package"] = match.group(1)
                            issues.append(
                                f"Line {line_num}: No version pinned for {match.group(1)}"
                            )
                        else:
                            issues.append(f"Line {line_num}: Invalid package name: {line}")

                    packages.append(package_info)

        except Exception as e:
            return {
                "valid": False,
                "error": f"Error reading requirements.txt: {str(e)}",
                "packages": [],
                "issues": [str(e)]
            }

        return {
            "valid": len(issues) == 0,
            "packages": packages,
            "issues": issues,
            "package_count": len(packages)
        }

    @staticmethod
    def check_required_env_vars(
        framework: str,
        provided_vars: Dict[str, str]
    ) -> Dict:
        """
        Check for framework-specific required environment variables.
        
        Args:
            framework: Web framework name (fastapi, flask, django)
            provided_vars: Dictionary of provided environment variables
            
        Returns:
            Validation result
        """
        required = EnvironmentConfigValidator.FRAMEWORK_SPECIFIC_VARS.get(
            framework.lower(),
            []
        )

        missing = []
        found = []

        for var in required:
            if var in provided_vars:
                found.append(var)
            else:
                missing.append(var)

        return {
            "framework": framework,
            "required_vars": required,
            "found_vars": found,
            "missing_vars": missing,
            "complete": len(missing) == 0,
            "missing_count": len(missing)
        }

    @staticmethod
    def validate_config_file(config_path: str, format: str = "python") -> Dict:
        """
        Validate application configuration file.
        
        Args:
            config_path: Path to configuration file
            format: Configuration format (python, json, yaml)
            
        Returns:
            Validation result
        """
        if not os.path.exists(config_path):
            return {
                "valid": False,
                "error": f"Config file not found at {config_path}",
                "config": {}
            }

        try:
            if format == "python":
                # For Python config files, check if they can be parsed
                with open(config_path, 'r') as f:
                    code = f.read()

                import ast
                try:
                    ast.parse(code)
                    return {
                        "valid": True,
                        "format": "python",
                        "path": config_path,
                        "error": None
                    }
                except SyntaxError as e:
                    return {
                        "valid": False,
                        "format": "python",
                        "path": config_path,
                        "error": str(e)
                    }

            elif format == "json":
                import json
                with open(config_path, 'r') as f:
                    json.load(f)

                return {
                    "valid": True,
                    "format": "json",
                    "path": config_path,
                    "error": None
                }

            elif format == "yaml":
                try:
                    import yaml
                    with open(config_path, 'r') as f:
                        yaml.safe_load(f)

                    return {
                        "valid": True,
                        "format": "yaml",
                        "path": config_path,
                        "error": None
                    }
                except ImportError:
                    return {
                        "valid": False,
                        "format": "yaml",
                        "path": config_path,
                        "error": "PyYAML not installed"
                    }

        except Exception as e:
            return {
                "valid": False,
                "format": format,
                "path": config_path,
                "error": str(e)
            }

        return {
            "valid": False,
            "format": format,
            "path": config_path,
            "error": "Unknown format"
        }

    @staticmethod
    def scan_project_configuration(project_dir: str) -> Dict:
        """
        Scan a project directory for configuration files.
        
        Args:
            project_dir: Path to project directory
            
        Returns:
            Configuration files found and their validity
        """
        results = {
            "env_files": {},
            "requirements": {},
            "config_files": {},
            "issues": []
        }

        # Check for .env files
        env_files = [".env", ".env.local", ".env.example"]
        for env_file in env_files:
            env_path = os.path.join(project_dir, env_file)
            if os.path.exists(env_path):
                results["env_files"][env_file] = EnvironmentConfigValidator.validate_env_file(env_path)

        # Check for requirements.txt
        req_path = os.path.join(project_dir, "requirements.txt")
        if os.path.exists(req_path):
            results["requirements"]["requirements.txt"] = EnvironmentConfigValidator.validate_requirements_txt(req_path)

        # Check for config files
        config_candidates = [
            ("config.py", "python"),
            ("config.json", "json"),
            ("config.yaml", "yaml"),
            ("settings.py", "python"),
        ]

        for config_file, format in config_candidates:
            config_path = os.path.join(project_dir, config_file)
            if os.path.exists(config_path):
                results["config_files"][config_file] = EnvironmentConfigValidator.validate_config_file(
                    config_path,
                    format
                )

        return results
