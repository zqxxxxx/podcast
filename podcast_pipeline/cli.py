from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="podcast-pipeline")
    parser.add_argument("--version", action="store_true", help="Show package version.")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("doctor", help="Check local requirements.")
    transcribe_parser = subparsers.add_parser("transcribe", help="Create timestamped transcript.")
    transcribe_parser.add_argument("--config", default="config.yaml")
    content_map_parser = subparsers.add_parser("content-map", help="Create content map.")
    content_map_parser.add_argument("--config", default="config.yaml")
    demo_parser = subparsers.add_parser("demo-edl", help="Create demo edit decision list.")
    demo_parser.add_argument("--config", default="config.yaml")
    demo_parser.add_argument("--version", default="v1")
    assemble_demo_parser = subparsers.add_parser("assemble-demo", help="Assemble demo audio from EDL.")
    assemble_demo_parser.add_argument("--config", default="config.yaml")
    assemble_demo_parser.add_argument("--version", default="v1")
    feedback_parser = subparsers.add_parser("demo-feedback", help="Ingest user feedback for a demo.")
    feedback_parser.add_argument("--config", default="config.yaml")
    feedback_parser.add_argument("--version", required=True)
    feedback_parser.add_argument("--feedback", required=True)
    freeze_parser = subparsers.add_parser("freeze-style", help="Freeze approved demo style.")
    freeze_parser.add_argument("--config", default="config.yaml")
    freeze_parser.add_argument("--approved-version", required=True)
    final_edl_parser = subparsers.add_parser("final-edl", help="Create final 50-55 minute EDL.")
    final_edl_parser.add_argument("--config", default="config.yaml")
    assemble_final_parser = subparsers.add_parser("assemble-final", help="Assemble rough cut from final EDL.")
    assemble_final_parser.add_argument("--config", default="config.yaml")
    post_parser = subparsers.add_parser("postproduction-handoff", help="Write Cleanvoice/Auphonic handoff.")
    post_parser.add_argument("--config", default="config.yaml")
    assets_parser = subparsers.add_parser("publishing-assets", help="Create transcript-derived publishing assets.")
    assets_parser.add_argument("--config", default="config.yaml")
    next_parser = subparsers.add_parser("next-steps", help="Print the recommended command order.")
    next_parser.add_argument("--config", default="config.yaml")
    return parser


