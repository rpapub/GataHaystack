#!/usr/bin/env python
"""
Merge official Swagger 2.0 (docs/swagger.json) with local OAS3 (docs/openapi.yml)
into a single OAS3 spec, applying normalization and annotations.

Outputs: docs/openapi-merged.yml (JSON text valid as YAML 1.2)
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any, Dict, Tuple

DOCS = Path("docs")
OFFICIAL = DOCS / "swagger.json"
LOCAL = DOCS / "openapi.yml"
OUT = DOCS / "openapi-merged.yml"


def deep_replace_refs(obj: Any) -> Any:
    # Recursively replace Swagger $ref prefixes to OAS3 components.*
    if isinstance(obj, dict):
        new = {}
        for k, v in obj.items():
            if k == "$ref" and isinstance(v, str):
                if v.startswith("#/definitions/"):
                    v = v.replace("#/definitions/", "#/components/schemas/")
                elif v.startswith("#/parameters/"):
                    v = v.replace("#/parameters/", "#/components/parameters/")
                elif v.startswith("#/responses/"):
                    v = v.replace("#/responses/", "#/components/responses/")
                elif v.startswith("#/securityDefinitions/"):
                    v = v.replace("#/securityDefinitions/", "#/components/securitySchemes/")
                new[k] = v
            else:
                new[k] = deep_replace_refs(v)
        return new
    elif isinstance(obj, list):
        return [deep_replace_refs(x) for x in obj]
    else:
        return obj


def to_oas3_from_swagger(sw: Dict[str, Any]) -> Dict[str, Any]:
    oas: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": sw.get("info", {}),
        "servers": [
            {
                "url": "https://cloud.uipath.com/{account}/{tenant}/orchestrator_/",
                "variables": {
                    "account": {"default": "<account>"},
                    "tenant": {"default": "<tenant>"},
                },
            }
        ],
        "paths": {},
        "components": {
            "schemas": {},
            "parameters": {},
            "responses": {},
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
                "oauth2": {
                    "type": "oauth2",
                    "flows": {
                        "authorizationCode": {
                            "authorizationUrl": "https://cloud.uipath.com/identity_/connect/authorize",
                            "tokenUrl": "https://cloud.uipath.com/identity_/connect/token",
                            "scopes": {},
                        },
                        "clientCredentials": {
                            "tokenUrl": "https://cloud.uipath.com/identity_/connect/token",
                            "scopes": {},
                        },
                    },
                },
            },
        },
    }

    # Move definitions/parameters/responses
    if "definitions" in sw:
        oas["components"]["schemas"] = sw["definitions"]
    if "parameters" in sw:
        oas["components"]["parameters"] = sw["parameters"]
    if "responses" in sw:
        oas["components"]["responses"] = sw["responses"]
    if "securityDefinitions" in sw:
        # Not used directly; we standardize to bearer/oauth2 above.
        pass

    oas = deep_replace_refs(oas)

    # Build Error response schema
    oas.setdefault("components", {}).setdefault("schemas", {})["Error"] = {
        "type": "object",
        "required": ["code", "message"],
        "properties": {
            "code": {"type": "string"},
            "message": {"type": "string"},
            "details": {"type": "array", "items": {"type": "string"}},
            "correlationId": {"type": "string"},
        },
    }
    oas["components"]["responses"]["Error"] = {
        "description": "Error response",
        "headers": {"X-Correlation-Id": {"schema": {"type": "string"}}},
        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}},
    }
    # Shared parameters (pagination, folder)
    oas["components"]["parameters"].update(
        {
            "folderIdHeader": {
                "name": "X-UIPATH-OrganizationUnitId",
                "in": "header",
                "required": False,
                "schema": {"type": "integer", "format": "int64"},
                "description": "Folder context (Organization Unit Id)",
            },
            "take": {"name": "take", "in": "query", "schema": {"type": "integer", "format": "int32"}},
            "skip": {"name": "skip", "in": "query", "schema": {"type": "integer", "format": "int32"}},
            "top": {"name": "$top", "in": "query", "schema": {"type": "integer", "format": "int32"}},
            "odata_skip": {"name": "$skip", "in": "query", "schema": {"type": "integer", "format": "int32"}},
        }
    )

    # Transform paths
    for path, methods in sw.get("paths", {}).items():
        oitem: Dict[str, Any] = {}
        # Carry over and convert path-level parameters if present
        path_level_params = []
        if isinstance(methods.get("parameters"), list):
            for p in methods.get("parameters", []):
                path_level_params.append(convert_param_to_oas3(p))
        for method, op in methods.items():
            if method.lower() not in {"get", "post", "put", "delete", "patch", "options", "head"}:
                continue
            op3 = copy.deepcopy(op)
            # Drop swagger-specific keys
            op3.pop("consumes", None)
            op3.pop("produces", None)
            # Request body: move body parameter to requestBody
            params = op3.get("parameters", []) + path_level_params
            body_schema = None
            new_params = []
            for p in params:
                if p.get("in") == "body":
                    body_schema = p.get("schema")
                else:
                    new_params.append(convert_param_to_oas3(p))
            op3["parameters"] = new_params
            if body_schema is not None:
                op3["requestBody"] = {
                    "content": {"application/json": {"schema": body_schema}},
                    "required": True,
                }
            # Responses: move schema under content
            responses = op3.get("responses", {})
            for code, r in list(responses.items()):
                if not isinstance(r, dict):
                    continue
                schema = r.pop("schema", None)
                if schema is not None:
                    r.setdefault("content", {}).setdefault("application/json", {})["schema"] = schema
            # Ensure default error
            op3.setdefault("responses", {}).setdefault("default", {"$ref": "#/components/responses/Error"})
            # Security
            op3["security"] = [{"bearerAuth": []}]
            # operationId normalization
            op3["operationId"] = canonical_operation_id(path, op3)
            # annotations
            op3["x-source"] = "official"
            if op3.get("deprecated"):
                op3["x-stability"] = "deprecated"
            else:
                op3["x-stability"] = "stable"
            oitem[method.lower()] = op3
        oas["paths"][path] = oitem

    # Replace refs in paths too
    oas["paths"] = deep_replace_refs(oas["paths"])
    return oas


def convert_param_to_oas3(p: Dict[str, Any]) -> Dict[str, Any]:
    p = copy.deepcopy(p)
    if "schema" not in p and p.get("in") != "body":
        schema: Dict[str, Any] = {}
        if "type" in p:
            schema["type"] = p.pop("type")
        if "format" in p:
            schema["format"] = p.pop("format")
        if "items" in p:
            schema["items"] = p.pop("items")
        if schema:
            p["schema"] = schema
        # Remove Swagger-only fields
        p.pop("collectionFormat", None)
    return p


def canonical_operation_id(path: str, op: Dict[str, Any]) -> str:
    # Build noun_action from path and hints
    segs = [s for s in path.split("/") if s]
    noun = (segs[1] if segs and segs[0] in {"api", "odata"} and len(segs) > 1 else (segs[0] if segs else "root"))
    # Determine action
    summary = (op.get("summary") or op.get("operationId") or "").lower()
    action = "list"
    if any(x in summary for x in ("get by", "retrieve", "getone", "getby")) or re.search(r"\{.*\}", path):
        action = "get"
    elif "create" in summary or op.get("requestBody"):
        action = "create"
    elif "update" in summary:
        action = "update"
    elif "delete" in summary or op.get("operationId", "").lower().startswith("delete"):
        action = "delete"
    return f"{to_snake(noun)}_{action}"


def to_snake(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    return s.strip("_").lower()


def merge_local(oas: Dict[str, Any], local: Dict[str, Any]) -> Dict[str, Any]:
    # Add local paths that are not present; annotate.
    for path, methods in local.get("paths", {}).items():
        if path not in oas["paths"]:
            oas["paths"][path] = {}
        for method, op in methods.items():
            if method.lower() not in {"get", "post", "put", "delete", "patch", "options", "head"}:
                continue
            if method.lower() in oas["paths"][path]:
                # Annotate official op to indicate also present in local
                oas["paths"][path][method.lower()]["x-alsoPresentIn"] = [
                    *set(oas["paths"][path][method.lower()].get("x-alsoPresentIn", [])),
                    "local",
                ]
                continue
            op3 = copy.deepcopy(op)
            # Ensure responses have default error
            op3.setdefault("responses", {}).setdefault("default", {"$ref": "#/components/responses/Error"})
            # Ensure security
            op3["security"] = [{"bearerAuth": []}]
            # operationId present or generate
            op3.setdefault("operationId", canonical_operation_id(path, op3))
            # annotations
            op3["x-source"] = "local"
            # Stability heuristic
            tags = op3.get("tags", []) or []
            if any(t for t in tags if "beta" in t.lower() or "alpha" in t.lower() or "debug" in t.lower()):
                op3["x-stability"] = "beta"
            else:
                op3["x-stability"] = "experimental"
            op3["x-unofficial"] = True
            oas["paths"][path][method.lower()] = op3

    return oas


def main() -> None:
    if not OFFICIAL.exists():
        raise SystemExit(f"Missing {OFFICIAL}")
    if not LOCAL.exists():
        raise SystemExit(f"Missing {LOCAL}")

    sw = json.loads(OFFICIAL.read_text(encoding="utf-8"))
    local = json.loads(LOCAL.read_text(encoding="utf-8"))

    oas = to_oas3_from_swagger(sw)
    oas = merge_local(oas, local)

    # Set top-level default security
    oas["security"] = [{"bearerAuth": []}]

    OUT.write_text(json.dumps(oas, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
