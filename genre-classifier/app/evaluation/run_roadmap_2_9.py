import argparse
import json
from pathlib import Path

from app.evaluation.report import build_roadmap_2_9_evaluation_report
from app.evaluation.runner import run_roadmap_2_9_offline_evaluation


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run offline Roadmap 2.9 evaluation and write a stabilized JSON report.",
    )
    parser.add_argument(
        "--subset",
        required=True,
        choices=("curated", "golden", "repeat_run"),
        help="Roadmap 2.9 subset manifest to evaluate.",
    )
    parser.add_argument(
        "--input-bundle",
        required=True,
        help="Path to the offline comparison input JSON bundle.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path where the stabilized JSON report should be written.",
    )
    args = parser.parse_args(argv)

    evaluation_result = run_roadmap_2_9_offline_evaluation(
        subset_name=args.subset,
        comparison_input_path=args.input_bundle,
    )
    report = build_roadmap_2_9_evaluation_report(evaluation_result)

    output_path = write_json_report(args.output, report)
    print(
        "subset={subset} evaluated_samples={evaluated} missing_samples={missing} warning_samples={warnings} output={output}".format(
            subset=report["subset_name"],
            evaluated=report["run_summary"]["evaluated_sample_count"],
            missing=len(report["run_summary"]["missing_sample_ids"]),
            warnings=len(report["warning_summary"]["samples_with_warnings"]),
            output=output_path,
        )
    )
    return report


def write_json_report(path, report):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return output_path


if __name__ == "__main__":
    main()