def run_doctor() -> int:
    from podcast_pipeline.audio import audio_tool_paths

    print(f"workspace: {Path.cwd()}")
    missing = []
    for executable, path in audio_tool_paths().items():
        if path:
            print(f"{executable}: {path}")
        else:
            print(f"{executable}: missing")
            missing.append(executable)
    if missing:
        print("Install missing audio tools before running assembly commands.")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        from podcast_pipeline import __version__

        print(__version__)
        return 0
    if args.command == "doctor":
        return run_doctor()
    if args.command == "transcribe":
        from podcast_pipeline.config import load_config
        from podcast_pipeline.transcribe import create_transcript

        output_path = create_transcript(load_config(args.config))
        print(output_path)
        return 0
    if args.command == "content-map":
        from podcast_pipeline.config import load_config
        from podcast_pipeline.content_map import build_content_map
        from podcast_pipeline.llm import LLMClient

        config = load_config(args.config)
        output_path = build_content_map(
            LLMClient(config.text_model, config.openai_api_key_env),
            config.outputs_root / "transcript" / "transcript.json",
            config.outline_path,
            config.outputs_root / "content_map" / "content_map.json",
        )
        print(output_path)
        return 0
    if args.command == "demo-edl":
        from podcast_pipeline.config import load_config
        from podcast_pipeline.demo import create_demo_edl
        from podcast_pipeline.llm import LLMClient

        config = load_config(args.config)
        output_path = create_demo_edl(
            LLMClient(config.text_model, config.openai_api_key_env),
            config.outputs_root / "transcript" / "transcript.json",
            config.outputs_root / "content_map" / "content_map.json",
            config.outputs_root / "demos" / f"demo_{args.version}_edit_decision_list.json",
            config.demo_min_seconds,
            config.demo_max_seconds,
        )
        print(output_path)
        return 0
    if args.command == "assemble-demo":
        from podcast_pipeline.assemble import assemble_from_edl
        from podcast_pipeline.config import load_config

        config = load_config(args.config)
        output_path = assemble_from_edl(
            config.audio_path,
            config.outputs_root / "demos" / f"demo_{args.version}_edit_decision_list.json",
            config.outputs_root / "demos" / f"demo_{args.version}_parts",
            config.outputs_root / "demos" / f"demo_{args.version}.wav",
        )
        print(output_path)
        return 0
    if args.command == "demo-feedback":
        from podcast_pipeline.config import load_config
        from podcast_pipeline.llm import LLMClient
        from podcast_pipeline.style import ingest_demo_feedback

        config = load_config(args.config)
        output_path = ingest_demo_feedback(
            LLMClient(config.text_model, config.openai_api_key_env),
            args.feedback,
            config.outputs_root / "demos" / f"demo_{args.version}_feedback.json",
        )
        print(output_path)
        return 0
    if args.command == "freeze-style":
        from podcast_pipeline.config import load_config
        from podcast_pipeline.llm import LLMClient
        from podcast_pipeline.style import freeze_style

        config = load_config(args.config)
        feedback_paths = sorted((config.outputs_root / "demos").glob("demo_*_feedback.json"))
        output_path = freeze_style(
            LLMClient(config.text_model, config.openai_api_key_env),
            config.outputs_root / "demos" / f"demo_{args.approved_version}_edit_decision_list.json",
            feedback_paths,
            config.outputs_root / "style",
        )
        print(output_path)
        return 0
    if args.command == "final-edl":
        from podcast_pipeline.config import load_config
        from podcast_pipeline.edit_decision import create_final_edl
        from podcast_pipeline.llm import LLMClient

        config = load_config(args.config)
        output_path = create_final_edl(
            LLMClient(config.text_model, config.openai_api_key_env),
            config.outputs_root / "transcript" / "transcript.json",
            config.outputs_root / "content_map" / "content_map.json",
            config.outputs_root / "style" / "edit_style_guide.md",
            config.outputs_root / "style" / "selection_rules.json",
            config.outputs_root / "style" / "cutting_rules.json",
            config.outputs_root / "edit_decision_list.json",
            config.final_min_seconds,
            config.final_max_seconds,
        )
        print(output_path)
        return 0
    if args.command == "assemble-final":
        from podcast_pipeline.assemble import assemble_from_edl
        from podcast_pipeline.config import load_config

        config = load_config(args.config)
        output_path = assemble_from_edl(
            config.audio_path,
            config.outputs_root / "edit_decision_list.json",
            config.outputs_root / "rough_cut_parts",
            config.outputs_root / "rough_cut.wav",
        )
        print(output_path)
        return 0
    if args.command == "postproduction-handoff":
        from podcast_pipeline.config import load_config
        from podcast_pipeline.postproduction import write_postproduction_handoff

        config = load_config(args.config)
        output_path = write_postproduction_handoff(
            config.outputs_root / "rough_cut.wav",
            config.outputs_root / "postproduction",
        )
        print(output_path)
        return 0
    if args.command == "publishing-assets":
        from podcast_pipeline.config import load_config
        from podcast_pipeline.llm import LLMClient
        from podcast_pipeline.publish_assets import create_publishing_assets

        config = load_config(args.config)
        output_path = create_publishing_assets(
            LLMClient(config.text_model, config.openai_api_key_env),
            config.outputs_root / "transcript" / "transcript.json",
            config.outputs_root / "edit_decision_list.json",
            config.outputs_root,
        )
        print(output_path)
        return 0
    if args.command == "next-steps":
        config_path = args.config
        print(
            "\n".join(
                [
                    "1. podcast-pipeline doctor",
                    f"2. podcast-pipeline transcribe --config {config_path}",
                    f"3. podcast-pipeline content-map --config {config_path}",
                    f"4. podcast-pipeline demo-edl --config {config_path} --version v1",
                    f"5. podcast-pipeline assemble-demo --config {config_path} --version v1",
                    "6. Listen to outputs/demos/demo_v1.wav and provide feedback.",
                    f"7. podcast-pipeline demo-feedback --config {config_path} --version v1 --feedback \"...\"",
                    "8. Repeat demo-edl/assemble-demo with v2, v3 until approved.",
                    f"9. podcast-pipeline freeze-style --config {config_path} --approved-version vN",
                    f"10. podcast-pipeline final-edl --config {config_path}",
                    f"11. podcast-pipeline assemble-final --config {config_path}",
                    f"12. podcast-pipeline postproduction-handoff --config {config_path}",
                    f"13. podcast-pipeline publishing-assets --config {config_path}",
                ]
            )
        )
        return 0
    parser.print_help()
    return 0
