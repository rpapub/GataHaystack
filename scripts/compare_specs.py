#!/usr/bin/env python
"""
Compare official UiPath Swagger (Swagger 2.0) against local FastAPI OpenAPI (3.1)
and emit:
- docs/spec-diff.csv (endpoint inventory with status)
- docs/spec-diff.jsonl (per-operation records)
- docs/spec-summary.json (totals, by-domain)
- docs/spec-patches.json (skeleton patch hints)

Assumptions:
- Official spec at docs/swagger.json (Swagger 2.0)
- Local spec at docs/openapi.yml (JSON text that is valid YAML 1.2)
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple


DOCS = Path("docs")
OFFICIAL_PATH = DOCS / "swagger.json"
LOCAL_PATH = DOCS / "openapi.yml"


@dataclass
class OpRecord:
    domain: str
    resource: str
    action: str
    method: str
    path_official: str
    path_local: Optional[str]
    status: str  # Exact|Minor-diff|Major-diff|Missing|Extra
    param_gaps: List[str]
    body_diff: Optional[str]
    pagination: Optional[str]
    auth: Optional[str]
    headers_needed: List[str]
    error_model: str
    stability: str  # official|unofficial|deprecated
    deprecation: bool
    notes: Optional[str]


def load_official() -> Tuple[Dict, str]:
    with OFFICIAL_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    base = data.get("basePath", "") or ""
    return data, base


def load_local() -> Dict:
    # docs/openapi.yml is JSON text
    with LOCAL_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_official_path(base: str, path: str) -> str:
    # Make a full path, then strip base and common prefixes
    full = f"{base.rstrip('/')}/{path.lstrip('/')}" if base else path
    p = full
    # Strip base path prefix segments common to UiPath Cloud
    # Remove '/.../orchestrator_/' if present
    if "/orchestrator_/" in p:
        p = p.split("/orchestrator_/", 1)[1]
    # Remove leading /api/ or /odata/
    for pref in ("/api/", "/odata/"):
        if p.startswith(pref):
            p = p[len(pref):]
    return p.lstrip("/")


def normalize_local_path(path: str) -> str:
    # Local paths are app-facing. Remove product-specific prefixes to compare at resource level.
    p = path
    # Trim leading slash
    p = p.lstrip("/")
    # Remove our wrapper namespace if present
    for pref in ("uipathcloud/", "oauth2_uipath/"):
        if p.startswith(pref):
            p = p[len(pref):]
    return p


def resource_and_action_from_path(path: str) -> Tuple[str, str]:
    parts = [s for s in path.split("/") if s]
    if not parts:
        return "root", "index"
    resource = parts[0]
    # last fixed segment (ignore path params)
    last = next((seg for seg in reversed(parts) if not seg.startswith("{")), parts[-1])
    return resource, last


def build_index_official(sw: Dict, base: str) -> Dict[Tuple[str, str], Dict]:
    idx: Dict[Tuple[str, str], Dict] = {}
    for raw_path, methods in sw.get("paths", {}).items():
        norm_path = normalize_official_path(base, raw_path)
        for method, op in methods.items():
            method_upper = method.upper()
            if method_upper not in {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}:
                continue
            idx[(method_upper, norm_path)] = op
    return idx


def build_index_local(local: Dict) -> Dict[Tuple[str, str], Dict]:
    idx: Dict[Tuple[str, str], Dict] = {}
    for raw_path, methods in local.get("paths", {}).items():
        norm_path = normalize_local_path(raw_path)
        for method, op in methods.items():
            method_upper = method.upper()
            if method_upper not in {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}:
                continue
            idx[(method_upper, norm_path)] = op
    return idx


def compare(sw: Dict, base: str, local: Dict) -> Tuple[List[OpRecord], Dict]:
    off_idx = build_index_official(sw, base)
    loc_idx = build_index_local(local)

    records: List[OpRecord] = []

    # Map official ops
    for (method, off_norm_path), op in off_idx.items():
        # Try to match: exact normalized path; also try variants replacing 'odata/' and 'api/' differences already handled
        match_path_local = None
        if (method, off_norm_path) in loc_idx:
            match_path_local = off_norm_path
            status = "Exact"
        else:
            status = "Missing"

        tags = op.get("tags", [])
        domain = tags[0] if tags else ""
        resource, action = resource_and_action_from_path(off_norm_path)
        path_official = off_norm_path

        # Determine header needs (heuristic)
        headers_needed: List[str] = []
        params = op.get("parameters", [])
        for p in params:
            if p.get("in") == "header":
                headers_needed.append(p.get("name", ""))

        rec = OpRecord(
            domain=domain,
            resource=resource,
            action=action,
            method=method,
            path_official=path_official,
            path_local=match_path_local,
            status=status,
            param_gaps=[p.get("name", "") for p in params if p.get("required") and p.get("in") != "body"],
            body_diff=None,
            pagination=None,
            auth="OAuth2 bearer",
            headers_needed=headers_needed,
            error_model="unknown",
            stability="official",
            deprecation=bool(op.get("deprecated", False)),
            notes=None,
        )
        records.append(rec)

    # Map local extras (those not in official)
    for (method, loc_norm_path), op in loc_idx.items():
        if (method, loc_norm_path) in off_idx:
            continue
        # Ignore docs, root, favicon
        if loc_norm_path in {"", "favicon.ico"}:
            continue
        domain = ",".join(op.get("tags", [])) if isinstance(op.get("tags"), list) else ""
        resource, action = resource_and_action_from_path(loc_norm_path)
        records.append(
            OpRecord(
                domain=domain,
                resource=resource,
                action=action,
                method=method,
                path_official="",
                path_local=loc_norm_path,
                status="Extra",
                param_gaps=[],
                body_diff=None,
                pagination=None,
                auth=None,
                headers_needed=[],
                error_model="unknown",
                stability="unofficial",
                deprecation=False,
                notes="Local-only endpoint",
            )
        )

    # Summary
    total = len(records)
    exact = sum(1 for r in records if r.status == "Exact")
    missing = sum(1 for r in records if r.status == "Missing")
    extra = sum(1 for r in records if r.status == "Extra")
    by_domain: Dict[str, Dict[str, int]] = {}
    for r in records:
        d = r.domain or "(none)"
        by_domain.setdefault(d, {"official": 0, "implemented": 0, "missing": 0, "extra": 0})
        if r.stability == "official":
            by_domain[d]["official"] += 1
            if r.status == "Missing":
                by_domain[d]["missing"] += 1
            elif r.status == "Exact":
                by_domain[d]["implemented"] += 1
        if r.status == "Extra":
            by_domain[d]["extra"] += 1

    summary = {
        "totals": {"all": total, "exact": exact, "missing": missing, "extra": extra},
        "by_domain": [{"domain": k, **v} for k, v in sorted(by_domain.items())],
        "notes": "This is a surface-level mapping; schema/param diffs are not fully analyzed.",
    }

    return records, summary


def write_outputs(records: List[OpRecord], summary: Dict) -> None:
    DOCS.mkdir(exist_ok=True)

    # CSV
    csv_path = DOCS / "spec-diff.csv"
    columns = [
        "domain",
        "resource",
        "action",
        "method",
        "path_official",
        "path_local",
        "status",
        "param_gaps",
        "body_diff",
        "pagination",
        "auth",
        "headers_needed",
        "error_model",
        "stability",
        "deprecation",
        "notes",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        for r in records:
            row = asdict(r)
            row["param_gaps"] = ";".join(r.param_gaps)
            row["headers_needed"] = ";".join(r.headers_needed)
            w.writerow(row)

    # JSONL
    jsonl_path = DOCS / "spec-diff.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")

    # Summary JSON
    summary_path = DOCS / "spec-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    # Patches JSON (skeletons only)
    patches_path = DOCS / "spec-patches.json"
    patches: List[Dict] = []
    for r in records:
        if r.status == "Missing" and r.stability == "official":
            patches.append(
                {
                    "domain": r.domain,
                    "resource": r.resource,
                    "action": r.action,
                    "method": r.method,
                    "path_official": r.path_official,
                    "patch": {
                        "add_parameters": [
                            {"in": "header", "name": h, "schema": {"type": "string"}}
                            for h in r.headers_needed
                        ],
                        "set_security": [{"bearerAuth": []}],
                        "set_pagination": None,
                    },
                }
            )
    patches_path.write_text(json.dumps(patches, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    if not OFFICIAL_PATH.exists():
        raise SystemExit(f"Official spec not found at {OFFICIAL_PATH}")
    if not LOCAL_PATH.exists():
        raise SystemExit(f"Local OpenAPI not found at {LOCAL_PATH}")

    sw, base = load_official()
    local = load_local()
    records, summary = compare(sw, base, local)
    write_outputs(records, summary)
    print("Wrote: docs/spec-diff.csv, docs/spec-diff.jsonl, docs/spec-summary.json, docs/spec-patches.json")


if __name__ == "__main__":
    main()

