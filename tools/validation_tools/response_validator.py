import json
import re
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass


@dataclass
class APIContractRule:
    """API contract validation rule"""
    field: str
    type: str  # "string", "number", "integer", "boolean", "array", "object"
    required: bool = True
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None  # Regex pattern
    enum: Optional[List[Any]] = None  # Allowed values


class ResponseValidatorTool:
    """
    Response validation tool for HTTP responses.
    
    Responsibilities:
    - Validate response structure
    - Check response types
    - Verify response codes
    - Validate API contracts
    """

    @staticmethod
    def validate_response_structure(
        response_data: Dict,
        schema: Dict
    ) -> Dict:
        """
        Validate response against a schema.
        
        Args:
            response_data: Response data to validate
            schema: JSON schema
            
        Returns:
            Validation result with errors
        """
        errors = []
        warnings = []

        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in response_data:
                errors.append(f"Missing required field: {field}")

        # Check field types
        properties = schema.get("properties", {})
        for field, field_schema in properties.items():
            if field not in response_data:
                continue

            field_value = response_data[field]
            expected_type = field_schema.get("type", "string")

            # Type validation
            type_valid = ResponseValidatorTool._validate_type(
                field_value,
                expected_type
            )

            if not type_valid:
                errors.append(
                    f"Field '{field}' has incorrect type. "
                    f"Expected {expected_type}, got {type(field_value).__name__}"
                )

            # Min/max validation for numbers
            if expected_type in ["number", "integer"]:
                if "minimum" in field_schema:
                    if field_value < field_schema["minimum"]:
                        errors.append(
                            f"Field '{field}' is below minimum: {field_schema['minimum']}"
                        )

                if "maximum" in field_schema:
                    if field_value > field_schema["maximum"]:
                        errors.append(
                            f"Field '{field}' is above maximum: {field_schema['maximum']}"
                        )

            # String length validation
            if expected_type == "string":
                if "minLength" in field_schema:
                    if len(field_value) < field_schema["minLength"]:
                        errors.append(
                            f"Field '{field}' is shorter than minimum: {field_schema['minLength']}"
                        )

                if "maxLength" in field_schema:
                    if len(field_value) > field_schema["maxLength"]:
                        errors.append(
                            f"Field '{field}' is longer than maximum: {field_schema['maxLength']}"
                        )

                # Regex pattern validation
                if "pattern" in field_schema:
                    if not re.match(field_schema["pattern"], field_value):
                        errors.append(
                            f"Field '{field}' does not match pattern: {field_schema['pattern']}"
                        )

            # Enum validation
            if "enum" in field_schema:
                if field_value not in field_schema["enum"]:
                    errors.append(
                        f"Field '{field}' value '{field_value}' not in allowed values: "
                        f"{field_schema['enum']}"
                    )

            # Nested object validation
            if expected_type == "object" and "properties" in field_schema:
                nested_result = ResponseValidatorTool.validate_response_structure(
                    field_value,
                    field_schema
                )
                errors.extend(nested_result["errors"])

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "error_count": len(errors)
        }

    @staticmethod
    def _validate_type(value: Any, expected_type: str) -> bool:
        """
        Validate value type.
        
        Args:
            value: Value to validate
            expected_type: Expected type name
            
        Returns:
            True if type matches
        """
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None)
        }

        if expected_type not in type_map:
            return True

        expected = type_map[expected_type]
        return isinstance(value, expected)

    @staticmethod
    def validate_api_contract(
        response_data: Dict,
        contract_rules: List[APIContractRule]
    ) -> Dict:
        """
        Validate response against API contract rules.
        
        Args:
            response_data: Response data
            contract_rules: List of contract rules
            
        Returns:
            Validation result
        """
        violations = []

        for rule in contract_rules:
            if rule.field not in response_data:
                if rule.required:
                    violations.append({
                        "field": rule.field,
                        "violation": "Missing required field",
                        "severity": "error"
                    })
                continue

            value = response_data[rule.field]

            # Type check
            if not ResponseValidatorTool._validate_type(value, rule.type):
                violations.append({
                    "field": rule.field,
                    "violation": f"Type mismatch: expected {rule.type}, got {type(value).__name__}",
                    "severity": "error"
                })
                continue

            # Value range checks
            if rule.min_value is not None and isinstance(value, (int, float)):
                if value < rule.min_value:
                    violations.append({
                        "field": rule.field,
                        "violation": f"Value below minimum: {rule.min_value}",
                        "severity": "error"
                    })

            if rule.max_value is not None and isinstance(value, (int, float)):
                if value > rule.max_value:
                    violations.append({
                        "field": rule.field,
                        "violation": f"Value above maximum: {rule.max_value}",
                        "severity": "error"
                    })

            # String length checks
            if rule.min_length is not None and isinstance(value, str):
                if len(value) < rule.min_length:
                    violations.append({
                        "field": rule.field,
                        "violation": f"String shorter than minimum: {rule.min_length}",
                        "severity": "error"
                    })

            if rule.max_length is not None and isinstance(value, str):
                if len(value) > rule.max_length:
                    violations.append({
                        "field": rule.field,
                        "violation": f"String longer than maximum: {rule.max_length}",
                        "severity": "error"
                    })

            # Pattern matching
            if rule.pattern and isinstance(value, str):
                if not re.match(rule.pattern, value):
                    violations.append({
                        "field": rule.field,
                        "violation": f"Value does not match pattern: {rule.pattern}",
                        "severity": "error"
                    })

            # Enum validation
            if rule.enum and value not in rule.enum:
                violations.append({
                    "field": rule.field,
                    "violation": f"Value not in allowed list: {rule.enum}",
                    "severity": "error"
                })

        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "violation_count": len(violations)
        }

    @staticmethod
    def extract_json_schema_from_response(
        response_data: Union[Dict, List]
    ) -> Dict:
        """
        Extract JSON schema from response data.
        
        Args:
            response_data: Response data
            
        Returns:
            Inferred JSON schema
        """
        if isinstance(response_data, dict):
            properties = {}
            required = []

            for key, value in response_data.items():
                prop_type = ResponseValidatorTool._infer_type(value)
                properties[key] = {"type": prop_type}

                # All top-level keys are considered required
                required.append(key)

            return {
                "type": "object",
                "properties": properties,
                "required": required
            }

        elif isinstance(response_data, list):
            if not response_data:
                return {"type": "array", "items": {}}

            # Infer from first element
            first_type = ResponseValidatorTool._infer_type(response_data[0])
            return {
                "type": "array",
                "items": {"type": first_type}
            }

        else:
            return {"type": ResponseValidatorTool._infer_type(response_data)}

    @staticmethod
    def _infer_type(value: Any) -> str:
        """
        Infer JSON schema type from Python value.
        
        Args:
            value: Value to analyze
            
        Returns:
            JSON schema type
        """
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        elif value is None:
            return "null"
        else:
            return "string"

    @staticmethod
    def compare_responses(
        response1: Dict,
        response2: Dict
    ) -> Dict:
        """
        Compare two responses for structural differences.
        
        Args:
            response1: First response
            response2: Second response
            
        Returns:
            Comparison result with differences
        """
        differences = []

        # Check for missing keys in response2
        for key in response1.keys():
            if key not in response2:
                differences.append(f"Missing key in second response: {key}")

        # Check for extra keys in response2
        for key in response2.keys():
            if key not in response1:
                differences.append(f"Extra key in second response: {key}")

        # Check for value differences
        for key in set(response1.keys()) & set(response2.keys()):
            if response1[key] != response2[key]:
                differences.append(
                    f"Value difference for key '{key}': "
                    f"{response1[key]} vs {response2[key]}"
                )

        return {
            "identical": len(differences) == 0,
            "differences": differences,
            "difference_count": len(differences)
        }

    @staticmethod
    def validate_error_response(error_response: Dict) -> Dict:
        """
        Validate error response structure.
        
        Args:
            error_response: Error response data
            
        Returns:
            Validation result
        """
        issues = []
        warnings = []

        # Check for error code
        if "error_code" not in error_response and "code" not in error_response:
            issues.append("Error code not present in response")

        # Check for error message
        if "error_message" not in error_response and "message" not in error_response:
            issues.append("Error message not present in response")

        # Check for error details
        if "error_details" not in error_response and "details" not in error_response:
            warnings.append("Consider including error details in error response")

        # Check for HTTP status code consistency
        if "status" in error_response:
            status = error_response["status"]
            if not (400 <= status <= 599):
                issues.append(f"Invalid HTTP status code: {status}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }
