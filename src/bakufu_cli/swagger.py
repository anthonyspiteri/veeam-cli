import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, List, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEGACY_SWAGGER_PATH = PROJECT_ROOT / "swagger_v1.3.json"
SCHEMAS_DIR = PROJECT_ROOT / "schemas"


def _resolve_swagger_path() -> Path:
    override = os.getenv("BAKUFU_SWAGGER_PATH")
    if override:
        return Path(override).expanduser()
    candidates = sorted(
        SCHEMAS_DIR.glob("swagger*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if candidates:
        return candidates[0]
    return LEGACY_SWAGGER_PATH


SWAGGER_PATH = _resolve_swagger_path()


@dataclass
class Operation:
    operation_id: str
    method: str
    path: str
    summary: str
    description: str
    tags: List[str]
    parameters: List[Dict]
    request_body: Optional[dict]
    responses: Optional[dict]


class SwaggerSpec:
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.paths = data.get("paths", {})
        self.tags = data.get("tags", [])

    @classmethod
    def load(cls, path: Path = SWAGGER_PATH) -> "SwaggerSpec":
        if not path.exists():
            raise FileNotFoundError(f"Swagger spec not found at {path}")
        data = json.loads(path.read_text())
        return cls(data)

    @staticmethod
    def _is_api_tag(tag_name: Optional[str]) -> bool:
        if not tag_name:
            return False
        return not tag_name.startswith("Section")

    def list_tags(self) -> List[str]:
        tag_names = [tag.get("name") for tag in self.tags if isinstance(tag, dict)]
        return sorted([t for t in tag_names if self._is_api_tag(t)])

    def iter_operations(self) -> List[Operation]:
        ops: List[Operation] = []
        for path, methods in self.paths.items():
            if not isinstance(methods, dict):
                continue
            for method, details in methods.items():
                if method.lower() not in {"get", "post", "put", "delete", "patch"}:
                    continue
                if not isinstance(details, dict):
                    continue
                operation_id = details.get("operationId") or f"{method}_{path}"
                ops.append(
                    Operation(
                        operation_id=operation_id,
                        method=method.upper(),
                        path=path,
                        summary=details.get("summary", ""),
                        description=details.get("description", ""),
                        tags=details.get("tags", []) or [],
                        parameters=details.get("parameters", []) or [],
                        request_body=details.get("requestBody"),
                        responses=details.get("responses"),
                    )
                )
        return ops

    def operations_by_tag(self) -> Dict[str, List[Operation]]:
        grouped: Dict[str, List[Operation]] = {}
        for op in self.iter_operations():
            if not op.tags:
                grouped.setdefault("untagged", []).append(op)
            else:
                for tag in op.tags:
                    if not self._is_api_tag(tag):
                        continue
                    grouped.setdefault(tag, []).append(op)
        return grouped

    def find_operation(self, tag: str, operation_id: str) -> Optional[Operation]:
        for op in self.operations_by_tag().get(tag, []):
            if op.operation_id == operation_id:
                return op
        return None

    def find_operation_by_id(self, operation_id: str) -> Optional[Operation]:
        for op in self.iter_operations():
            if op.operation_id == operation_id:
                return op
        return None

    def schemas(self) -> Dict[str, Any]:
        return self.data.get("components", {}).get("schemas", {})
