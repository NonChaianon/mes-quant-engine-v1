from __future__ import annotations

import json
import re
from typing import Any


class RecordValidationError(RuntimeError):
    """Raised when CLASSIFICATION_RECORD_V1 fails the frozen schema subset."""


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _resolve_ref(root_schema: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise RecordValidationError(f"unsupported schema ref: {ref}")
    node: Any = root_schema
    for token in ref[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or token not in node:
            raise RecordValidationError(f"unresolvable schema ref: {ref}")
        node = node[token]
    if not isinstance(node, dict):
        raise RecordValidationError(f"schema ref is not an object: {ref}")
    return node


def _matches(instance: Any, schema: dict[str, Any], root: dict[str, Any], path: str) -> bool:
    try:
        _validate(instance, schema, root, path)
        return True
    except RecordValidationError:
        return False


def _validate_object(
    instance: Any,
    schema: dict[str, Any],
    root: dict[str, Any],
    path: str,
) -> None:
    if not isinstance(instance, dict):
        raise RecordValidationError(f"{path}: expected object")

    required = schema.get("required", [])
    missing = [key for key in required if key not in instance]
    if missing:
        raise RecordValidationError(f"{path}: missing required fields {missing}")

    properties = schema.get("properties", {})
    if schema.get("additionalProperties") is False:
        unknown = sorted(set(instance) - set(properties))
        if unknown:
            raise RecordValidationError(f"{path}: unknown fields {unknown}")

    property_names = schema.get("propertyNames", {})
    forbidden = property_names.get("not", {}).get("enum", [])
    bad_names = sorted(set(instance) & set(forbidden))
    if bad_names:
        raise RecordValidationError(f"{path}: forbidden executable-control fields {bad_names}")

    for key, value in instance.items():
        child_schema = properties.get(key)
        if child_schema is not None:
            _validate(value, child_schema, root, f"{path}.{key}")


def _validate_array(instance: Any, schema: dict[str, Any], root: dict[str, Any], path: str) -> None:
    if not isinstance(instance, list):
        raise RecordValidationError(f"{path}: expected array")

    if "minItems" in schema and len(instance) < schema["minItems"]:
        raise RecordValidationError(f"{path}: too few array items")
    if "maxItems" in schema and len(instance) > schema["maxItems"]:
        raise RecordValidationError(f"{path}: too many array items")

    if schema.get("uniqueItems"):
        canonical_items = [
            json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
            for value in instance
        ]
        if len(set(canonical_items)) != len(canonical_items):
            raise RecordValidationError(f"{path}: array items must be unique")

    if "items" in schema:
        for index, value in enumerate(instance):
            _validate(value, schema["items"], root, f"{path}[{index}]")

    if "contains" in schema:
        if not any(
            _matches(value, schema["contains"], root, f"{path}[{index}]")
            for index, value in enumerate(instance)
        ):
            raise RecordValidationError(f"{path}: contains constraint not satisfied")


def _validate(instance: Any, schema: dict[str, Any], root: dict[str, Any], path: str) -> None:
    if "$ref" in schema:
        _validate(instance, _resolve_ref(root, schema["$ref"]), root, path)
        return

    for branch in schema.get("allOf", []):
        if "if" in branch:
            if _matches(instance, branch["if"], root, path) and "then" in branch:
                _validate(instance, branch["then"], root, path)
        else:
            _validate(instance, branch, root, path)

    if "anyOf" in schema:
        if not any(_matches(instance, option, root, path) for option in schema["anyOf"]):
            raise RecordValidationError(f"{path}: no anyOf branch matched")
        return

    if "const" in schema and instance != schema["const"]:
        raise RecordValidationError(f"{path}: const mismatch")
    if "enum" in schema and instance not in schema["enum"]:
        raise RecordValidationError(f"{path}: value outside frozen enum")

    expected_type = schema.get("type")
    object_keywords = {"properties", "required", "additionalProperties", "propertyNames"}
    array_keywords = {"items", "minItems", "maxItems", "uniqueItems", "contains"}

    if expected_type == "object" or any(key in schema for key in object_keywords):
        _validate_object(instance, schema, root, path)
        return

    if expected_type == "array" or any(key in schema for key in array_keywords):
        _validate_array(instance, schema, root, path)
        return

    if expected_type == "string":
        if not isinstance(instance, str):
            raise RecordValidationError(f"{path}: expected string")
        if "minLength" in schema and len(instance) < schema["minLength"]:
            raise RecordValidationError(f"{path}: string shorter than minLength")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            raise RecordValidationError(f"{path}: string longer than maxLength")
        if "pattern" in schema and re.fullmatch(schema["pattern"], instance) is None:
            raise RecordValidationError(f"{path}: string does not match frozen pattern")
        return

    if expected_type == "integer":
        if not _is_integer(instance):
            raise RecordValidationError(f"{path}: expected integer")
        if "minimum" in schema and instance < schema["minimum"]:
            raise RecordValidationError(f"{path}: integer below minimum")
        if "maximum" in schema and instance > schema["maximum"]:
            raise RecordValidationError(f"{path}: integer above maximum")
        return

    if expected_type == "boolean":
        if not isinstance(instance, bool):
            raise RecordValidationError(f"{path}: expected boolean")
        return

    if expected_type == "null":
        if instance is not None:
            raise RecordValidationError(f"{path}: expected null")
        return


def validate_record(record: dict[str, Any], schema: dict[str, Any]) -> None:
    _validate(record, schema, schema, "$")


def canonical_record_bytes(
    record: dict[str, Any],
    *,
    schema: dict[str, Any],
    max_record_bytes: int,
) -> bytes:
    validate_record(record, schema)
    try:
        encoded = (
            json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise RecordValidationError("record is not canonical-JSON serializable") from exc
    if len(encoded) > max_record_bytes:
        raise RecordValidationError(
            f"record exceeds max_record_bytes: {len(encoded)} > {max_record_bytes}"
        )
    return encoded
