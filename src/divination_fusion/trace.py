from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from uuid import uuid4

from .models import TraceMetadata, TraceStep, now_iso, to_dict


class TraceRecorder:
    def __init__(self, root: Path, metadata: TraceMetadata) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.metadata = metadata

    @classmethod
    def create(cls, root: Path) -> "TraceRecorder":
        run_id = uuid4().hex[:12]
        metadata = TraceMetadata(
            run_id=run_id,
            created_at=now_iso(),
            input_version="v1",
            prompt_versions={},
            rule_versions={},
            model_versions={},
        )
        return cls(root / run_id, metadata)

    def record(
        self,
        step: str,
        payload_in: object,
        payload_out: object,
        *,
        prompt_version: str,
        model_version: str,
        rule_version: str,
        metadata: Optional[dict[str, object]] = None,
    ) -> None:
        step_name = step.strip()
        if not step_name:
            raise ValueError("step must be a non-empty string")
        if any(existing.step == step_name for existing in self.metadata.steps):
            raise ValueError(f"trace step already recorded: {step_name}")
        if not prompt_version.strip():
            raise ValueError("prompt_version must be a non-empty string")
        if not model_version.strip():
            raise ValueError("model_version must be a non-empty string")
        if not rule_version.strip():
            raise ValueError("rule_version must be a non-empty string")

        input_ref = f"{step_name}.input.json"
        output_ref = f"{step_name}.output.json"
        self._write_json(input_ref, payload_in)
        self._write_json(output_ref, payload_out)
        self.metadata.prompt_versions[step_name] = prompt_version
        self.metadata.model_versions[step_name] = model_version
        self.metadata.rule_versions[step_name] = rule_version
        self.metadata.steps.append(
            TraceStep(
                step=step_name,
                timestamp=now_iso(),
                input_ref=input_ref,
                output_ref=output_ref,
                prompt_version=prompt_version,
                model_version=model_version,
                rule_version=rule_version,
                metadata=metadata or {},
            )
        )
        self._write_json("trace_metadata.json", self.metadata)

    def _write_json(self, name: str, payload: object) -> None:
        path = self.root / name
        temp_path = path.with_suffix(f"{path.suffix}.tmp")
        temp_path.write_text(
            json.dumps(to_dict(payload), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temp_path.replace(path)


def load_trace_metadata(trace_dir: Path) -> TraceMetadata:
    root = Path(trace_dir)
    metadata_path = root / "trace_metadata.json"
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Trace metadata not found: {metadata_path}")
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    return _trace_metadata_from_payload(payload)


def _trace_metadata_from_payload(payload: object) -> TraceMetadata:
    if not isinstance(payload, dict):
        raise ValueError("Trace metadata must be a JSON object.")

    steps_payload = payload.get("steps", [])
    if not isinstance(steps_payload, list):
        raise ValueError("Trace metadata steps must be a list.")

    steps: list[TraceStep] = []
    for item in steps_payload:
        if not isinstance(item, dict):
            raise ValueError("Each trace step must be a JSON object.")
        steps.append(
            TraceStep(
                step=str(item["step"]),
                timestamp=str(item["timestamp"]),
                input_ref=str(item["input_ref"]),
                output_ref=str(item["output_ref"]),
                prompt_version=str(item["prompt_version"]),
                model_version=str(item["model_version"]),
                rule_version=str(item["rule_version"]),
                metadata=dict(item.get("metadata", {})),
            )
        )

    return TraceMetadata(
        run_id=str(payload["run_id"]),
        created_at=str(payload["created_at"]),
        input_version=str(payload["input_version"]),
        prompt_versions=_string_dict(payload.get("prompt_versions", {}), "prompt_versions"),
        rule_versions=_string_dict(payload.get("rule_versions", {}), "rule_versions"),
        model_versions=_string_dict(payload.get("model_versions", {}), "model_versions"),
        steps=steps,
    )


def _string_dict(value: object, field_name: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"Trace metadata field {field_name} must be a JSON object.")
    return {str(key): str(item) for key, item in value.items()}
