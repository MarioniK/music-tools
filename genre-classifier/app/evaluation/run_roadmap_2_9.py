import argparse
import json
from pathlib import Path

from app.evaluation.report import (
    build_roadmap_2_11_curated_review_artifact,
    build_roadmap_2_9_evaluation_report,
)
from app.evaluation.runner import (
    ROADMAP_2_10_SUBSET_MANIFESTS,
    run_roadmap_2_10_offline_evaluation,
    run_roadmap_2_9_offline_evaluation,
)


ROADMAP_2_9_SUBSETS = ("curated", "golden", "repeat_run")
ROADMAP_2_10_SUBSETS = tuple(ROADMAP_2_10_SUBSET_MANIFESTS)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run offline Roadmap evaluation and write a stabilized JSON report.",
    )
    parser.add_argument(
        "--roadmap-stage",
        default="2.9",
        choices=("2.9", "2.10"),
        help="Offline roadmap evaluation stage to run.",
    )
    parser.add_argument(
        "--subset",
        required=True,
        help="Subset manifest to evaluate.",
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
    parser.add_argument(
        "--output-kind",
        default="evaluation_report",
        choices=("evaluation_report", "roadmap_2_11_curated_review"),
        help="Shape of the offline JSON artifact to write.",
    )
    args = parser.parse_args(argv)

    if args.output_kind == "roadmap_2_11_curated_review" and args.roadmap_stage != "2.10":
        parser.error("Roadmap 2.11 curated review artifacts must be built from Roadmap 2.10 evaluation results.")

    evaluation_result = run_offline_evaluation(
        roadmap_stage=args.roadmap_stage,
        subset_name=args.subset,
        comparison_input_path=args.input_bundle,
        parser=parser,
    )
    if args.output_kind == "roadmap_2_11_curated_review":
        report = build_roadmap_2_11_curated_review_artifact(evaluation_result)
    else:
        report = build_roadmap_2_9_evaluation_report(evaluation_result)

    output_path = write_json_report(args.output, report)
    print(
        "subset={subset} evaluated_samples={evaluated} missing_samples={missing} warning_samples={warnings} output={output}".format(
            subset=evaluation_result["subset_name"],
            evaluated=evaluation_result["evaluated_sample_count"],
            missing=len(evaluation_result["missing_sample_ids"]),
            warnings=len(evaluation_result["samples_with_warnings"]),
            output=output_path,
        )
    )
    return report


def run_offline_evaluation(roadmap_stage, subset_name, comparison_input_path, parser):
    if roadmap_stage == "2.9":
        if subset_name not in ROADMAP_2_9_SUBSETS:
            parser.error(
                "Roadmap 2.9 subset must be one of: {}".format(", ".join(ROADMAP_2_9_SUBSETS))
            )
        return run_roadmap_2_9_offline_evaluation(
            subset_name=subset_name,
            comparison_input_path=comparison_input_path,
        )

    if subset_name not in ROADMAP_2_10_SUBSETS:
        parser.error(
            "Roadmap 2.10 subset must be one of: {}".format(", ".join(ROADMAP_2_10_SUBSETS))
        )
    return run_roadmap_2_10_offline_evaluation(
        subset_name=subset_name,
        comparison_input_path=comparison_input_path,
    )


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
