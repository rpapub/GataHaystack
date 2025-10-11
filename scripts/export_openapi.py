#!/usr/bin/env python
"""
Export OpenAPI schema from the FastAPI app.

- Writes JSON schema
- Writes YAML schema (JSON content; YAML 1.2 is a superset of JSON)

Note: We avoid adding dependencies. YAML output is JSON text which is valid YAML 1.2.
"""
import json
import sys
from pathlib import Path

from fastapi.openapi.utils import get_openapi

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    # Import the FastAPI app
    from uipathcloud.main import app
except Exception as e:
    raise SystemExit(f"Failed to import app: {e}")


def main() -> None:
    schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )

    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)

    # Write JSON (not committed by default)
    json_path = docs_dir / "openapi.json"
    json_text = json.dumps(schema, indent=2, ensure_ascii=False)
    json_path.write_text(json_text, encoding="utf-8")

    # Write YAML: JSON text is valid YAML 1.2
    yaml_path = docs_dir / "openapi.yml"
    yaml_path.write_text(json_text, encoding="utf-8")

    print(f"Wrote {json_path} and {yaml_path}")


if __name__ == "__main__":
    main()
