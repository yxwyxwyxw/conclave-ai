from __future__ import annotations

import argparse
import json
from pathlib import Path

from divination_fusion.agents import build_analysis_request
from divination_fusion.workflow import replay_trace, run_analysis, state_to_dict


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the divination fusion workflow.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--demo", action="store_true", help="Run the bundled demo scenario.")
    mode.add_argument("--query", type=str, help="User query for a normal analysis run.")
    mode.add_argument("--replay-trace", type=Path, help="Replay a saved trace directory.")
    parser.add_argument("--name", type=str, help="User name.")
    parser.add_argument("--birth-date", type=str, help="Birth date in YYYY-MM-DD.")
    parser.add_argument("--birth-time", type=str, help="Birth time in HH:MM.")
    parser.add_argument("--birth-place", type=str, help="Birth place string.")
    parser.add_argument("--timezone", type=str, help="IANA timezone, such as Asia/Shanghai.")
    parser.add_argument(
        "--max-battle-rounds",
        type=int,
        help="Maximum battle rounds before the judge forcibly terminates the issue.",
    )
    parser.add_argument("--trace-root", type=Path, default=Path("runs"), help="Trace output directory.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.replay_trace:
        replay = replay_output_from_args(args)
        print(json.dumps(replay, ensure_ascii=False, indent=2))
        return
    try:
        request = build_request_from_args(args)
    except ValueError as exc:
        parser.error(str(exc))
    state = run_analysis(
        request,
        trace_root=args.trace_root,
        battle_max_rounds=args.max_battle_rounds,
    )
    print(json.dumps(state_to_dict(state), ensure_ascii=False, indent=2))


def build_request_from_args(args: argparse.Namespace):
    if args.demo:
        extra_values = {
            "name": args.name,
            "birth_date": args.birth_date,
            "birth_time": args.birth_time,
            "birth_place": args.birth_place,
            "timezone": args.timezone,
        }
        active_fields = [field for field, value in extra_values.items() if value not in (None, "")]
        if active_fields:
            details = ", ".join(active_fields)
            raise ValueError(f"--demo 只能单独使用，不能再传这些字段: {details}")
        return _demo_request()

    query = (args.query or "").strip()
    if not query:
        raise ValueError("--query 不能为空。")
    return build_analysis_request(
        query,
        name=args.name,
        birth_date=args.birth_date,
        birth_time=args.birth_time,
        birth_place=args.birth_place,
        timezone=args.timezone,
        metadata=_request_metadata_from_args(args),
    )


def replay_output_from_args(args: argparse.Namespace) -> dict[str, object]:
    extra_values = {
        "name": args.name,
        "birth_date": args.birth_date,
        "birth_time": args.birth_time,
        "birth_place": args.birth_place,
        "timezone": args.timezone,
        "max_battle_rounds": args.max_battle_rounds,
    }
    active_fields = [field for field, value in extra_values.items() if value not in (None, "")]
    if active_fields:
        details = ", ".join(active_fields)
        raise ValueError(f"--replay-trace 只能单独使用，不能再传这些字段: {details}")
    return replay_trace(args.replay_trace)


def _demo_request():
    return build_analysis_request(
        "请综合分析我的事业、感情和性格优势",
        name="Demo User",
        birth_date="1990-06-12",
        birth_time="07:45",
        birth_place="Shanghai",
        timezone="Asia/Shanghai",
    )


def _request_metadata_from_args(args: argparse.Namespace) -> dict[str, object]:
    metadata: dict[str, object] = {}
    if args.max_battle_rounds is not None:
        metadata["max_battle_rounds"] = args.max_battle_rounds
    return metadata


if __name__ == "__main__":
    main()
