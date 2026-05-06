#!/usr/bin/env python3
"""Validate Roadmap 4.3 lightweight evaluation example artifacts.

This is an offline-only, dependency-free shape validator for documentation
artifacts. It intentionally does not import production app, provider, runtime,
or inference code.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, NamedTuple


EVALUATION_DIR = Path("docs/lightweight/evaluation")

REQUIRED_FILES = (
    Path("README.md"),
    Path("manifests/example-manifest.yaml"),
    Path("outputs/example-legacy-baseline-output.json"),
    Path("outputs/example-candidate-output.json"),
    Path("reports/example-evaluation-report.md"),
)

OUTPUT_FILES = (
    Path("outputs/example-legacy-baseline-output.json"),
    Path("outputs/example-candidate-output.json"),
)

MODEL_PROVENANCE_FILES = (
    Path("model-provenance/example-onnx-model-provenance.json"),
)

LOCAL_ARTIFACT_METADATA_FILES = (
    Path("model-provenance/template-local-musicnn-onnx-artifact-metadata.json"),
)

LOCAL_ARTIFACT_EVIDENCE_REPORT_FILES = (
    Path("model-provenance/example-local-musicnn-onnx-artifact-metadata-evidence-report.json"),
)

REAL_LOCAL_ARTIFACT_EVIDENCE_REPORT_FILES = (
    Path("model-provenance/local-musicnn-onnx-artifact-metadata-evidence-report.json"),
)

FIXTURE_MANIFEST_TEMPLATE_FILES = (
    Path("fixtures/template-local-musicnn-onnx-parity-fixture-manifest.json"),
)

PARITY_SCAFFOLD_DRY_RUN_OUTPUT_FILES = (
    Path("parity-scaffold/example-musicnn-onnx-parity-scaffold-dry-run-output.json"),
)

MUSICNN_ONNX_PARITY_SPIKE_REPORT_FILES = (
    Path("parity-scaffold/musicnn-onnx-parity-spike-report.json"),
)

MUSICNN_ONNX_PARITY_ENVIRONMENT_PREPARATION_REPORT_FILES = (
    Path("parity-scaffold/musicnn-onnx-parity-environment-preparation-report.json"),
)

MUSICNN_ONNX_FIXTURES_AND_BASELINE_RUNTIME_DECISION_REPORT_FILES = (
    Path("parity-scaffold/musicnn-onnx-parity-fixtures-and-baseline-runtime-decision-report.json"),
)

MUSICNN_ONNX_FIXTURE_SET_AND_BASELINE_RUNTIME_STRATEGY_REPORT_FILES = (
    Path("parity-scaffold/musicnn-onnx-parity-fixture-set-and-baseline-runtime-strategy-report.json"),
)

MUSICNN_ONNX_FIXTURES_AND_SCOPED_BASELINE_CAPTURE_APPROVAL_REPORT_FILES = (
    Path(
        "parity-scaffold/"
        "musicnn-onnx-parity-fixtures-and-scoped-baseline-capture-approval-report.json"
    ),
)

MUSICNN_ONNX_FIXTURE_PLACEMENT_AND_SCOPED_BASELINE_READINESS_REPORT_FILES = (
    Path(
        "parity-scaffold/"
        "musicnn-onnx-parity-fixture-placement-and-scoped-baseline-readiness-report.json"
    ),
)

MUSICNN_LEGACY_BASELINE_CAPTURE_REPORT_FILES = (
    Path("parity-scaffold/musicnn-legacy-baseline-capture-report.json"),
)

MUSICNN_ONNX_PREPROCESSING_ALIGNMENT_REPORT_FILES = (
    Path("parity-scaffold/musicnn-onnx-preprocessing-alignment-report.json"),
)

MUSICNN_ONNX_OUTPUT_CAPTURE_REPORT_FILES = (
    Path("parity-scaffold/musicnn-onnx-output-capture-report.json"),
)

MUSICNN_ONNX_FIXTURE_VISIBILITY_STRATEGY_REPORT_FILES = (
    Path("parity-scaffold/musicnn-onnx-fixture-visibility-strategy-report.json"),
)

MUSICNN_LEGACY_BASELINE_IMPORT_ORDER_DIAGNOSTIC_REPORT_FILES = (
    Path("parity-scaffold/musicnn-legacy-baseline-import-order-diagnostic-report.json"),
)

MUSICNN_ONNX_PRAGMATIC_PREPROCESSING_PROTOTYPE_REPORT_FILES = (
    Path("evidence/roadmap-4.56-onnx-musicnn-pragmatic-preprocessing-prototype-report.json"),
)

MUSICNN_TENSORFLOW_INPUT_MUSICCNN_AVAILABILITY_PROBE_REPORT_FILES = (
    Path("evidence/roadmap-4.57-tensorflow-input-musicnn-availability-probe-report.json"),
)

REQUIRED_LOCAL_ARTIFACT_METADATA_FIELDS = (
    "schema_version",
    "report_type",
    "report_id",
    "candidate_family",
    "purpose",
    "not_production_decision",
    "approved_for_inference",
    "approved_for_production",
    "created_at",
    "generated_by",
    "artifacts",
    "validation_status",
    "warnings",
    "no_go_items",
    "next_step_recommendation",
)

LOCAL_ARTIFACT_METADATA_STRING_FIELDS = (
    "schema_version",
    "report_type",
    "report_id",
    "candidate_family",
    "purpose",
    "generated_by",
    "next_step_recommendation",
)

REQUIRED_LOCAL_ARTIFACT_ROLES = (
    "current_bundled_pb",
    "current_bundled_json",
    "official_local_onnx",
    "optional_official_local_pb",
    "official_local_json",
)

OFFICIAL_LOCAL_ARTIFACT_ROLES = (
    "official_local_onnx",
    "optional_official_local_pb",
    "official_local_json",
)

REQUIRED_LOCAL_ARTIFACT_FIELDS = (
    "artifact_role",
    "artifact_name",
    "source_url",
    "local_path",
    "local_only",
    "artifact_downloaded",
    "artifact_in_repo",
    "committed_to_repo",
    "file_size_bytes",
    "sha256",
    "provenance_notes",
    "license_notes",
)

LOCAL_ARTIFACT_PLACEHOLDER_HASHES = {
    "todo",
    "tbd",
    "fake",
    "example",
    "placeholder",
    "0" * 64,
}

LOCAL_ARTIFACT_EVIDENCE_REPORT_TYPE = "local_musicnn_onnx_artifact_metadata_evidence_report_sample"

REQUIRED_LOCAL_ARTIFACT_EVIDENCE_REPORT_FIELDS = (
    "schema_version",
    "report_type",
    "report_id",
    "sample_only",
    "candidate_family",
    "purpose",
    "not_production_decision",
    "approved_for_inference",
    "approved_for_production",
    "generated_by",
    "artifacts",
    "warnings",
    "no_go_items",
    "review_status",
    "next_step_recommendation",
)

LOCAL_ARTIFACT_EVIDENCE_REPORT_STRING_FIELDS = (
    "schema_version",
    "report_type",
    "report_id",
    "candidate_family",
    "purpose",
    "generated_by",
    "review_status",
    "next_step_recommendation",
)

LOCAL_ARTIFACT_EVIDENCE_REPORT_REVIEW_STATUSES = {
    "sample_only_not_approved",
    "pending_review",
    "reviewed_not_approved",
    "blocked",
}

REAL_LOCAL_ARTIFACT_EVIDENCE_REPORT_TYPE = "local_musicnn_onnx_artifact_metadata_evidence_report"

REQUIRED_REAL_LOCAL_ARTIFACT_EVIDENCE_REPORT_FIELDS = (
    "schema_version",
    "report_type",
    "report_id",
    "candidate_family",
    "purpose",
    "not_production_decision",
    "approved_for_inference",
    "approved_for_production",
    "generated_by",
    "artifacts",
    "verification_commands",
    "verification_results",
    "warnings",
    "no_go_items",
    "review_status",
    "approval_status",
    "next_step_recommendation",
)

REAL_LOCAL_ARTIFACT_EVIDENCE_REPORT_STRING_FIELDS = (
    "schema_version",
    "report_type",
    "report_id",
    "candidate_family",
    "purpose",
    "generated_by",
    "review_status",
    "approval_status",
    "next_step_recommendation",
)

REAL_LOCAL_ARTIFACT_EVIDENCE_REPORT_REVIEW_STATUSES = {
    "prepared_for_review",
    "reviewed_not_approved",
}

EXPECTED_REAL_LOCAL_ARTIFACT_HASHES = {
    "official_local_onnx": "49668ffec47e52e94b96f45930bb46a28a1368d4bdfb5c05378fa834aca616e1",
    "optional_official_local_pb": "cdea0722bcee7f731286843f2233e3aa69887bb5c3e2dce011eff55f38d04f3e",
    "current_bundled_pb": "cdea0722bcee7f731286843f2233e3aa69887bb5c3e2dce011eff55f38d04f3e",
    "official_local_json": "8e6b3b509f0610c0e65dce467fd459d6777509388eaddb13ed138d8ac1341ffe",
    "current_bundled_json": "24842b068b5c09dce033a0bcb41d450e4e469352b799e831ac7728c93bbfb6be",
}

LOCAL_ARTIFACT_APPROVAL_FLAG_FIELDS = {
    "approved_for_inference",
    "approved_for_production",
    "inference_approved",
    "production_approved",
}

LOCAL_ARTIFACT_REPO_PATH_PREFIXES = (
    "/opt/music-tools",
    "/opt/music-tools/genre-classifier",
    "docs/",
    "tests/",
    "app/",
    "models/",
)

REQUIRED_LOCAL_ARTIFACT_VALIDATION_STATUS = {
    "template_only": True,
    "artifact_metadata_complete": False,
    "real_local_paths_recorded": False,
    "real_hashes_recorded": False,
    "real_file_sizes_recorded": False,
    "license_review_complete": False,
    "compared_against_legacy_musicnn_baseline": False,
}

FIXTURE_MANIFEST_TEMPLATE_TYPE = "local_musicnn_onnx_parity_fixture_manifest_template"

REQUIRED_FIXTURE_MANIFEST_TEMPLATE_FIELDS = (
    "schema_version",
    "manifest_type",
    "template_only",
    "not_production_decision",
    "approval_status",
    "approved_for_inference",
    "approved_for_production",
    "approved_for_local_parity_evaluation",
    "approved_for_repo_inclusion",
    "audio_files_in_repo",
    "real_audio_fixtures_included",
    "fixture_manifest_approved",
    "fixture_storage_policy",
    "required_fixture_fields",
    "fixture_categories",
    "sample_fixture",
)

REQUIRED_FIXTURE_FIELDS = (
    "fixture_id",
    "local_path",
    "local_only",
    "artifact_in_repo",
    "committed_to_repo",
    "duration_seconds",
    "file_size_bytes",
    "sha256",
    "audio_format",
    "sample_rate_hz",
    "channels",
    "source_type",
    "license_status",
    "usage_permission",
    "provenance_notes",
    "expected_quality_notes",
    "category",
    "tags",
    "approved_for_local_parity_evaluation",
    "approved_for_repo_inclusion",
)

FIXTURE_CATEGORIES = (
    "clear mainstream genre sample",
    "ambiguous / overlapping genre sample",
    "low-confidence / edge sample",
    "short sample",
    "production-relevant sample",
    "silence / corrupt / unreadable negative sample",
)

FIXTURE_FORBIDDEN_PATH_MARKERS = (
    "repo root",
    "docs/",
    "tests/",
    "app/",
    "any git-tracked path",
    "any location under /opt/music-tools/genre-classifier",
)

LABEL_MAPPING_FILES = (
    Path("label-mapping/example-onnx-label-mapping.json"),
)

EVIDENCE_PACKAGE_FILES = (
    Path("evidence/example-onnx-evidence-package.json"),
)

REQUIRED_MODEL_PROVENANCE_FIELDS = (
    "schema_version",
    "model_id",
    "model_name",
    "model_family",
    "model_format",
    "source_url",
    "source_repository",
    "license",
    "license_url",
    "model_version",
    "model_hash_sha256",
    "model_file_name",
    "model_file_size_bytes",
    "input_names",
    "input_shapes",
    "output_names",
    "output_shapes",
    "label_source",
    "label_count",
    "label_mapping_strategy",
    "intended_use",
    "known_limitations",
    "approval_status",
    "warnings",
)

MODEL_PROVENANCE_STRING_FIELDS = (
    "schema_version",
    "model_id",
    "model_name",
    "model_family",
    "model_format",
    "source_url",
    "source_repository",
    "license",
    "license_url",
    "model_version",
    "model_hash_sha256",
    "model_file_name",
    "label_source",
    "label_mapping_strategy",
    "intended_use",
    "approval_status",
)

PRODUCTION_APPROVED_STATUSES = {
    "approved",
    "approved_for_inference",
    "production_approved",
    "production-approved",
}

REQUIRED_LABEL_MAPPING_FIELDS = (
    "schema_version",
    "mapping_id",
    "model_id",
    "model_family",
    "label_source",
    "label_source_url",
    "label_count",
    "mapping_status",
    "labels",
    "controlled_vocabulary_version",
    "unmapped_labels",
    "warnings",
    "approval_status",
)

LABEL_MAPPING_STRING_FIELDS = (
    "schema_version",
    "mapping_id",
    "model_id",
    "model_family",
    "label_source",
    "label_source_url",
    "mapping_status",
    "controlled_vocabulary_version",
    "approval_status",
)

REQUIRED_LABEL_MAPPING_LABEL_FIELDS = (
    "raw_label",
    "raw_index",
    "mapped_genre",
    "mapped_confidence",
    "mapping_decision",
    "mapping_notes",
)

LABEL_MAPPING_DECISIONS = {
    "mapped",
    "alias_mapped",
    "ignored_non_genre",
    "unmapped",
    "rejected_ambiguous",
}

LABEL_MAPPING_APPROVAL_STATUSES = {
    "not_approved",
    "approved_for_offline_evaluation",
    "rejected",
    "deprecated",
}

EVIDENCE_PACKAGE_TYPE = "onnx_offline_evaluation_evidence_package"

EVIDENCE_DECISION_STATUSES = {
    "continue",
    "revise",
    "reject",
    "blocked",
}

REQUIRED_EVIDENCE_PACKAGE_FIELDS = (
    "schema_version",
    "package_id",
    "package_type",
    "created_at",
    "decision_status",
    "decision_summary",
    "not_production_decision",
    "baseline_provider",
    "candidate_provider",
    "candidate_family",
    "artifacts",
    "model_provenance_path",
    "label_mapping_path",
    "manifest_path",
    "baseline_output_path",
    "candidate_output_path",
    "report_path",
    "validation",
    "validator_command",
    "validator_result",
    "tests_command",
    "tests_result",
    "approvals",
    "approval_gates",
    "no_go_checklist",
    "warnings",
    "known_gaps",
    "next_step_recommendation",
)

EVIDENCE_PACKAGE_STRING_FIELDS = (
    "schema_version",
    "package_id",
    "package_type",
    "created_at",
    "decision_status",
    "decision_summary",
    "baseline_provider",
    "candidate_provider",
    "candidate_family",
    "model_provenance_path",
    "label_mapping_path",
    "manifest_path",
    "baseline_output_path",
    "candidate_output_path",
    "report_path",
    "validator_command",
    "validator_result",
    "tests_command",
    "tests_result",
    "next_step_recommendation",
)

EVIDENCE_PACKAGE_ARTIFACT_PATH_FIELDS = (
    "model_provenance_path",
    "label_mapping_path",
    "manifest_path",
    "baseline_output_path",
    "candidate_output_path",
    "report_path",
)

EVIDENCE_PACKAGE_LIST_FIELDS = (
    "approval_gates",
    "no_go_checklist",
    "warnings",
    "known_gaps",
)

MUSICNN_ONNX_PARITY_SPIKE_REPORT_TYPE = "musicnn_onnx_parity_spike_report"
MUSICNN_ONNX_PARITY_ENVIRONMENT_PREPARATION_REPORT_TYPE = (
    "musicnn_onnx_parity_environment_preparation_report"
)
MUSICNN_ONNX_FIXTURES_AND_BASELINE_RUNTIME_DECISION_REPORT_TYPE = (
    "musicnn_onnx_fixtures_and_baseline_runtime_decision_report"
)
MUSICNN_ONNX_FIXTURE_SET_AND_BASELINE_RUNTIME_STRATEGY_REPORT_TYPE = (
    "musicnn_onnx_fixture_set_and_baseline_runtime_strategy_report"
)
MUSICNN_ONNX_FIXTURES_AND_SCOPED_BASELINE_CAPTURE_APPROVAL_REPORT_TYPE = (
    "musicnn_onnx_fixtures_and_scoped_baseline_capture_approval_report"
)
MUSICNN_ONNX_FIXTURE_PLACEMENT_AND_SCOPED_BASELINE_READINESS_REPORT_TYPE = (
    "musicnn_onnx_fixture_placement_and_scoped_baseline_readiness_report"
)
MUSICNN_LEGACY_BASELINE_CAPTURE_REPORT_TYPE = "musicnn_legacy_baseline_capture_report"
MUSICNN_ONNX_PREPROCESSING_ALIGNMENT_REPORT_TYPE = "musicnn_onnx_preprocessing_alignment_report"
MUSICNN_ONNX_PRAGMATIC_PREPROCESSING_PROTOTYPE_REPORT_TYPE = (
    "musicnn_onnx_pragmatic_preprocessing_prototype_report"
)
MUSICNN_TENSORFLOW_INPUT_MUSICCNN_AVAILABILITY_PROBE_REPORT_TYPE = (
    "musicnn_tensorflow_input_musiccnn_availability_probe_report"
)
MUSICNN_ONNX_OUTPUT_CAPTURE_REPORT_TYPE = "musicnn_onnx_output_capture_report"
MUSICNN_ONNX_FIXTURE_VISIBILITY_STRATEGY_REPORT_TYPE = (
    "musicnn_onnx_fixture_visibility_strategy_report"
)
MUSICNN_LEGACY_BASELINE_IMPORT_ORDER_DIAGNOSTIC_REPORT_TYPE = (
    "musicnn_legacy_baseline_import_order_diagnostic_report"
)

MUSICNN_ONNX_OUTPUT_CAPTURE_BLOCKERS = {
    "AGENTS_MD_NOT_READ",
    "BASELINE_EVIDENCE_MISSING",
    "ONNX_ARTIFACT_MISSING",
    "ONNX_METADATA_MISSING",
    "ONNXRUNTIME_UNAVAILABLE",
    "FIXTURE_FILES_MISSING",
    "PREPROCESSING_ALIGNMENT_UNKNOWN",
    "ONNX_INPUT_SHAPE_UNSUPPORTED",
    "ONNX_CAPTURE_HELPER_UNSAFE",
    "ONNX_CAPTURE_FAILED",
    "CLASSIFY_CALL_NOT_ALLOWED",
    "PRODUCTION_DEPENDENCY_CHANGE_NOT_ALLOWED",
    "MODEL_FILE_IN_REPO_NOT_ALLOWED",
    "AUDIO_FILE_IN_REPO_NOT_ALLOWED",
    "VENV_IN_REPO_NOT_ALLOWED",
    "NUMERIC_PARITY_DECISION_NOT_APPROVED",
    "LOCAL_PATHS_NOT_PUBLISHABLE",
    "TIDAL_PARSER_SCOPE_VIOLATION",
}

MUSICNN_ONNX_PREPROCESSING_ALIGNMENT_BLOCKERS = {
    "AGENTS_MD_NOT_READ",
    "BASELINE_EVIDENCE_MISSING",
    "ONNX_ARTIFACT_MISSING",
    "ONNX_METADATA_MISSING",
    "LEGACY_METADATA_MISSING",
    "PREPROCESSING_PARAMETERS_MISSING",
    "MEL_INPUT_GENERATION_UNKNOWN",
    "LEGACY_INTERMEDIATE_NOT_EXPOSED",
    "TENSOR_LAYOUT_UNKNOWN",
    "NORMALIZATION_UNKNOWN",
    "ESSENTIA_PREPROCESSING_CHAIN_UNCONFIRMED",
    "ONNX_INPUT_SHAPE_UNSUPPORTED",
    "ONNX_FIXTURE_CAPTURE_NOT_APPROVED",
    "CLASSIFY_CALL_NOT_ALLOWED",
    "PRODUCTION_DEPENDENCY_CHANGE_NOT_ALLOWED",
    "MODEL_FILE_IN_REPO_NOT_ALLOWED",
    "AUDIO_FILE_IN_REPO_NOT_ALLOWED",
    "VENV_IN_REPO_NOT_ALLOWED",
    "FINAL_PARITY_DECISION_NOT_APPROVED",
    "LOCAL_PATHS_NOT_PUBLISHABLE",
    "TIDAL_PARSER_SCOPE_VIOLATION",
}

MUSICNN_ONNX_PRAGMATIC_PREPROCESSING_PROTOTYPE_BLOCKERS = {
    "AGENTS_MD_NOT_READ",
    "BASELINE_EVIDENCE_MISSING",
    "ONNX_ARTIFACT_MISSING",
    "ONNX_METADATA_MISSING",
    "ONNXRUNTIME_UNAVAILABLE",
    "FIXTURE_FILES_MISSING",
    "PRAGMATIC_PREPROCESSING_DEPENDENCY_UNAVAILABLE",
    "ESSENTIA_STANDARD_MEL_PATH_UNAVAILABLE",
    "MEL_PATCH_SHAPE_NOT_PRODUCED",
    "CLASSIFY_CALL_NOT_ALLOWED",
    "PRODUCTION_DEPENDENCY_CHANGE_NOT_ALLOWED",
    "MODEL_FILE_IN_REPO_NOT_ALLOWED",
    "AUDIO_FILE_IN_REPO_NOT_ALLOWED",
    "VENV_IN_REPO_NOT_ALLOWED",
    "LOCAL_PATHS_NOT_PUBLISHABLE",
    "TIDAL_PARSER_SCOPE_VIOLATION",
}

MUSICNN_TENSORFLOW_INPUT_MUSICCNN_AVAILABILITY_PROBE_BLOCKERS = {
    "AGENTS_MD_NOT_READ",
    "ROADMAP_4_55_STRATEGY_REPORT_MISSING",
    "ROADMAP_4_56_PROTOTYPE_REPORT_MISSING",
    "FIXTURE_FILES_MISSING",
    "ISOLATED_ENV_MISSING",
    "ONNXRUNTIME_UNAVAILABLE",
    "ESSENTIA_IMPORT_FAILED",
    "TENSORFLOW_INPUT_MUSICNN_UNAVAILABLE",
    "TENSORFLOW_INPUT_MUSICNN_IMPORT_FAILED",
    "TENSORFLOW_INPUT_MUSICNN_PROBE_FAILED",
    "MUSICNN_MEL_PATCH_SHAPE_NOT_PRODUCED",
    "MUSICNN_MEL_PATCH_SHAPE_UNSTABLE",
    "GENERIC_MELBANDS_FALLBACK_USED",
    "GENERIC_MELBANDS_FALLBACK_BLOCKED",
    "LOCAL_PATHS_NOT_PUBLISHABLE",
    "MODEL_FILE_IN_REPO_NOT_ALLOWED",
    "AUDIO_FILE_IN_REPO_NOT_ALLOWED",
    "PRODUCTION_DEPENDENCY_CHANGE_NOT_APPROVED",
    "CLASSIFY_CALL_NOT_ALLOWED",
    "PROVIDER_IMPLEMENTATION_NOT_APPROVED",
    "DEFAULT_PROVIDER_SWITCH_NOT_APPROVED",
    "PRODUCTION_MIGRATION_NOT_APPROVED",
    "TIDAL_PARSER_SCOPE_VIOLATION",
}

REQUIRED_MUSICNN_ONNX_OUTPUT_CAPTURE_FIELDS = (
    "report_type",
    "roadmap",
    "report_id",
    "generated_by",
    "agents_md_read",
    "not_production_decision",
    "approved_for_production",
    "approved_for_provider_implementation",
    "approved_for_default_provider_switch",
    "approved_for_full_numeric_parity_run",
    "approved_for_final_parity_decision",
    "approved_for_classify_contract_change",
    "no_audio_files_committed",
    "no_model_files_committed",
    "no_venv_committed",
    "no_dependency_changes",
    "no_dockerfile_changes",
    "no_compose_file_changes",
    "no_docker_rebuild",
    "no_classify_calls",
    "no_provider_changes",
    "no_tidal_parser_changes",
    "legacy_musicnn_remains_baseline",
    "baseline_evidence",
    "onnx_environment",
    "onnx_artifacts",
    "fixture_count",
    "sanitized_fixtures",
    "onnx_model_metadata",
    "onnx_capture_succeeded",
    "onnx_capture_status",
    "onnx_outputs",
    "blockers",
    "warnings",
    "next_step_recommendation",
)

REQUIRED_MUSICNN_ONNX_PREPROCESSING_ALIGNMENT_FIELDS = (
    "report_type",
    "roadmap",
    "report_id",
    "generated_by",
    "agents_md_read",
    "not_production_decision",
    "approved_for_production",
    "approved_for_provider_implementation",
    "approved_for_default_provider_switch",
    "approved_for_full_numeric_parity_run",
    "approved_for_final_parity_decision",
    "approved_for_classify_contract_change",
    "approved_for_onnx_fixture_output_capture",
    "no_audio_files_committed",
    "no_model_files_committed",
    "no_venv_committed",
    "no_dependency_changes",
    "no_dockerfile_changes",
    "no_compose_file_changes",
    "no_docker_rebuild",
    "no_classify_calls",
    "no_provider_changes",
    "no_tidal_parser_changes",
    "legacy_musicnn_remains_baseline",
    "baseline_evidence",
    "onnx_model_metadata",
    "preprocessing_metadata",
    "legacy_preprocessing_path",
    "alignment_status",
    "candidate_alignment_path",
    "blockers",
    "warnings",
    "next_step_recommendation",
)

REQUIRED_MUSICNN_ONNX_PRAGMATIC_PREPROCESSING_PROTOTYPE_FIELDS = (
    "schema_version",
    "report_type",
    "report_id",
    "generated_by",
    "created_at",
    "roadmap",
    "agents_md_read",
    "not_production_decision",
    "target_candidate",
    "strategy_source",
    "strict_legacy_parity_required",
    "output_drift_allowed",
    "preprocessing_identical_to_legacy_required",
    "documented_reproducible_preprocessing_required",
    "approved_for_provider_implementation",
    "approved_for_default_provider_switch",
    "approved_for_production",
    "approved_for_dependency_changes",
    "approved_for_classify_call",
    "legacy_musicnn_default_unchanged",
    "prototype_modes",
    "onnx_artifacts",
    "baseline_evidence",
    "onnx_input",
    "expected_outputs",
    "local_environment",
    "preprocessing_probe_result",
    "sanitized_fixtures",
    "blockers",
    "next_step_recommendation",
)

REQUIRED_MUSICNN_TENSORFLOW_INPUT_MUSICCNN_AVAILABILITY_PROBE_FIELDS = (
    "schema_version",
    "report_type",
    "report_id",
    "generated_by",
    "created_at",
    "roadmap",
    "agents_md_read",
    "not_production_decision",
    "target_candidate",
    "strategy_source",
    "prototype_source",
    "strict_legacy_parity_required",
    "output_drift_allowed",
    "preprocessing_identical_to_legacy_required",
    "documented_reproducible_preprocessing_required",
    "approved_for_provider_implementation",
    "approved_for_default_provider_switch",
    "approved_for_production",
    "approved_for_dependency_changes",
    "approved_for_classify_call",
    "legacy_musicnn_default_unchanged",
    "isolated_python_used_for_availability_check",
    "preprocessing_probe_execution",
    "recommended_isolated_probe_invocation",
    "probe_policy",
    "tensorflow_input_musiccnn",
    "preprocessing_probe_result",
    "sanitized_fixtures",
    "fallback",
    "blockers",
    "next_step_recommendation",
)

MUSICNN_ONNX_PARITY_SPIKE_DECISION_STATUSES = {
    "viable",
    "not_viable",
    "needs_preprocessing_alignment",
    "blocked_missing_runtime",
    "blocked_missing_fixtures",
    "blocked_missing_artifacts",
}

MUSICNN_ONNX_PARITY_SPIKE_BLOCKED_STATUSES = {
    "blocked_missing_runtime",
    "blocked_missing_fixtures",
    "blocked_missing_artifacts",
}

REQUIRED_MUSICNN_ONNX_PARITY_SPIKE_FIELDS = (
    "schema_version",
    "roadmap",
    "report_type",
    "report_id",
    "generated_by",
    "not_production_decision",
    "approved_for_production",
    "approved_for_provider_implementation",
    "approved_for_default_provider_switch",
    "approved_for_inference_beyond_local_spike",
    "legacy_musicnn_remains_baseline",
    "default_provider_unchanged",
    "classify_contract_unchanged",
    "response_shape_unchanged",
    "no_audio_files_committed",
    "no_model_files_committed",
    "no_dependency_changes",
    "onnxruntime_added_to_production_requirements",
    "no_docker_changes",
    "no_provider_factory_changes",
    "no_default_provider_changes",
    "no_classify_calls",
    "tidal_parser_untouched",
    "fixture_count",
    "baseline_runtime_available",
    "onnx_runtime_available",
    "model_artifacts_available",
    "fixtures_available",
    "baseline_capture_attempted",
    "onnx_capture_attempted",
    "parity_run_executed",
    "decision_status",
    "blockers",
    "metrics",
    "warnings",
    "next_step_recommendation",
)

MUSICNN_ONNX_PARITY_ENVIRONMENT_STATUSES = {
    "ready_for_local_parity_run",
    "partially_ready",
    "blocked",
}

MUSICNN_ONNX_PARITY_ENVIRONMENT_BLOCKERS = {
    "FIXTURE_DIR_MISSING",
    "FIXTURE_FILES_MISSING",
    "FIXTURE_PROVENANCE_UNCLEAR",
    "ONNXRUNTIME_UNAVAILABLE",
    "ONNXRUNTIME_LOCAL_INSTALL_FAILED",
    "BASELINE_RUNTIME_UNAVAILABLE",
    "BASELINE_ENVIRONMENT_NOT_REPRODUCIBLE",
    "ESSENTIA_UNAVAILABLE",
    "TENSORFLOW_UNAVAILABLE",
    "MODEL_ARTIFACTS_MISSING",
    "UNSAFE_TO_IMPORT_BASELINE_PROVIDER",
    "LOCAL_ENV_NOT_CREATED",
    "LOCAL_PATHS_NOT_PUBLISHABLE",
    "PARITY_RUN_NOT_EXECUTED",
}

REQUIRED_MUSICNN_ONNX_PARITY_ENVIRONMENT_PREPARATION_FIELDS = (
    "report_type",
    "roadmap",
    "not_production_decision",
    "approved_for_production",
    "approved_for_provider_implementation",
    "approved_for_default_provider_switch",
    "approved_for_inference_beyond_local_spike",
    "no_audio_files_committed",
    "no_model_files_committed",
    "no_venv_committed",
    "no_dependency_changes",
    "no_docker_changes",
    "no_classify_calls",
    "legacy_musicnn_remains_baseline",
    "environment_status",
    "blockers",
    "prerequisites",
    "next_step_recommendation",
)

REQUIRED_MUSICNN_ONNX_PARITY_ENVIRONMENT_PREREQUISITES = (
    "model_artifacts_available",
    "fixture_dir_available",
    "fixture_count",
    "onnxruntime_available",
    "tensorflow_available",
    "essentia_available",
    "baseline_runtime_available",
    "isolated_env_created",
    "isolated_env_path_sanitized",
)

MUSICNN_ONNX_FIXTURE_STATUSES = {
    "available",
    "missing",
    "unclear_provenance",
}

MUSICNN_ONNX_BASELINE_RUNTIME_STATUSES = {
    "available",
    "unavailable",
    "container_only_candidate",
    "container_strategy_candidate",
    "unsafe_to_import",
}

MUSICNN_ONNX_DECISION_GATE_STATUSES = {
    "ready_for_numeric_parity_run",
    "blocked_missing_fixtures",
    "blocked_missing_baseline_runtime",
    "blocked_missing_fixtures_and_baseline_runtime",
    "blocked_fixture_provenance_unclear",
    "baseline_container_strategy_selected",
}

MUSICNN_ONNX_DECISION_GATE_BLOCKERS = {
    "FIXTURE_FILES_MISSING",
    "FIXTURE_PROVENANCE_UNCLEAR",
    "TENSORFLOW_UNAVAILABLE",
    "ESSENTIA_UNAVAILABLE",
    "BASELINE_RUNTIME_UNAVAILABLE",
    "BASELINE_CONTAINER_PATH_NEEDED",
    "BASELINE_CONTAINER_STRATEGY_SELECTED",
    "BASELINE_ENVIRONMENT_NOT_REPRODUCIBLE",
    "UNSAFE_TO_IMPORT_BASELINE_PROVIDER",
    "ONNXRUNTIME_ENV_NOT_AVAILABLE",
    "LOCAL_PATHS_NOT_PUBLISHABLE",
    "NUMERIC_PARITY_NOT_APPROVED",
}

MUSICNN_ONNX_SCOPED_BASELINE_CAPTURE_DECISION_STATUSES = {
    "ready_for_scoped_baseline_capture",
    "blocked_missing_fixtures",
    "blocked_fixture_provenance_unclear",
    "blocked_container_unavailable",
    "blocked_missing_fixtures_and_container_unavailable",
}

MUSICNN_ONNX_FIXTURE_PLACEMENT_READINESS_STATUSES = {
    "ready_for_scoped_baseline_capture",
    "fixtures_ready_container_not_checked",
    "blocked_container_unavailable",
    "blocked_service_unknown",
    "blocked_container_strategy_not_reproducible",
    "blocked_fixture_provenance_unclear",
}

MUSICNN_ONNX_SCOPED_BASELINE_CAPTURE_BLOCKERS = {
    "FIXTURE_FILES_MISSING",
    "BLOCKED_FIXTURE_PROVENANCE_UNCLEAR",
    "CONTAINER_SERVICE_UNCONFIRMED",
    "CONTAINER_UNAVAILABLE",
}

MUSICNN_ONNX_FIXTURE_PLACEMENT_READINESS_BLOCKERS = {
    "FIXTURE_FILES_MISSING",
    "FIXTURE_PROVENANCE_UNCLEAR",
    "FIXTURE_HASH_MISMATCH",
    "BASELINE_CONTAINER_UNAVAILABLE",
    "BASELINE_CONTAINER_SERVICE_UNKNOWN",
    "BASELINE_CONTAINER_STRATEGY_NOT_REPRODUCIBLE",
    "BASELINE_CAPTURE_NOT_APPROVED",
    "NUMERIC_PARITY_NOT_APPROVED",
    "LOCAL_PATHS_NOT_PUBLISHABLE",
}

MUSICNN_LEGACY_BASELINE_CAPTURE_BLOCKERS = {
    "BASELINE_CONTAINER_SERVICE_UNKNOWN",
    "ONE_OFF_COMPOSE_RUN_FAILED",
    "FIXTURE_BIND_MOUNT_FAILED",
    "FIXTURE_PATH_NOT_VISIBLE_IN_ONE_OFF_CONTAINER",
    "BASELINE_IMPORT_FAILED",
    "ESSENTIA_IMPORT_FAILED",
    "BITCAST_DUPLICATE_REGISTRATION",
    "BASELINE_CAPTURE_SCRIPT_UNSAFE",
    "BASELINE_CAPTURE_FAILED",
    "CLASSIFY_CALL_NOT_ALLOWED",
    "ONNX_EXECUTION_NOT_ALLOWED",
    "NUMERIC_PARITY_NOT_APPROVED",
    "LOCAL_PATHS_NOT_PUBLISHABLE",
}

MUSICNN_LEGACY_BASELINE_IMPORT_ORDER_DIAGNOSTIC_DECISION_STATUSES = {
    "safe_import_order_found",
    "blocked_import_order_unresolved",
    "blocked_container_diagnostic_failed",
    "blocked_service_unknown",
}

MUSICNN_LEGACY_BASELINE_IMPORT_ORDER_DIAGNOSTIC_BLOCKERS = {
    "IMPORT_ORDER_UNRESOLVED",
    "BITCAST_DUPLICATE_REGISTRATION",
    "CONTAINER_DIAGNOSTIC_FAILED",
    "SERVICE_UNKNOWN",
}

MUSICNN_LEGACY_BASELINE_IMPORT_ORDER_DIAGNOSTIC_ERROR_CATEGORIES = {
    "none",
    "tensorflow_import_failed",
    "essentia_import_failed",
    "duplicate_tensorflow_op_registration",
    "bitcast_duplicate_registration",
    "predictor_import_failed",
    "container_execution_failed",
    "unknown_runtime_error",
}

REQUIRED_MUSICNN_LEGACY_BASELINE_IMPORT_ORDER_DIAGNOSTIC_FIELDS = (
    "report_type",
    "roadmap",
    "not_production_decision",
    "approved_for_production",
    "approved_for_provider_implementation",
    "approved_for_default_provider_switch",
    "approved_for_full_numeric_parity_run",
    "approved_for_onnx_execution",
    "approved_for_baseline_output_capture",
    "no_audio_files_committed",
    "no_model_files_committed",
    "no_venv_committed",
    "no_dependency_changes",
    "no_dockerfile_changes",
    "no_compose_file_changes",
    "no_docker_rebuild",
    "no_classify_calls",
    "no_onnx_execution",
    "no_tensorflow_vs_onnx_comparison",
    "legacy_musicnn_remains_baseline",
    "diagnostic_scope",
    "observed_previous_blocker",
    "diagnostic_cases",
    "safe_import_order",
    "decision_status",
    "blockers",
    "next_step_recommendation",
)

REQUIRED_MUSICNN_LEGACY_BASELINE_IMPORT_ORDER_CASE_FIELDS = (
    "case_id",
    "import_order",
    "exit_code",
    "succeeded",
    "error_category",
    "bitcast_duplicate_seen",
    "notes",
)

LEGACY_MUSICNN_IMPORT_ORDER_DIAGNOSTIC_TRUE_FIELDS = (
    "not_production_decision",
    "no_audio_files_committed",
    "no_model_files_committed",
    "no_venv_committed",
    "no_dependency_changes",
    "no_dockerfile_changes",
    "no_compose_file_changes",
    "no_docker_rebuild",
    "no_classify_calls",
    "no_onnx_execution",
    "no_tensorflow_vs_onnx_comparison",
    "legacy_musicnn_remains_baseline",
)

LEGACY_MUSICNN_IMPORT_ORDER_DIAGNOSTIC_FALSE_FIELDS = (
    "approved_for_production",
    "approved_for_provider_implementation",
    "approved_for_default_provider_switch",
    "approved_for_full_numeric_parity_run",
    "approved_for_onnx_execution",
    "approved_for_baseline_output_capture",
)

REQUIRED_MUSICNN_ONNX_SCOPED_BASELINE_CAPTURE_APPROVAL_FIELDS = (
    "report_type",
    "roadmap",
    "not_production_decision",
    "approved_for_production",
    "approved_for_provider_implementation",
    "approved_for_default_provider_switch",
    "approved_for_full_numeric_parity_run",
    "approved_for_scoped_baseline_capture",
    "fixture_workspace",
    "fixtures",
    "fixture_blockers",
    "baseline_capture",
    "container_strategy",
    "readiness_decision",
    "safety_confirmations",
)

REQUIRED_MUSICNN_ONNX_FIXTURE_PLACEMENT_READINESS_FIELDS = (
    "report_type",
    "roadmap",
    "not_production_decision",
    "approved_for_production",
    "approved_for_provider_implementation",
    "approved_for_default_provider_switch",
    "approved_for_full_numeric_parity_run",
    "approved_for_scoped_baseline_capture",
    "no_audio_files_committed",
    "no_model_files_committed",
    "no_venv_committed",
    "no_dependency_changes",
    "no_docker_changes",
    "no_docker_rebuild",
    "no_classify_calls",
    "legacy_musicnn_remains_baseline",
    "fixture_status",
    "fixture_count",
    "provenance_status",
    "license_status",
    "usage_permission",
    "sanitized_fixtures",
    "baseline_runtime_strategy",
    "baseline_capture_readiness",
    "container_strategy",
    "decision_status",
    "blockers",
    "next_step_recommendation",
)

REQUIRED_MUSICNN_ONNX_FIXTURE_PLACEMENT_SANITIZED_FIELDS = (
    "fixture_id",
    "sha256",
    "file_size_bytes",
    "audio_format",
    "source_artist",
    "license_status",
    "usage_permission",
)

REQUIRED_MUSICNN_LEGACY_BASELINE_CAPTURE_FIELDS = (
    "report_type",
    "roadmap",
    "not_production_decision",
    "approved_for_production",
    "approved_for_provider_implementation",
    "approved_for_default_provider_switch",
    "approved_for_full_numeric_parity_run",
    "approved_for_onnx_execution",
    "baseline_capture_scope",
    "selected_fixture_visibility_strategy",
    "import_policy",
    "no_audio_files_committed",
    "no_model_files_committed",
    "no_venv_committed",
    "no_dependency_changes",
    "no_dockerfile_changes",
    "no_compose_file_changes",
    "no_docker_rebuild",
    "no_classify_calls",
    "no_onnx_execution",
    "no_tensorflow_vs_onnx_comparison",
    "legacy_musicnn_remains_baseline",
    "fixture_count",
    "sanitized_fixtures",
    "container_execution",
    "baseline_capture_succeeded",
    "baseline_capture_status",
    "baseline_outputs",
    "blockers",
    "next_step_recommendation",
)

LEGACY_MUSICNN_BASELINE_CAPTURE_REPORT_OPTIONAL_TRUE_FIELDS = (
    "no_audio_files_committed",
    "no_model_files_committed",
    "no_venv_committed",
    "no_dependency_changes",
    "no_dockerfile_changes",
    "no_compose_file_changes",
    "no_docker_rebuild",
    "no_classify_calls",
    "no_onnx_execution",
    "no_tensorflow_vs_onnx_comparison",
    "legacy_musicnn_remains_baseline",
)

REQUIRED_MUSICNN_LEGACY_BASELINE_SANITIZED_FIXTURE_FIELDS = (
    "fixture_id",
    "sha256",
    "audio_format",
    "source_artist",
    "license_status",
)

REQUIRED_MUSICNN_ONNX_FIXTURE_VISIBILITY_STRATEGY_FIELDS = (
    "report_type",
    "roadmap",
    "not_production_decision",
    "approved_for_production",
    "approved_for_provider_implementation",
    "approved_for_default_provider_switch",
    "approved_for_full_numeric_parity_run",
    "approved_for_onnx_execution",
    "approved_for_baseline_capture_execution",
    "approved_for_future_scoped_baseline_capture_with_selected_strategy",
    "no_audio_files_committed",
    "no_model_files_committed",
    "no_venv_committed",
    "no_dependency_changes",
    "no_dockerfile_changes",
    "no_compose_file_changes",
    "no_docker_rebuild",
    "no_classify_calls",
    "legacy_musicnn_remains_baseline",
    "fixture_source",
    "current_blocker",
    "evaluated_strategies",
    "selected_strategy",
    "selected_strategy_status",
    "strategy_rationale",
    "execution_boundaries",
    "blockers",
    "next_step_recommendation",
)

MUSICNN_ONNX_FIXTURE_VISIBILITY_STRATEGIES = {
    "one_off_compose_run_bind_mount",
    "temporary_local_override_not_committed",
    "docker_cp_to_container_temp_path",
    "existing_mounted_path",
}

MUSICNN_ONNX_FIXTURE_VISIBILITY_CURRENT_BLOCKERS = {
    "FIXTURE_PATH_NOT_AVAILABLE_IN_CONTAINER",
    "BASELINE_CAPTURE_BLOCKED_BY_CONTAINER_MOUNT",
}

REQUIRED_SCOPED_BASELINE_SAFETY_CONFIRMATIONS = (
    "numeric_parity_not_run",
    "tensorflow_model_execution_not_run",
    "onnx_model_execution_not_run",
    "classify_endpoint_not_called",
    "production_dependency_files_unchanged",
    "docker_files_unchanged",
    "provider_factory_unchanged",
    "default_provider_unchanged",
    "response_shape_unchanged",
    "cache_logic_unchanged",
    "tidal_parser_untouched",
    "audio_files_not_committed",
    "model_files_not_committed",
    "venv_not_committed",
    "release_or_tag_not_created",
)

REQUIRED_MUSICNN_ONNX_DECISION_GATE_FIELDS = (
    "report_type",
    "roadmap",
    "not_production_decision",
    "approved_for_production",
    "approved_for_provider_implementation",
    "approved_for_default_provider_switch",
    "approved_for_numeric_parity_run",
    "no_audio_files_committed",
    "no_model_files_committed",
    "no_venv_committed",
    "no_dependency_changes",
    "no_docker_changes",
    "no_classify_calls",
    "legacy_musicnn_remains_baseline",
    "fixture_status",
    "fixture_count",
    "sanitized_fixtures",
    "baseline_runtime_status",
    "tensorflow_available",
    "essentia_available",
    "onnxruntime_available",
    "decision_status",
    "blockers",
    "next_step_recommendation",
)

REQUIRED_SANITIZED_FIXTURE_FIELDS = (
    "fixture_id",
    "format",
    "file_size_bytes",
    "sha256",
)

MANIFEST_MARKERS = (
    'schema_version: "0.1"',
    'artifact_type: "example_manifest_skeleton"',
    'manifest_id: "example_lightweight_eval_manifest_v0_1"',
    "fixtures:",
    'category: "clear_mainstream_genres"',
    'category: "negative_edge_fixtures"',
)

REPORT_MARKERS = (
    "# Example Lightweight Evaluation Report",
    "Status: example skeleton only",
    "## Production Contract",
    "`legacy_musicnn` remains the production baseline and default provider.",
    "## Approval Gate Status",
)

REQUIRED_REPORT_MARKERS = (
    "summary",
    "scope",
    "baseline provider",
    "candidate provider",
    "manifest",
    "fixture coverage",
    "aggregate comparison",
    "controlled vocabulary results",
    "oov results",
    "top-n overlap",
    "resource metrics",
    "failures and warnings",
    "known gaps",
    "decision",
    "approval gate status",
    "appendix",
    "per-fixture results",
)

KNOWN_WARNING_CATEGORIES = (
    "fixture_missing",
    "fixture_unreadable",
    "baseline_failed",
    "candidate_failed",
    "empty_output",
    "oov_terms_detected",
    "major_genre_shift",
    "license_unknown",
    "model_provenance_unknown",
    "runtime_metric_missing",
    "comparison_incomplete",
)

README_MARKERS = (
    "# Lightweight Evaluation Artifacts",
    "The `/classify` contract is unchanged.",
    "- `ok`",
    "- `message`",
    "- `genres`",
    "- `genres_pretty`",
)


class ValidationError(Exception):
    """Raised when an artifact does not match the expected example shape."""


class ValidationSummary(NamedTuple):
    files_checked: int
    json_outputs_checked: int
    fixture_results_checked: int
    model_provenance_checked: int = 0
    local_artifact_metadata_checked: int = 0
    local_artifact_evidence_reports_checked: int = 0
    real_local_artifact_evidence_reports_checked: int = 0
    parity_scaffold_dry_run_outputs_checked: int = 0
    musicnn_onnx_parity_spike_reports_checked: int = 0
    musicnn_onnx_parity_environment_preparation_reports_checked: int = 0
    musicnn_onnx_fixtures_and_baseline_runtime_decision_reports_checked: int = 0
    musicnn_onnx_fixture_set_and_baseline_runtime_strategy_reports_checked: int = 0
    musicnn_onnx_fixtures_and_scoped_baseline_capture_approval_reports_checked: int = 0
    musicnn_onnx_fixture_placement_and_scoped_baseline_readiness_reports_checked: int = 0
    musicnn_legacy_baseline_capture_reports_checked: int = 0
    musicnn_onnx_preprocessing_alignment_reports_checked: int = 0
    musicnn_onnx_pragmatic_preprocessing_prototype_reports_checked: int = 0
    musicnn_tensorflow_input_musiccnn_availability_probe_reports_checked: int = 0
    musicnn_onnx_output_capture_reports_checked: int = 0
    musicnn_onnx_fixture_visibility_strategy_reports_checked: int = 0
    musicnn_legacy_baseline_import_order_diagnostic_reports_checked: int = 0
    label_mapping_checked: int = 0
    evidence_packages_checked: int = 0
    fixture_manifest_templates_checked: int = 0


class GenreOverlapSummary(NamedTuple):
    baseline_count: int
    candidate_count: int
    overlap_count: int
    overlap_ratio: float
    baseline_empty: bool
    candidate_empty: bool


def _read_non_empty_text(path: Path) -> str:
    if not path.exists():
        raise ValidationError(f"Missing required artifact: {path}")
    if not path.is_file():
        raise ValidationError(f"Required artifact is not a file: {path}")

    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValidationError(f"Required artifact is empty: {path}")
    return text


def _validate_markers(path: Path, text: str, markers: Iterable[str]) -> None:
    for marker in markers:
        if marker not in text:
            raise ValidationError(f"Missing marker in {path}: {marker!r}")


def _normalize_report_text(text: str) -> str:
    return " ".join(text.casefold().split())


def _validate_normalized_report_markers(path: Path, text: str, markers: Iterable[str]) -> None:
    normalized_text = _normalize_report_text(text)
    for marker in markers:
        normalized_marker = _normalize_report_text(marker)
        if normalized_marker not in normalized_text:
            raise ValidationError(f"Missing report section or marker in {path}: {marker!r}")


def _validate_report(path: Path) -> None:
    text = _read_non_empty_text(path)
    _validate_markers(path, text, REPORT_MARKERS)
    _validate_normalized_report_markers(path, text, REQUIRED_REPORT_MARKERS)
    _validate_normalized_report_markers(path, text, KNOWN_WARNING_CATEGORIES)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(_read_non_empty_text(path))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(value, dict):
        raise ValidationError(f"JSON artifact must be an object: {path}")
    return value


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_warnings(value: dict[str, Any], context: str) -> None:
    if "warnings" not in value:
        return

    warnings = value["warnings"]
    if not isinstance(warnings, list):
        raise ValidationError(f"{context}.warnings must be a list when present")

    for index, item in enumerate(warnings):
        item_context = f"{context}.warnings[{index}]"
        if isinstance(item, str):
            continue
        if not isinstance(item, dict):
            raise ValidationError(f"{item_context} must be a string or object")

        category = item.get("category")
        if category is not None and (not isinstance(category, str) or not category.strip()):
            raise ValidationError(f"{item_context}.category must be a non-empty string when present")


def _validate_classify_response_shape(value: dict[str, Any], context: str) -> None:
    required_fields = ("ok", "message", "genres", "genres_pretty")
    for field in required_fields:
        if field not in value:
            raise ValidationError(f"{context} is missing required field: {field}")

    if not isinstance(value["ok"], bool):
        raise ValidationError(f"{context}.ok must be a bool")
    if not isinstance(value["message"], str):
        raise ValidationError(f"{context}.message must be a string")
    if not isinstance(value["genres"], list):
        raise ValidationError(f"{context}.genres must be a list")
    if not isinstance(value["genres_pretty"], list):
        raise ValidationError(f"{context}.genres_pretty must be a list")

    for index, item in enumerate(value["genres_pretty"]):
        if not isinstance(item, str):
            raise ValidationError(f"{context}.genres_pretty[{index}] must be a string")

    for index, item in enumerate(value["genres"]):
        item_context = f"{context}.genres[{index}]"
        if not isinstance(item, dict):
            raise ValidationError(f"{item_context} must be an object")
        for field in ("tag", "prob"):
            if field not in item:
                raise ValidationError(f"{item_context} is missing required field: {field}")

        tag = item["tag"]
        if not isinstance(tag, str) or not tag.strip():
            raise ValidationError(f"{item_context}.tag must be a non-empty string")

        prob = item["prob"]
        if not _is_number(prob):
            raise ValidationError(f"{item_context}.prob must be an int or float")
        if not 0 <= prob <= 1:
            raise ValidationError(f"{item_context}.prob must be in range 0..1")

    _validate_warnings(value, context)


def _validate_output(path: Path) -> int:
    data = _load_json(path)
    _validate_warnings(data, str(path))

    fixture_results = data.get("fixture_results")
    if not isinstance(fixture_results, list) or not fixture_results:
        raise ValidationError(f"{path}.fixture_results must be a non-empty list")

    for index, result in enumerate(fixture_results):
        if not isinstance(result, dict):
            raise ValidationError(f"{path}.fixture_results[{index}] must be an object")
        _validate_classify_response_shape(result, f"{path}.fixture_results[{index}]")

    return len(fixture_results)


def _validate_model_provenance(path: Path) -> None:
    data = _load_json(path)

    for field in REQUIRED_MODEL_PROVENANCE_FIELDS:
        if field not in data:
            raise ValidationError(f"{path} is missing required provenance field: {field}")

    for field in MODEL_PROVENANCE_STRING_FIELDS:
        value = data[field]
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{path}.{field} must be a non-empty string")

    if data["model_format"] != "onnx":
        raise ValidationError(f'{path}.model_format must be "onnx"')

    for field in ("input_names", "output_names", "known_limitations", "warnings"):
        if not isinstance(data[field], list):
            raise ValidationError(f"{path}.{field} must be a list")

    for field in ("input_shapes", "output_shapes"):
        value = data[field]
        if not isinstance(value, list):
            raise ValidationError(f"{path}.{field} must be a list")
        for index, item in enumerate(value):
            if not isinstance(item, list):
                raise ValidationError(f"{path}.{field}[{index}] must be a list")

    for field in ("model_file_size_bytes", "label_count"):
        value = data[field]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValidationError(f"{path}.{field} must be a non-negative integer")

    _validate_warnings(data, str(path))

    approval_status = data["approval_status"].strip().casefold()
    if approval_status in PRODUCTION_APPROVED_STATUSES:
        raise ValidationError(f"{path}.approval_status must not be production-approved")


def _validate_required_list_container(data: dict[str, Any], path: Path, field: str) -> None:
    if field not in data:
        raise ValidationError(f"{path} is missing required local artifact metadata field: {field}")
    if not isinstance(data[field], list):
        raise ValidationError(f"{path}.{field} must be a list")


def _is_fake_or_placeholder_hash(value: str) -> bool:
    normalized = value.strip().casefold()
    if normalized in LOCAL_ARTIFACT_PLACEHOLDER_HASHES:
        return True
    if any(marker in normalized for marker in LOCAL_ARTIFACT_PLACEHOLDER_HASHES - {"0" * 64}):
        return True
    if len(normalized) >= 32 and set(normalized) == {"0"}:
        return True
    return False


def _validate_sha256(value: Any, context: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValidationError(f"{context} must be a 64-character lowercase hex string")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValidationError(f"{context} must be a 64-character lowercase hex string")
    if _is_fake_or_placeholder_hash(value):
        raise ValidationError(f"{context} must not be a fake placeholder hash")
    return value


def _validate_positive_integer(value: Any, context: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValidationError(f"{context} must be a positive integer")


def _iter_text_values(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str):
                yield key
            yield from _iter_text_values(item)
        return
    if isinstance(value, list):
        for item in value:
            yield from _iter_text_values(item)


def _joined_normalized_text(value: Any) -> str:
    return _normalize_report_text(" ".join(_iter_text_values(value)))


def _has_true_key(value: Any, key_name: str) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == key_name and item is True:
                return True
            if _has_true_key(item, key_name):
                return True
    if isinstance(value, list):
        return any(_has_true_key(item, key_name) for item in value)
    return False


def _validate_no_parity_or_runtime_approval_claims(data: dict[str, Any], path: Path) -> None:
    text = _joined_normalized_text(data)
    dangerous_phrases = (
        "model parity proven",
        "numeric parity approved",
        "numeric parity is approved",
        "numeric parity confirmed",
        "numeric parity passed",
        "claims numeric parity",
        "final genres parity approved",
        "final genres parity confirmed",
        "genres_pretty parity approved",
        "genres_pretty parity confirmed",
        "parity evidence approved",
        "parity proven",
        "parity confirmed",
        "approved for inference",
        "inference is approved",
        "onnxruntime approved",
        "onnx runtime approved",
        "provider implementation approved",
        "production migration approved",
        "default provider switch approved",
    )
    for phrase in dangerous_phrases:
        if phrase in text:
            raise ValidationError(f"{path} must not claim parity/inference/runtime/production approval: {phrase!r}")


def _require_bool_value(value: Any, expected: bool, context: str) -> None:
    if value is not expected:
        expected_text = str(expected).lower()
        raise ValidationError(f"{context} must be {expected_text}")


def _validate_required_object(data: dict[str, Any], path: Path, field: str) -> dict[str, Any]:
    value = data.get(field)
    if not isinstance(value, dict):
        raise ValidationError(f"{path}.{field} must be an object")
    return value


def _validate_required_non_empty_list(data: dict[str, Any], path: Path, field: str) -> None:
    value = data.get(field)
    if not isinstance(value, list) or not value:
        raise ValidationError(f"{path}.{field} must be a non-empty list")


def _validate_required_list(data: dict[str, Any], path: Path, field: str) -> None:
    value = data.get(field)
    if not isinstance(value, list):
        raise ValidationError(f"{path}.{field} must be a list")


def _collect_blocker_codes(blockers: list[Any], allowed_codes: set[str], context: str) -> set[str]:
    blocker_codes: set[str] = set()
    for index, blocker in enumerate(blockers):
        item_context = f"{context}[{index}]"
        if not isinstance(blocker, dict):
            raise ValidationError(f"{item_context} must be an object")
        code = blocker.get("code")
        message = blocker.get("message")
        if code not in allowed_codes:
            raise ValidationError(f"{item_context}.code is not allowed: {code!r}")
        if not isinstance(message, str) or not message.strip():
            raise ValidationError(f"{item_context}.message must be a non-empty string")
        blocker_codes.add(code)
    return blocker_codes


def _validate_parity_scaffold_dry_run_output(path: Path) -> None:
    data = _load_json(path)

    if data.get("artifact_type") != "scaffold_dry_run_output":
        raise ValidationError(f'{path}.artifact_type must be "scaffold_dry_run_output"')
    _require_bool_value(data.get("not_production_decision"), True, f"{path}.not_production_decision")
    _require_bool_value(data.get("approved_for_inference"), False, f"{path}.approved_for_inference")
    _require_bool_value(data.get("approved_for_production"), False, f"{path}.approved_for_production")

    generated_from = data.get("generated_from")
    if generated_from != "scripts/lightweight/musicnn_onnx_parity_scaffold.py":
        raise ValidationError(f"{path}.generated_from must reference the scaffold script")
    command = data.get("command")
    if command != "python3 scripts/lightweight/musicnn_onnx_parity_scaffold.py --mode dry-run":
        raise ValidationError(f"{path}.command must record the dry-run scaffold command")

    scaffold_output = _validate_required_object(data, path, "scaffold_output")
    _require_bool_value(scaffold_output.get("ok"), True, f"{path}.scaffold_output.ok")
    if scaffold_output.get("mode") != "dry-run":
        raise ValidationError(f'{path}.scaffold_output.mode must be "dry-run"')

    for field in ("scaffold_type", "evidence_report_path", "next_step_recommendation"):
        value = scaffold_output.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{path}.scaffold_output.{field} must be a non-empty string")

    for field in (
        "inference_attempted",
        "onnxruntime_imported",
        "tensorflow_imported",
        "essentia_imported",
        "classify_called",
        "provider_imported",
        "production_runtime_touched",
    ):
        _require_bool_value(scaffold_output.get(field), False, f"{path}.scaffold_output.{field}")

    _validate_required_non_empty_list(scaffold_output, path / "scaffold_output", "checks")
    _validate_required_list(scaffold_output, path / "scaffold_output", "warnings")
    _validate_required_list(scaffold_output, path / "scaffold_output", "no_go_items")

    for index, check in enumerate(scaffold_output["checks"]):
        context = f"{path}.scaffold_output.checks[{index}]"
        if not isinstance(check, dict):
            raise ValidationError(f"{context} must be an object")
        if not isinstance(check.get("name"), str) or not check["name"].strip():
            raise ValidationError(f"{context}.name must be a non-empty string")
        if check.get("ok") is not True:
            raise ValidationError(f"{context}.ok must be true in a committed successful dry-run artifact")

    _validate_no_inference_or_production_approval_claims(data, str(path))
    _validate_no_parity_or_runtime_approval_claims(data, path)


def _validate_nullable_metric(data: dict[str, Any], path: Path, field: str) -> None:
    value = data[field]
    if value is None:
        return
    if not _is_number(value):
        raise ValidationError(f"{path}.{field} must be null or numeric")


def _validate_musicnn_onnx_parity_spike_report(path: Path) -> None:
    data = _load_json(path)

    for field in REQUIRED_MUSICNN_ONNX_PARITY_SPIKE_FIELDS:
        if field not in data:
            raise ValidationError(f"{path} is missing required Roadmap 4.40 parity spike field: {field}")

    if data["roadmap"] != "4.40":
        raise ValidationError(f'{path}.roadmap must be "4.40"')
    if data["report_type"] != MUSICNN_ONNX_PARITY_SPIKE_REPORT_TYPE:
        raise ValidationError(f'{path}.report_type must be "{MUSICNN_ONNX_PARITY_SPIKE_REPORT_TYPE}"')
    if data["generated_by"] != "scripts/lightweight/musicnn_onnx_parity_scaffold.py":
        raise ValidationError(f"{path}.generated_by must reference the local-only scaffold")

    expected_false_flags = (
        "approved_for_production",
        "approved_for_provider_implementation",
        "approved_for_default_provider_switch",
        "approved_for_inference_beyond_local_spike",
        "onnxruntime_added_to_production_requirements",
    )
    for field in expected_false_flags:
        _require_bool_value(data[field], False, f"{path}.{field}")

    expected_true_flags = (
        "not_production_decision",
        "legacy_musicnn_remains_baseline",
        "default_provider_unchanged",
        "classify_contract_unchanged",
        "response_shape_unchanged",
        "no_audio_files_committed",
        "no_model_files_committed",
        "no_dependency_changes",
        "no_docker_changes",
        "no_provider_factory_changes",
        "no_default_provider_changes",
        "no_classify_calls",
        "tidal_parser_untouched",
    )
    for field in expected_true_flags:
        _require_bool_value(data[field], True, f"{path}.{field}")

    fixture_count = data["fixture_count"]
    if not isinstance(fixture_count, int) or isinstance(fixture_count, bool) or fixture_count < 0:
        raise ValidationError(f"{path}.fixture_count must be a non-negative integer")

    for field in (
        "baseline_runtime_available",
        "onnx_runtime_available",
        "model_artifacts_available",
        "fixtures_available",
        "baseline_capture_attempted",
        "onnx_capture_attempted",
        "parity_run_executed",
    ):
        if not isinstance(data[field], bool):
            raise ValidationError(f"{path}.{field} must be a bool")

    if data["decision_status"] not in MUSICNN_ONNX_PARITY_SPIKE_DECISION_STATUSES:
        raise ValidationError(f"{path}.decision_status is not allowed: {data['decision_status']!r}")

    metrics = data["metrics"]
    if not isinstance(metrics, dict):
        raise ValidationError(f"{path}.metrics must be an object")
    required_metric_fields = (
        "fixture_count",
        "baseline_runtime_available",
        "onnx_runtime_available",
        "baseline_output_shape",
        "onnx_output_shape",
        "output_shape_match",
        "max_abs_diff",
        "mean_abs_diff",
        "top_1_match",
        "top_3_overlap",
        "top_5_overlap",
        "preprocessing_alignment_status",
    )
    for field in required_metric_fields:
        if field not in metrics:
            raise ValidationError(f"{path}.metrics is missing required field: {field}")
    if metrics["fixture_count"] != data["fixture_count"]:
        raise ValidationError(f"{path}.metrics.fixture_count must match top-level fixture_count")
    if metrics["baseline_runtime_available"] != data["baseline_runtime_available"]:
        raise ValidationError(f"{path}.metrics.baseline_runtime_available must match top-level value")
    if metrics["onnx_runtime_available"] != data["onnx_runtime_available"]:
        raise ValidationError(f"{path}.metrics.onnx_runtime_available must match top-level value")

    blockers = data["blockers"]
    if not isinstance(blockers, list):
        raise ValidationError(f"{path}.blockers must be a list")
    for index, blocker in enumerate(blockers):
        context = f"{path}.blockers[{index}]"
        if not isinstance(blocker, dict):
            raise ValidationError(f"{context} must be an object")
        for field in ("code", "message"):
            value = blocker.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValidationError(f"{context}.{field} must be a non-empty string")

    if data["decision_status"] in MUSICNN_ONNX_PARITY_SPIKE_BLOCKED_STATUSES:
        if not blockers:
            raise ValidationError(f"{path}.blockers must be non-empty when decision_status is blocked")
        if data["parity_run_executed"] is not False:
            raise ValidationError(f"{path}.parity_run_executed must be false when blocked")
        if not isinstance(data.get("metrics_unavailable_reason"), str) or not data["metrics_unavailable_reason"].strip():
            raise ValidationError(f"{path}.metrics_unavailable_reason must explain why metrics are unavailable")
        for field in (
            "baseline_output_shape",
            "onnx_output_shape",
            "output_shape_match",
            "max_abs_diff",
            "mean_abs_diff",
            "top_1_match",
            "top_3_overlap",
            "top_5_overlap",
        ):
            if metrics[field] is not None:
                raise ValidationError(f"{path}.metrics.{field} must be null in a blocked report")

    for field in ("max_abs_diff", "mean_abs_diff", "top_3_overlap", "top_5_overlap"):
        value = metrics[field]
        if value is not None and not _is_number(value):
            raise ValidationError(f"{path}.metrics.{field} must be null or numeric")

    for field in ("baseline_output_shape", "onnx_output_shape"):
        value = metrics[field]
        if value is not None and not isinstance(value, list):
            raise ValidationError(f"{path}.metrics.{field} must be null or a list")

    for field in ("output_shape_match", "top_1_match"):
        value = metrics[field]
        if value is not None and not isinstance(value, bool):
            raise ValidationError(f"{path}.metrics.{field} must be null or a bool")

    if (
        not isinstance(metrics["preprocessing_alignment_status"], str)
        or not metrics["preprocessing_alignment_status"].strip()
    ):
        raise ValidationError(f"{path}.metrics.preprocessing_alignment_status must be a non-empty string")

    _validate_required_list_container(data, path, "warnings")
    _validate_warnings(data, str(path))
    _validate_no_inference_or_production_approval_claims(data, str(path))
    _validate_no_parity_or_runtime_approval_claims(data, path)


def _validate_musicnn_onnx_parity_environment_preparation_report(path: Path) -> None:
    data = _load_json(path)

    for field in REQUIRED_MUSICNN_ONNX_PARITY_ENVIRONMENT_PREPARATION_FIELDS:
        if field not in data:
            raise ValidationError(f"{path} is missing required Roadmap 4.41 environment field: {field}")

    if data["roadmap"] != "4.41":
        raise ValidationError(f'{path}.roadmap must be "4.41"')
    if data["report_type"] != MUSICNN_ONNX_PARITY_ENVIRONMENT_PREPARATION_REPORT_TYPE:
        raise ValidationError(
            f'{path}.report_type must be "{MUSICNN_ONNX_PARITY_ENVIRONMENT_PREPARATION_REPORT_TYPE}"'
        )

    for field in (
        "approved_for_production",
        "approved_for_provider_implementation",
        "approved_for_default_provider_switch",
        "approved_for_inference_beyond_local_spike",
    ):
        _require_bool_value(data[field], False, f"{path}.{field}")

    for field in (
        "not_production_decision",
        "no_audio_files_committed",
        "no_model_files_committed",
        "no_venv_committed",
        "no_dependency_changes",
        "no_docker_changes",
        "no_classify_calls",
        "legacy_musicnn_remains_baseline",
    ):
        _require_bool_value(data[field], True, f"{path}.{field}")

    status = data["environment_status"]
    if status not in MUSICNN_ONNX_PARITY_ENVIRONMENT_STATUSES:
        raise ValidationError(f"{path}.environment_status is not allowed: {status!r}")

    prerequisites = _validate_required_object(data, path, "prerequisites")
    for field in REQUIRED_MUSICNN_ONNX_PARITY_ENVIRONMENT_PREREQUISITES:
        if field not in prerequisites:
            raise ValidationError(f"{path}.prerequisites is missing required field: {field}")
    for field in REQUIRED_MUSICNN_ONNX_PARITY_ENVIRONMENT_PREREQUISITES:
        if field == "fixture_count":
            continue
        if not isinstance(prerequisites[field], bool):
            raise ValidationError(f"{path}.prerequisites.{field} must be a bool")
    fixture_count = prerequisites["fixture_count"]
    if not isinstance(fixture_count, int) or isinstance(fixture_count, bool) or fixture_count < 0:
        raise ValidationError(f"{path}.prerequisites.fixture_count must be a non-negative integer")

    blockers = data["blockers"]
    if not isinstance(blockers, list):
        raise ValidationError(f"{path}.blockers must be a list")
    blocker_codes: set[str] = set()
    for index, blocker in enumerate(blockers):
        context = f"{path}.blockers[{index}]"
        if not isinstance(blocker, dict):
            raise ValidationError(f"{context} must be an object")
        code = blocker.get("code")
        message = blocker.get("message")
        if code not in MUSICNN_ONNX_PARITY_ENVIRONMENT_BLOCKERS:
            raise ValidationError(f"{context}.code is not allowed: {code!r}")
        if not isinstance(message, str) or not message.strip():
            raise ValidationError(f"{context}.message must be a non-empty string")
        blocker_codes.add(code)

    if status == "ready_for_local_parity_run":
        for field in (
            "model_artifacts_available",
            "onnxruntime_available",
            "tensorflow_available",
            "essentia_available",
            "baseline_runtime_available",
        ):
            _require_bool_value(prerequisites[field], True, f"{path}.prerequisites.{field}")
        if fixture_count <= 0:
            raise ValidationError(f"{path}.prerequisites.fixture_count must be positive when ready")
    elif status == "blocked":
        if "MODEL_ARTIFACTS_MISSING" not in blocker_codes and "LOCAL_ENV_NOT_CREATED" not in blocker_codes:
            raise ValidationError(f"{path}.blockers must explain blocked status")
    elif not blockers:
        raise ValidationError(f"{path}.blockers must be non-empty when partially_ready")

    sanitized_locations = data.get("sanitized_locations")
    if sanitized_locations is not None:
        if not isinstance(sanitized_locations, dict):
            raise ValidationError(f"{path}.sanitized_locations must be an object")
        if sanitized_locations.get("full_local_paths_published") is not False:
            raise ValidationError(f"{path}.sanitized_locations.full_local_paths_published must be false")

    serialized = json.dumps(data)
    for forbidden_path in ("/tmp/music-tools-onnx-parity", "/opt/music-tools"):
        if forbidden_path in serialized:
            raise ValidationError(f"{path} must not publish private full local path: {forbidden_path}")

    if data.get("parity_run_executed") is not None:
        _require_bool_value(data["parity_run_executed"], False, f"{path}.parity_run_executed")
    if data.get("metrics_simulated") is not None:
        _require_bool_value(data["metrics_simulated"], False, f"{path}.metrics_simulated")

    _validate_required_list_container(data, path, "warnings")
    _validate_warnings(data, str(path))
    _validate_no_inference_or_production_approval_claims(data, str(path))
    _validate_no_parity_or_runtime_approval_claims(data, path)


def _validate_musicnn_onnx_fixtures_and_baseline_runtime_decision_report(
    path: Path,
    *,
    expected_roadmap: str = "4.42",
    expected_report_type: str = MUSICNN_ONNX_FIXTURES_AND_BASELINE_RUNTIME_DECISION_REPORT_TYPE,
    require_baseline_strategy: bool = False,
) -> None:
    data = _load_json(path)

    for field in REQUIRED_MUSICNN_ONNX_DECISION_GATE_FIELDS:
        if field not in data:
            raise ValidationError(f"{path} is missing required Roadmap decision gate field: {field}")

    if require_baseline_strategy and "baseline_runtime_strategy" not in data:
        raise ValidationError(f"{path} is missing required Roadmap 4.43 field: baseline_runtime_strategy")

    if data["roadmap"] != expected_roadmap:
        raise ValidationError(f'{path}.roadmap must be "{expected_roadmap}"')
    if data["report_type"] != expected_report_type:
        raise ValidationError(f'{path}.report_type must be "{expected_report_type}"')

    for field in (
        "approved_for_production",
        "approved_for_provider_implementation",
        "approved_for_default_provider_switch",
        "approved_for_numeric_parity_run",
    ):
        _require_bool_value(data[field], False, f"{path}.{field}")

    for field in (
        "not_production_decision",
        "no_audio_files_committed",
        "no_model_files_committed",
        "no_venv_committed",
        "no_dependency_changes",
        "no_docker_changes",
        "no_classify_calls",
        "legacy_musicnn_remains_baseline",
    ):
        _require_bool_value(data[field], True, f"{path}.{field}")

    fixture_status = data["fixture_status"]
    if fixture_status not in MUSICNN_ONNX_FIXTURE_STATUSES:
        raise ValidationError(f"{path}.fixture_status is not allowed: {fixture_status!r}")

    baseline_status = data["baseline_runtime_status"]
    if baseline_status not in MUSICNN_ONNX_BASELINE_RUNTIME_STATUSES:
        raise ValidationError(f"{path}.baseline_runtime_status is not allowed: {baseline_status!r}")

    if require_baseline_strategy:
        baseline_strategy = data["baseline_runtime_strategy"]
        if baseline_strategy not in {
            "local_service_env",
            "existing_container_local_only",
            "isolated_baseline_env",
            "unavailable",
        }:
            raise ValidationError(f"{path}.baseline_runtime_strategy is not allowed: {baseline_strategy!r}")

    decision_status = data["decision_status"]
    if decision_status not in MUSICNN_ONNX_DECISION_GATE_STATUSES:
        raise ValidationError(f"{path}.decision_status is not allowed: {decision_status!r}")

    fixture_count = data["fixture_count"]
    if not isinstance(fixture_count, int) or isinstance(fixture_count, bool) or fixture_count < 0:
        raise ValidationError(f"{path}.fixture_count must be a non-negative integer")

    for field in ("tensorflow_available", "essentia_available", "onnxruntime_available"):
        if not isinstance(data[field], bool):
            raise ValidationError(f"{path}.{field} must be a bool")

    sanitized_fixtures = data["sanitized_fixtures"]
    if not isinstance(sanitized_fixtures, list):
        raise ValidationError(f"{path}.sanitized_fixtures must be a list")
    if fixture_count != len(sanitized_fixtures):
        raise ValidationError(f"{path}.fixture_count must match sanitized_fixtures length")

    for index, fixture in enumerate(sanitized_fixtures):
        context = f"{path}.sanitized_fixtures[{index}]"
        if not isinstance(fixture, dict):
            raise ValidationError(f"{context} must be an object")
        for field in REQUIRED_SANITIZED_FIXTURE_FIELDS:
            if field not in fixture:
                raise ValidationError(f"{context} is missing required field: {field}")
        fixture_id = fixture["fixture_id"]
        if not isinstance(fixture_id, str) or not fixture_id.strip():
            raise ValidationError(f"{context}.fixture_id must be a non-empty string")
        if "/" in fixture_id or "\\" in fixture_id:
            raise ValidationError(f"{context}.fixture_id must not contain path separators")
        audio_format = fixture["format"]
        if not isinstance(audio_format, str) or not audio_format.strip():
            raise ValidationError(f"{context}.format must be a non-empty string")
        _validate_positive_integer(fixture["file_size_bytes"], f"{context}.file_size_bytes")
        _validate_sha256(fixture["sha256"], f"{context}.sha256")
        duration = fixture.get("duration_seconds")
        if duration is not None and (not _is_number(duration) or duration <= 0):
            raise ValidationError(f"{context}.duration_seconds must be null, absent, or a positive number")
        category = fixture.get("category")
        if category is not None and (not isinstance(category, str) or not category.strip()):
            raise ValidationError(f"{context}.category must be a non-empty string when present")

    blockers = data["blockers"]
    if not isinstance(blockers, list):
        raise ValidationError(f"{path}.blockers must be a list")
    blocker_codes: set[str] = set()
    for index, blocker in enumerate(blockers):
        context = f"{path}.blockers[{index}]"
        if not isinstance(blocker, dict):
            raise ValidationError(f"{context} must be an object")
        code = blocker.get("code")
        message = blocker.get("message")
        if code not in MUSICNN_ONNX_DECISION_GATE_BLOCKERS:
            raise ValidationError(f"{context}.code is not allowed: {code!r}")
        if not isinstance(message, str) or not message.strip():
            raise ValidationError(f"{context}.message must be a non-empty string")
        blocker_codes.add(code)

    if fixture_status == "available" and fixture_count <= 0:
        raise ValidationError(f"{path}.fixture_count must be positive when fixtures are available")
    if fixture_status == "missing" and "FIXTURE_FILES_MISSING" not in blocker_codes:
        raise ValidationError(f"{path}.blockers must include FIXTURE_FILES_MISSING when fixtures are missing")
    if fixture_status == "unclear_provenance" and "FIXTURE_PROVENANCE_UNCLEAR" not in blocker_codes:
        raise ValidationError(f"{path}.blockers must include FIXTURE_PROVENANCE_UNCLEAR when provenance is unclear")

    if baseline_status == "available":
        _require_bool_value(data["tensorflow_available"], True, f"{path}.tensorflow_available")
        _require_bool_value(data["essentia_available"], True, f"{path}.essentia_available")
    elif (
        "BASELINE_RUNTIME_UNAVAILABLE" not in blocker_codes
        and "BASELINE_CONTAINER_STRATEGY_SELECTED" not in blocker_codes
        and baseline_status in {"unavailable", "container_only_candidate", "container_strategy_candidate"}
    ):
        raise ValidationError(f"{path}.blockers must explain unavailable baseline runtime")

    if decision_status == "ready_for_numeric_parity_run":
        if blockers:
            raise ValidationError(f"{path}.blockers must be empty when ready_for_numeric_parity_run")
        if fixture_status != "available" or baseline_status != "available":
            raise ValidationError(f"{path}.decision_status cannot be ready without fixtures and baseline runtime")
    else:
        if not blockers:
            raise ValidationError(f"{path}.blockers must be non-empty when decision_status is blocked")
        if "NUMERIC_PARITY_NOT_APPROVED" not in blocker_codes:
            raise ValidationError(f"{path}.blockers must include NUMERIC_PARITY_NOT_APPROVED when blocked")

    sanitized_locations = data.get("sanitized_locations")
    if sanitized_locations is not None:
        if not isinstance(sanitized_locations, dict):
            raise ValidationError(f"{path}.sanitized_locations must be an object")
        if sanitized_locations.get("full_local_paths_published") is not False:
            raise ValidationError(f"{path}.sanitized_locations.full_local_paths_published must be false")

    serialized = json.dumps(data)
    for forbidden_path in ("/tmp/music-tools-onnx-parity", "/opt/music-tools"):
        if forbidden_path in serialized:
            raise ValidationError(f"{path} must not publish private full local path: {forbidden_path}")

    _validate_no_inference_or_production_approval_claims(data, str(path))
    _validate_no_parity_or_runtime_approval_claims(data, path)


def _validate_musicnn_onnx_fixture_set_and_baseline_runtime_strategy_report(path: Path) -> None:
    _validate_musicnn_onnx_fixtures_and_baseline_runtime_decision_report(
        path,
        expected_roadmap="4.43",
        expected_report_type=MUSICNN_ONNX_FIXTURE_SET_AND_BASELINE_RUNTIME_STRATEGY_REPORT_TYPE,
        require_baseline_strategy=True,
    )


def _validate_musicnn_onnx_fixtures_and_scoped_baseline_capture_approval_report(path: Path) -> None:
    data = _load_json(path)

    for field in REQUIRED_MUSICNN_ONNX_SCOPED_BASELINE_CAPTURE_APPROVAL_FIELDS:
        if field not in data:
            raise ValidationError(f"{path} is missing required Roadmap 4.44 field: {field}")

    if data["roadmap"] != "4.44":
        raise ValidationError(f'{path}.roadmap must be "4.44"')
    if data["report_type"] != MUSICNN_ONNX_FIXTURES_AND_SCOPED_BASELINE_CAPTURE_APPROVAL_REPORT_TYPE:
        raise ValidationError(
            f'{path}.report_type must be "'
            f'{MUSICNN_ONNX_FIXTURES_AND_SCOPED_BASELINE_CAPTURE_APPROVAL_REPORT_TYPE}"'
        )

    for field in (
        "approved_for_production",
        "approved_for_provider_implementation",
        "approved_for_default_provider_switch",
        "approved_for_full_numeric_parity_run",
    ):
        _require_bool_value(data[field], False, f"{path}.{field}")
    _require_bool_value(data["not_production_decision"], True, f"{path}.not_production_decision")

    if not isinstance(data["approved_for_scoped_baseline_capture"], bool):
        raise ValidationError(f"{path}.approved_for_scoped_baseline_capture must be a bool")

    fixture_workspace = _validate_required_object(data, path, "fixture_workspace")
    if fixture_workspace["expected_path_policy"] != "outside_repo_tmp_workspace":
        raise ValidationError(f"{path}.fixture_workspace.expected_path_policy is not allowed")
    if fixture_workspace["sanitized_workspace_label"] != "tmp_music_tools_onnx_parity_fixtures":
        raise ValidationError(f"{path}.fixture_workspace.sanitized_workspace_label is not allowed")
    _require_bool_value(fixture_workspace["path_redacted"], True, f"{path}.fixture_workspace.path_redacted")
    _require_bool_value(fixture_workspace["under_repo"], False, f"{path}.fixture_workspace.under_repo")
    _require_bool_value(
        fixture_workspace["audio_files_committed"], False, f"{path}.fixture_workspace.audio_files_committed"
    )

    fixtures = _validate_required_object(data, path, "fixtures")
    fixture_count = fixtures["fixture_count"]
    if not isinstance(fixture_count, int) or isinstance(fixture_count, bool) or fixture_count < 0:
        raise ValidationError(f"{path}.fixtures.fixture_count must be a non-negative integer")
    fixture_status = fixtures["fixture_status"]
    if fixture_status not in MUSICNN_ONNX_FIXTURE_STATUSES:
        raise ValidationError(f"{path}.fixtures.fixture_status is not allowed: {fixture_status!r}")
    fixture_files = fixtures["files"]
    if not isinstance(fixture_files, list):
        raise ValidationError(f"{path}.fixtures.files must be a list")
    if fixture_count != len(fixture_files):
        raise ValidationError(f"{path}.fixtures.fixture_count must match fixtures.files length")

    fixture_blockers = data["fixture_blockers"]
    if not isinstance(fixture_blockers, list):
        raise ValidationError(f"{path}.fixture_blockers must be a list")
    fixture_blocker_codes = _collect_blocker_codes(
        fixture_blockers,
        MUSICNN_ONNX_SCOPED_BASELINE_CAPTURE_BLOCKERS,
        f"{path}.fixture_blockers",
    )

    baseline_capture = _validate_required_object(data, path, "baseline_capture")
    if baseline_capture["selected_strategy"] != "existing_container_local_only":
        raise ValidationError(f"{path}.baseline_capture.selected_strategy is not allowed")
    if baseline_capture["scope"] != "scoped_baseline_capture_only":
        raise ValidationError(f"{path}.baseline_capture.scope is not allowed")
    for field in (
        "no_classify_calls",
        "no_rebuild",
        "no_compose_file_changes",
        "no_dependency_changes",
        "no_provider_changes",
        "no_default_provider_switch",
        "future_capture_only",
    ):
        _require_bool_value(baseline_capture[field], True, f"{path}.baseline_capture.{field}")

    container_strategy = _validate_required_object(data, path, "container_strategy")
    if container_strategy["compose_directory"] != "/opt/music-tools/genre-classifier":
        raise ValidationError(f"{path}.container_strategy.compose_directory must be service scoped")

    readiness_decision = _validate_required_object(data, path, "readiness_decision")
    decision_status = readiness_decision["decision_status"]
    if decision_status not in MUSICNN_ONNX_SCOPED_BASELINE_CAPTURE_DECISION_STATUSES:
        raise ValidationError(f"{path}.readiness_decision.decision_status is not allowed: {decision_status!r}")
    ready_for_capture = readiness_decision["ready_for_scoped_baseline_capture"]
    if not isinstance(ready_for_capture, bool):
        raise ValidationError(f"{path}.readiness_decision.ready_for_scoped_baseline_capture must be a bool")
    if ready_for_capture != data["approved_for_scoped_baseline_capture"]:
        raise ValidationError(
            f"{path}.approved_for_scoped_baseline_capture must match readiness_decision"
        )
    readiness_blockers = readiness_decision["blockers"]
    if not isinstance(readiness_blockers, list):
        raise ValidationError(f"{path}.readiness_decision.blockers must be a list")
    readiness_blocker_codes = _collect_blocker_codes(
        readiness_blockers,
        MUSICNN_ONNX_SCOPED_BASELINE_CAPTURE_BLOCKERS,
        f"{path}.readiness_decision.blockers",
    )

    if fixture_status == "missing":
        if fixture_count != 0:
            raise ValidationError(f"{path}.fixtures.fixture_count must be 0 when missing")
        if "FIXTURE_FILES_MISSING" not in fixture_blocker_codes | readiness_blocker_codes:
            raise ValidationError(f"{path} must record FIXTURE_FILES_MISSING when fixtures are missing")
        if data["approved_for_scoped_baseline_capture"] is not False:
            raise ValidationError(f"{path}.approved_for_scoped_baseline_capture must be false without fixtures")
        if decision_status != "blocked_missing_fixtures":
            raise ValidationError(f'{path}.readiness_decision.decision_status must be "blocked_missing_fixtures"')
    if fixture_status == "unclear_provenance":
        if "BLOCKED_FIXTURE_PROVENANCE_UNCLEAR" not in fixture_blocker_codes | readiness_blocker_codes:
            raise ValidationError(f"{path} must record BLOCKED_FIXTURE_PROVENANCE_UNCLEAR")
        if data["approved_for_scoped_baseline_capture"] is not False:
            raise ValidationError(f"{path}.approved_for_scoped_baseline_capture must be false without provenance")
    if ready_for_capture and (fixture_status != "available" or fixture_count <= 0 or readiness_blockers):
        raise ValidationError(f"{path} cannot be ready without available fixtures and empty blockers")
    if not ready_for_capture and not readiness_blockers:
        raise ValidationError(f"{path}.readiness_decision.blockers must be non-empty when blocked")

    safety_confirmations = _validate_required_object(data, path, "safety_confirmations")
    for field in REQUIRED_SCOPED_BASELINE_SAFETY_CONFIRMATIONS:
        if field not in safety_confirmations:
            raise ValidationError(f"{path}.safety_confirmations is missing required field: {field}")
        _require_bool_value(safety_confirmations[field], True, f"{path}.safety_confirmations.{field}")

    serialized = json.dumps(data)
    forbidden_paths = (
        "/tmp/music-tools-onnx-parity/fixtures/",
        "/opt/music-tools/tidal-parser",
    )
    for forbidden_path in forbidden_paths:
        if forbidden_path in serialized:
            raise ValidationError(f"{path} must not publish private or unrelated full local path: {forbidden_path}")

    _validate_no_inference_or_production_approval_claims(data, str(path))
    _validate_no_parity_or_runtime_approval_claims(data, path)


def _validate_musicnn_onnx_fixture_placement_and_scoped_baseline_readiness_report(path: Path) -> None:
    data = _load_json(path)

    for field in REQUIRED_MUSICNN_ONNX_FIXTURE_PLACEMENT_READINESS_FIELDS:
        if field not in data:
            raise ValidationError(f"{path} is missing required Roadmap 4.45 field: {field}")

    if data["roadmap"] != "4.45":
        raise ValidationError(f'{path}.roadmap must be "4.45"')
    if data["report_type"] != MUSICNN_ONNX_FIXTURE_PLACEMENT_AND_SCOPED_BASELINE_READINESS_REPORT_TYPE:
        raise ValidationError(
            f'{path}.report_type must be "'
            f'{MUSICNN_ONNX_FIXTURE_PLACEMENT_AND_SCOPED_BASELINE_READINESS_REPORT_TYPE}"'
        )

    _require_bool_value(data["not_production_decision"], True, f"{path}.not_production_decision")
    for field in (
        "approved_for_production",
        "approved_for_provider_implementation",
        "approved_for_default_provider_switch",
        "approved_for_full_numeric_parity_run",
    ):
        _require_bool_value(data[field], False, f"{path}.{field}")
    for field in (
        "no_audio_files_committed",
        "no_model_files_committed",
        "no_venv_committed",
        "no_dependency_changes",
        "no_docker_changes",
        "no_docker_rebuild",
        "no_classify_calls",
        "legacy_musicnn_remains_baseline",
    ):
        _require_bool_value(data[field], True, f"{path}.{field}")
    if not isinstance(data["approved_for_scoped_baseline_capture"], bool):
        raise ValidationError(f"{path}.approved_for_scoped_baseline_capture must be a bool")

    fixture_status = data["fixture_status"]
    if fixture_status not in {"present", "missing", "unclear_provenance"}:
        raise ValidationError(f"{path}.fixture_status is not allowed: {fixture_status!r}")
    fixture_count = data["fixture_count"]
    if not isinstance(fixture_count, int) or isinstance(fixture_count, bool) or fixture_count < 0:
        raise ValidationError(f"{path}.fixture_count must be a non-negative integer")
    provenance_status = data["provenance_status"]
    if provenance_status not in {"available", "missing", "unclear"}:
        raise ValidationError(f"{path}.provenance_status is not allowed: {provenance_status!r}")
    if data["license_status"] != "CC0 1.0 Universal / public domain":
        raise ValidationError(f"{path}.license_status must record CC0/public-domain status")
    if data["usage_permission"] != "local_evaluation_only":
        raise ValidationError(f'{path}.usage_permission must be "local_evaluation_only"')

    sanitized_fixtures = data["sanitized_fixtures"]
    if not isinstance(sanitized_fixtures, list):
        raise ValidationError(f"{path}.sanitized_fixtures must be a list")
    if fixture_count != len(sanitized_fixtures):
        raise ValidationError(f"{path}.fixture_count must match sanitized_fixtures length")
    if fixture_status == "present" and fixture_count <= 0:
        raise ValidationError(f"{path}.fixture_count must be positive when fixtures are present")

    for index, fixture in enumerate(sanitized_fixtures):
        context = f"{path}.sanitized_fixtures[{index}]"
        if not isinstance(fixture, dict):
            raise ValidationError(f"{context} must be an object")
        for field in REQUIRED_MUSICNN_ONNX_FIXTURE_PLACEMENT_SANITIZED_FIELDS:
            if field not in fixture:
                raise ValidationError(f"{context} is missing required field: {field}")
        if not isinstance(fixture["fixture_id"], str) or not fixture["fixture_id"].strip():
            raise ValidationError(f"{context}.fixture_id must be a non-empty string")
        _validate_sha256(fixture["sha256"], f"{context}.sha256")
        _validate_positive_integer(fixture["file_size_bytes"], f"{context}.file_size_bytes")
        if fixture["audio_format"] != "mp3":
            raise ValidationError(f'{context}.audio_format must be "mp3"')
        if fixture["source_artist"] != "John Bartmann":
            raise ValidationError(f'{context}.source_artist must be "John Bartmann"')
        if fixture["license_status"] != data["license_status"]:
            raise ValidationError(f"{context}.license_status must match the top-level license_status")
        if fixture["usage_permission"] != data["usage_permission"]:
            raise ValidationError(f"{context}.usage_permission must match the top-level usage_permission")

    if data["baseline_runtime_strategy"] != "existing_container_local_only":
        raise ValidationError(f"{path}.baseline_runtime_strategy is not allowed")
    if data["baseline_capture_readiness"] not in MUSICNN_ONNX_FIXTURE_PLACEMENT_READINESS_STATUSES:
        raise ValidationError(
            f"{path}.baseline_capture_readiness is not allowed: {data['baseline_capture_readiness']!r}"
        )
    decision_status = data["decision_status"]
    if decision_status not in MUSICNN_ONNX_FIXTURE_PLACEMENT_READINESS_STATUSES:
        raise ValidationError(f"{path}.decision_status is not allowed: {decision_status!r}")
    if data["baseline_capture_readiness"] != decision_status:
        raise ValidationError(f"{path}.baseline_capture_readiness must match decision_status")

    container_strategy = _validate_required_object(data, path, "container_strategy")
    for field in ("service_name_known", "import_check_allowed", "classify_call_allowed", "rebuild_allowed"):
        if not isinstance(container_strategy.get(field), bool):
            raise ValidationError(f"{path}.container_strategy.{field} must be a bool")
    _require_bool_value(
        container_strategy["classify_call_allowed"],
        False,
        f"{path}.container_strategy.classify_call_allowed",
    )
    _require_bool_value(container_strategy["rebuild_allowed"], False, f"{path}.container_strategy.rebuild_allowed")
    compose_directory = container_strategy.get("compose_directory")
    if not isinstance(compose_directory, str) or not compose_directory.strip():
        raise ValidationError(f"{path}.container_strategy.compose_directory must be a non-empty string")
    if compose_directory.startswith("/") or "/opt/music-tools" in compose_directory:
        raise ValidationError(f"{path}.container_strategy.compose_directory must be sanitized")

    blockers = data["blockers"]
    if not isinstance(blockers, list):
        raise ValidationError(f"{path}.blockers must be a list")
    blocker_codes = _collect_blocker_codes(
        blockers,
        MUSICNN_ONNX_FIXTURE_PLACEMENT_READINESS_BLOCKERS,
        f"{path}.blockers",
    )

    if decision_status == "ready_for_scoped_baseline_capture":
        if blockers:
            raise ValidationError(f"{path}.blockers must be empty when ready_for_scoped_baseline_capture")
        if fixture_status != "present" or provenance_status != "available":
            raise ValidationError(f"{path}.decision_status cannot be ready without present fixtures and provenance")
        if data["approved_for_scoped_baseline_capture"] is not True:
            raise ValidationError(f"{path}.approved_for_scoped_baseline_capture must be true when ready")
        _require_bool_value(container_strategy["service_name_known"], True, f"{path}.container_strategy.service_name_known")
    else:
        if not blockers:
            raise ValidationError(f"{path}.blockers must be non-empty unless ready")
        if data["approved_for_scoped_baseline_capture"] is not False:
            raise ValidationError(f"{path}.approved_for_scoped_baseline_capture must be false when blocked")
        if fixture_status == "missing" and "FIXTURE_FILES_MISSING" not in blocker_codes:
            raise ValidationError(f"{path}.blockers must include FIXTURE_FILES_MISSING when fixtures are missing")
        if fixture_status == "unclear_provenance" and "FIXTURE_PROVENANCE_UNCLEAR" not in blocker_codes:
            raise ValidationError(
                f"{path}.blockers must include FIXTURE_PROVENANCE_UNCLEAR when provenance is unclear"
            )

    serialized = json.dumps(data)
    forbidden_paths = (
        "/tmp/music-tools-onnx-parity",
        "/opt/music-tools",
        "docs/",
        "tests/",
        "app/",
    )
    for forbidden_path in forbidden_paths:
        if forbidden_path in serialized:
            raise ValidationError(f"{path} must not publish a forbidden local or repo path: {forbidden_path}")

    _validate_no_inference_or_production_approval_claims(data, str(path))
    _validate_no_parity_or_runtime_approval_claims(data, path)


def _validate_musicnn_legacy_baseline_capture_report(path: Path) -> None:
    data = _load_json(path)

    for field in REQUIRED_MUSICNN_LEGACY_BASELINE_CAPTURE_FIELDS:
        if field not in data:
            raise ValidationError(f"{path} is missing required Roadmap 4.48 field: {field}")

    if data["roadmap"] != "4.50":
        raise ValidationError(f'{path}.roadmap must be "4.50"')
    if data["report_type"] != MUSICNN_LEGACY_BASELINE_CAPTURE_REPORT_TYPE:
        raise ValidationError(f'{path}.report_type must be "{MUSICNN_LEGACY_BASELINE_CAPTURE_REPORT_TYPE}"')

    _require_bool_value(data["not_production_decision"], True, f"{path}.not_production_decision")
    for field in (
        "approved_for_production",
        "approved_for_provider_implementation",
        "approved_for_default_provider_switch",
        "approved_for_full_numeric_parity_run",
        "approved_for_onnx_execution",
    ):
        _require_bool_value(data[field], False, f"{path}.{field}")
    for field in LEGACY_MUSICNN_BASELINE_CAPTURE_REPORT_OPTIONAL_TRUE_FIELDS:
        _require_bool_value(data[field], True, f"{path}.{field}")
    if data["baseline_capture_scope"] != "one_off_compose_run_bind_mount":
        raise ValidationError(f'{path}.baseline_capture_scope must be "one_off_compose_run_bind_mount"')
    if data["selected_fixture_visibility_strategy"] != "one_off_compose_run_bind_mount":
        raise ValidationError(
            f'{path}.selected_fixture_visibility_strategy must be "one_off_compose_run_bind_mount"'
        )
    expected_import_policy = [
        "essentia_first",
        "no_explicit_tensorflow_before_essentia",
        "production_like_legacy_musicnn_path",
        "fresh_python_process",
    ]
    if data["import_policy"] != expected_import_policy:
        raise ValidationError(f"{path}.import_policy must record the Essentia-first import policy")

    fixture_count = data["fixture_count"]
    if not isinstance(fixture_count, int) or isinstance(fixture_count, bool) or fixture_count < 0:
        raise ValidationError(f"{path}.fixture_count must be a non-negative integer")
    sanitized_fixtures = data["sanitized_fixtures"]
    if not isinstance(sanitized_fixtures, list):
        raise ValidationError(f"{path}.sanitized_fixtures must be a list")
    if fixture_count != len(sanitized_fixtures):
        raise ValidationError(f"{path}.fixture_count must match sanitized_fixtures length")
    for index, fixture in enumerate(sanitized_fixtures):
        context = f"{path}.sanitized_fixtures[{index}]"
        if not isinstance(fixture, dict):
            raise ValidationError(f"{context} must be an object")
        for field in REQUIRED_MUSICNN_LEGACY_BASELINE_SANITIZED_FIXTURE_FIELDS:
            if field not in fixture:
                raise ValidationError(f"{context} is missing required field: {field}")
        if not isinstance(fixture["fixture_id"], str) or not fixture["fixture_id"].strip():
            raise ValidationError(f"{context}.fixture_id must be a non-empty string")
        _validate_sha256(fixture["sha256"], f"{context}.sha256")
        if fixture["audio_format"] != "mp3":
            raise ValidationError(f'{context}.audio_format must be "mp3"')
        if fixture["source_artist"] != "John Bartmann":
            raise ValidationError(f'{context}.source_artist must be "John Bartmann"')
        if fixture["license_status"] != "CC0":
            raise ValidationError(f'{context}.license_status must be "CC0"')

    container_execution = _validate_required_object(data, path, "container_execution")
    for field in (
        "one_off_container_used",
        "bind_mount_used",
        "running_service_mutated",
        "fixture_path_visible",
        "expected_mp3_files_visible",
        "essentia_standard_import_ok",
        "tensorflow_predict_musicnn_available",
    ):
        if not isinstance(container_execution.get(field), bool):
            raise ValidationError(f"{path}.container_execution.{field} must be a bool")
    _require_bool_value(
        container_execution["one_off_container_used"], True, f"{path}.container_execution.one_off_container_used"
    )
    _require_bool_value(container_execution["bind_mount_used"], True, f"{path}.container_execution.bind_mount_used")
    _require_bool_value(
        container_execution["running_service_mutated"], False, f"{path}.container_execution.running_service_mutated"
    )
    for field in ("compose_directory", "service_name"):
        value = container_execution.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{path}.container_execution.{field} must be a non-empty string")
    if container_execution.get("import_policy_used") != expected_import_policy:
        raise ValidationError(f"{path}.container_execution.import_policy_used must record the Essentia-first policy")

    capture_status = _validate_required_object(data, path, "baseline_capture_status")
    if not isinstance(data["baseline_capture_succeeded"], bool):
        raise ValidationError(f"{path}.baseline_capture_succeeded must be a bool")
    if not isinstance(capture_status.get("succeeded"), bool):
        raise ValidationError(f"{path}.baseline_capture_status.succeeded must be a bool")
    if data["baseline_capture_succeeded"] != capture_status["succeeded"]:
        raise ValidationError(f"{path}.baseline_capture_succeeded must match baseline_capture_status.succeeded")
    for field, value in capture_status.items():
        if isinstance(value, bool):
            continue
        if not isinstance(value, (str, list, dict, int, float)) or isinstance(value, bool):
            raise ValidationError(f"{path}.baseline_capture_status.{field} must be a bool")

    baseline_outputs = data["baseline_outputs"]
    if not isinstance(baseline_outputs, list):
        raise ValidationError(f"{path}.baseline_outputs must be a list")
    blockers = data["blockers"]
    if not isinstance(blockers, list):
        raise ValidationError(f"{path}.blockers must be a list")
    blocker_codes = _collect_blocker_codes(
        blockers,
        MUSICNN_LEGACY_BASELINE_CAPTURE_BLOCKERS,
        f"{path}.blockers",
    )

    if capture_status["succeeded"]:
        if blockers:
            raise ValidationError(f"{path}.blockers must be empty when baseline capture succeeds")
        if len(baseline_outputs) != fixture_count:
            raise ValidationError(f"{path}.baseline_outputs must match fixture_count when capture succeeds")
        _require_bool_value(
            container_execution["fixture_path_visible"],
            True,
            f"{path}.container_execution.fixture_path_visible",
        )
        for index, output in enumerate(baseline_outputs):
            context = f"{path}.baseline_outputs[{index}]"
            if not isinstance(output, dict):
                raise ValidationError(f"{context} must be an object")
            for field in (
                "fixture_id",
                "output_shape",
                "top_labels",
                "top_scores",
                "genres",
                "genres_pretty",
                "warnings",
            ):
                if field not in output:
                    raise ValidationError(f"{context} is missing required field: {field}")
            if not isinstance(output["fixture_id"], str) or not output["fixture_id"].strip():
                raise ValidationError(f"{context}.fixture_id must be a non-empty string")
            if not isinstance(output["output_shape"], list) or not output["output_shape"]:
                raise ValidationError(f"{context}.output_shape must be a non-empty list")
            if not all(isinstance(item, int) and not isinstance(item, bool) for item in output["output_shape"]):
                raise ValidationError(f"{context}.output_shape must contain integers")
            if not isinstance(output["top_labels"], list) or not output["top_labels"]:
                raise ValidationError(f"{context}.top_labels must be a non-empty list")
            if not all(isinstance(item, str) and item.strip() for item in output["top_labels"]):
                raise ValidationError(f"{context}.top_labels must contain non-empty strings")
            if not isinstance(output["top_scores"], list) or len(output["top_scores"]) != len(output["top_labels"]):
                raise ValidationError(f"{context}.top_scores must match top_labels length")
            if not all(_is_number(item) for item in output["top_scores"]):
                raise ValidationError(f"{context}.top_scores must contain numbers")
            if not isinstance(output["genres"], list) or not isinstance(output["genres_pretty"], list):
                raise ValidationError(f"{context}.genres and genres_pretty must be lists")
            for genre_index, genre in enumerate(output["genres"]):
                genre_context = f"{context}.genres[{genre_index}]"
                if not isinstance(genre, dict):
                    raise ValidationError(f"{genre_context} must be an object")
                if not isinstance(genre.get("tag"), str) or not genre["tag"].strip():
                    raise ValidationError(f"{genre_context}.tag must be a non-empty string")
                if not _is_number(genre.get("prob")):
                    raise ValidationError(f"{genre_context}.prob must be a number")
            if not all(isinstance(item, str) and item.strip() for item in output["genres_pretty"]):
                raise ValidationError(f"{context}.genres_pretty must contain non-empty strings")
            if not isinstance(output["warnings"], list):
                raise ValidationError(f"{context}.warnings must be a list")
    else:
        if not blockers:
            raise ValidationError(f"{path}.blockers must be non-empty when baseline capture is blocked")

    serialized = json.dumps(data)
    if "/tmp/music-tools-onnx-parity" in serialized:
        raise ValidationError(f"{path} must not publish the external fixture workspace path")
    if "/opt/music-tools" in serialized:
        raise ValidationError(f"{path} must not publish private repository paths")
    _validate_no_inference_or_production_approval_claims(data, str(path))
    _validate_no_parity_or_runtime_approval_claims(data, path)


def _validate_musicnn_onnx_preprocessing_alignment_report(path: Path) -> None:
    data = _load_json(path)

    for field in REQUIRED_MUSICNN_ONNX_PREPROCESSING_ALIGNMENT_FIELDS:
        if field not in data:
            raise ValidationError(f"{path} is missing required Roadmap 4.52 field: {field}")

    if data["roadmap"] != "4.52":
        raise ValidationError(f'{path}.roadmap must be "4.52"')
    if data["report_type"] != MUSICNN_ONNX_PREPROCESSING_ALIGNMENT_REPORT_TYPE:
        raise ValidationError(
            f'{path}.report_type must be "{MUSICNN_ONNX_PREPROCESSING_ALIGNMENT_REPORT_TYPE}"'
        )
    if data["generated_by"] != "scripts/lightweight/musicnn_preprocessing_alignment_probe.py":
        raise ValidationError(f"{path}.generated_by must reference the local-only alignment probe")

    _require_bool_value(data["agents_md_read"], True, f"{path}.agents_md_read")
    _require_bool_value(data["not_production_decision"], True, f"{path}.not_production_decision")
    for field in (
        "approved_for_production",
        "approved_for_provider_implementation",
        "approved_for_default_provider_switch",
        "approved_for_full_numeric_parity_run",
        "approved_for_final_parity_decision",
        "approved_for_classify_contract_change",
        "approved_for_onnx_fixture_output_capture",
    ):
        _require_bool_value(data[field], False, f"{path}.{field}")
    for field in (
        "no_audio_files_committed",
        "no_model_files_committed",
        "no_venv_committed",
        "no_dependency_changes",
        "no_dockerfile_changes",
        "no_compose_file_changes",
        "no_docker_rebuild",
        "no_classify_calls",
        "no_provider_changes",
        "no_tidal_parser_changes",
        "legacy_musicnn_remains_baseline",
    ):
        _require_bool_value(data[field], True, f"{path}.{field}")

    baseline_evidence = _validate_required_object(data, path, "baseline_evidence")
    if baseline_evidence.get("available") is not True:
        raise ValidationError(f"{path}.baseline_evidence.available must be true")
    if baseline_evidence.get("fixture_count") != 3:
        raise ValidationError(f"{path}.baseline_evidence.fixture_count must be 3")
    if baseline_evidence.get("expected_output_shapes") != [[30, 50], [35, 50], [86, 50]]:
        raise ValidationError(f"{path}.baseline_evidence.expected_output_shapes must record the committed shapes")
    if baseline_evidence.get("report_path") != (
        "docs/lightweight/evaluation/parity-scaffold/musicnn-legacy-baseline-capture-report.json"
    ):
        raise ValidationError(f"{path}.baseline_evidence.report_path must reference the committed baseline report")

    onnx_model_metadata = _validate_required_object(data, path, "onnx_model_metadata")
    if onnx_model_metadata.get("input_name") != "melspectrogram":
        raise ValidationError(f"{path}.onnx_model_metadata.input_name must be melspectrogram")
    if onnx_model_metadata.get("input_shape_tail") != [187, 96]:
        raise ValidationError(f"{path}.onnx_model_metadata.input_shape_tail must be [187, 96]")
    if onnx_model_metadata.get("output_names") != ["activations", "embeddings"]:
        raise ValidationError(f"{path}.onnx_model_metadata.output_names must record the committed ONNX outputs")
    if onnx_model_metadata.get("output_shape_tails") != [[50], [200]]:
        raise ValidationError(f"{path}.onnx_model_metadata.output_shape_tails must record the committed ONNX shapes")

    preprocessing_metadata = _validate_required_object(data, path, "preprocessing_metadata")
    if preprocessing_metadata.get("sample_rate") != 16000:
        raise ValidationError(f"{path}.preprocessing_metadata.sample_rate must be 16000")
    for field in ("frame_size", "hop_size", "mel_bands", "patch_length", "tensor_layout", "normalization"):
        if field not in preprocessing_metadata:
            raise ValidationError(f"{path}.preprocessing_metadata is missing required field: {field}")
    if preprocessing_metadata.get("source_of_truth") != [
        "app/services/classify.py",
        "app/providers/legacy_musicnn.py",
        "app/core/settings.py",
        "app/models/msd-musicnn-1.json",
        "docs/lightweight/evaluation/parity-scaffold/musicnn-legacy-baseline-capture-report.json",
        "docs/lightweight/evaluation/parity-scaffold/musicnn-onnx-output-capture-report.json",
    ]:
        raise ValidationError(f"{path}.preprocessing_metadata.source_of_truth must remain sanitized and scoped")
    unknown_fields = preprocessing_metadata.get("unknown_fields")
    if not isinstance(unknown_fields, list) or not unknown_fields:
        raise ValidationError(f"{path}.preprocessing_metadata.unknown_fields must be a non-empty list")
    for index, field in enumerate(unknown_fields):
        if not isinstance(field, str) or not field.strip():
            raise ValidationError(f"{path}.preprocessing_metadata.unknown_fields[{index}] must be a non-empty string")

    legacy_preprocessing_path = _validate_required_object(data, path, "legacy_preprocessing_path")
    _require_bool_value(
        legacy_preprocessing_path.get("uses_tensorflow_predict_musiccnn"),
        True,
        f"{path}.legacy_preprocessing_path.uses_tensorflow_predict_musiccnn",
    )
    _require_bool_value(
        legacy_preprocessing_path.get("uses_monoloader"),
        True,
        f"{path}.legacy_preprocessing_path.uses_monoloader",
    )
    _require_bool_value(
        legacy_preprocessing_path.get("uses_ffmpeg"),
        True,
        f"{path}.legacy_preprocessing_path.uses_ffmpeg",
    )
    _require_bool_value(
        legacy_preprocessing_path.get("preprocessing_exposed_as_intermediate"),
        False,
        f"{path}.legacy_preprocessing_path.preprocessing_exposed_as_intermediate",
    )

    alignment_status = _validate_required_object(data, path, "alignment_status")
    for field in ("candidate_alignment_path_found", "blocked", "inconclusive"):
        if not isinstance(alignment_status.get(field), bool):
            raise ValidationError(f"{path}.alignment_status.{field} must be a bool")
    if alignment_status["candidate_alignment_path_found"] is not False:
        raise ValidationError(f"{path}.alignment_status.candidate_alignment_path_found must be false")
    if alignment_status["blocked"] is not True:
        raise ValidationError(f"{path}.alignment_status.blocked must be true")
    if alignment_status["inconclusive"] is not False:
        raise ValidationError(f"{path}.alignment_status.inconclusive must be false")

    candidate_alignment_path = _validate_required_object(data, path, "candidate_alignment_path")
    if not isinstance(candidate_alignment_path.get("method"), str) or not candidate_alignment_path["method"].strip():
        raise ValidationError(f"{path}.candidate_alignment_path.method must be a non-empty string")
    for field in ("required_algorithms", "evidence", "risks"):
        value = candidate_alignment_path.get(field)
        if not isinstance(value, list) or not value:
            raise ValidationError(f"{path}.candidate_alignment_path.{field} must be a non-empty list")
        for index, item in enumerate(value):
            if not isinstance(item, str) or not item.strip():
                raise ValidationError(f"{path}.candidate_alignment_path.{field}[{index}] must be a non-empty string")

    blockers = data["blockers"]
    if not isinstance(blockers, list) or not blockers:
        raise ValidationError(f"{path}.blockers must be a non-empty list")
    blocker_codes: set[str] = set()
    for index, blocker in enumerate(blockers):
        context = f"{path}.blockers[{index}]"
        if not isinstance(blocker, dict):
            raise ValidationError(f"{context} must be an object")
        code = blocker.get("code")
        message = blocker.get("message")
        if code not in MUSICNN_ONNX_PREPROCESSING_ALIGNMENT_BLOCKERS:
            raise ValidationError(f"{context}.code is not allowed: {code!r}")
        if not isinstance(message, str) or not message.strip():
            raise ValidationError(f"{context}.message must be a non-empty string")
        blocker_codes.add(code)

    for required_code in (
        "LEGACY_INTERMEDIATE_NOT_EXPOSED",
        "MEL_INPUT_GENERATION_UNKNOWN",
        "ESSENTIA_PREPROCESSING_CHAIN_UNCONFIRMED",
    ):
        if required_code not in blocker_codes:
            raise ValidationError(f"{path}.blockers must include {required_code}")

    if "onnx_outputs" in data:
        raise ValidationError(f"{path} must not include ONNX output claims in the alignment gate")
    if "onnx_capture_succeeded" in data:
        raise ValidationError(f"{path} must not include ONNX capture success claims in the alignment gate")

    _validate_no_inference_or_production_approval_claims(data, str(path))
    _validate_no_parity_or_runtime_approval_claims(data, path)


def _validate_musicnn_onnx_pragmatic_preprocessing_prototype_report(path: Path) -> None:
    data = _load_json(path)

    for field in REQUIRED_MUSICNN_ONNX_PRAGMATIC_PREPROCESSING_PROTOTYPE_FIELDS:
        if field not in data:
            raise ValidationError(f"{path} is missing required Roadmap 4.56 field: {field}")

    if data["schema_version"] != "0.1":
        raise ValidationError(f'{path}.schema_version must be "0.1"')
    if data["roadmap"] != "4.56":
        raise ValidationError(f'{path}.roadmap must be "4.56"')
    if data["report_type"] != MUSICNN_ONNX_PRAGMATIC_PREPROCESSING_PROTOTYPE_REPORT_TYPE:
        raise ValidationError(
            f'{path}.report_type must be "{MUSICNN_ONNX_PRAGMATIC_PREPROCESSING_PROTOTYPE_REPORT_TYPE}"'
        )
    if data["generated_by"] != "scripts/lightweight/musicnn_pragmatic_preprocessing_prototype.py":
        raise ValidationError(f"{path}.generated_by must reference the local-only prototype helper")

    for field in ("created_at", "report_id", "target_candidate", "next_step_recommendation"):
        value = data[field]
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{path}.{field} must be a non-empty string")

    _require_bool_value(data["agents_md_read"], True, f"{path}.agents_md_read")
    _require_bool_value(data["not_production_decision"], True, f"{path}.not_production_decision")
    _require_bool_value(data["strict_legacy_parity_required"], False, f"{path}.strict_legacy_parity_required")
    _require_bool_value(data["output_drift_allowed"], True, f"{path}.output_drift_allowed")
    _require_bool_value(
        data["preprocessing_identical_to_legacy_required"],
        False,
        f"{path}.preprocessing_identical_to_legacy_required",
    )
    _require_bool_value(
        data["documented_reproducible_preprocessing_required"],
        True,
        f"{path}.documented_reproducible_preprocessing_required",
    )
    for field in (
        "approved_for_provider_implementation",
        "approved_for_default_provider_switch",
        "approved_for_production",
        "approved_for_dependency_changes",
        "approved_for_classify_call",
    ):
        _require_bool_value(data[field], False, f"{path}.{field}")
    _require_bool_value(data["legacy_musicnn_default_unchanged"], True, f"{path}.legacy_musicnn_default_unchanged")

    strategy_source = _validate_required_object(data, path, "strategy_source")
    if strategy_source.get("roadmap") != "4.55":
        raise ValidationError(f"{path}.strategy_source.roadmap must be 4.55")
    if strategy_source.get("strategy") != "essentia_standard_audio_loading_plus_standalone_mel_spectrogram_generation":
        raise ValidationError(f"{path}.strategy_source.strategy must describe the approved 4.55 strategy")

    prototype_modes = data["prototype_modes"]
    if prototype_modes != ["metadata_only", "preprocessing_probe"]:
        raise ValidationError(f"{path}.prototype_modes must record the two local-only helper modes")

    onnx_artifacts = _validate_required_object(data, path, "onnx_artifacts")
    if onnx_artifacts.get("model_name") != "msd-musicnn-1.onnx":
        raise ValidationError(f"{path}.onnx_artifacts.model_name must be msd-musicnn-1.onnx")
    if onnx_artifacts.get("metadata_name") != "msd-musicnn-1.json":
        raise ValidationError(f"{path}.onnx_artifacts.metadata_name must be msd-musicnn-1.json")
    if onnx_artifacts.get("external_workspace") is not True:
        raise ValidationError(f"{path}.onnx_artifacts.external_workspace must be true")
    if onnx_artifacts.get("model_sha256") != "49668ffec47e52e94b96f45930bb46a28a1368d4bdfb5c05378fa834aca616e1":
        raise ValidationError(f"{path}.onnx_artifacts.model_sha256 must match the approved local ONNX file")
    if onnx_artifacts.get("metadata_sha256") != "8e6b3b509f0610c0e65dce467fd459d6777509388eaddb13ed138d8ac1341ffe":
        raise ValidationError(f"{path}.onnx_artifacts.metadata_sha256 must match the approved local metadata file")

    baseline_evidence = _validate_required_object(data, path, "baseline_evidence")
    if baseline_evidence.get("report_path") != (
        "docs/lightweight/evaluation/parity-scaffold/musicnn-legacy-baseline-capture-report.json"
    ):
        raise ValidationError(f"{path}.baseline_evidence.report_path must reference the committed baseline report")
    if baseline_evidence.get("available") is not True:
        raise ValidationError(f"{path}.baseline_evidence.available must be true")
    if baseline_evidence.get("fixture_count") != 3:
        raise ValidationError(f"{path}.baseline_evidence.fixture_count must be 3")
    if baseline_evidence.get("expected_output_shapes") != [[30, 50], [35, 50], [86, 50]]:
        raise ValidationError(f"{path}.baseline_evidence.expected_output_shapes must record the committed shapes")

    onnx_input = _validate_required_object(data, path, "onnx_input")
    if onnx_input.get("input_name") != "melspectrogram":
        raise ValidationError(f"{path}.onnx_input.input_name must be melspectrogram")
    if onnx_input.get("shape_tail") != [187, 96]:
        raise ValidationError(f"{path}.onnx_input.shape_tail must be [187, 96]")
    if onnx_input.get("output_names") != ["activations", "embeddings"]:
        raise ValidationError(f"{path}.onnx_input.output_names must be ['activations', 'embeddings']")
    if onnx_input.get("output_shape_tails") != [[50], [200]]:
        raise ValidationError(f"{path}.onnx_input.output_shape_tails must be [[50], [200]]")

    expected_outputs = _validate_required_object(data, path, "expected_outputs")
    if expected_outputs.get("activations") != [50]:
        raise ValidationError(f"{path}.expected_outputs.activations must be [50]")
    if expected_outputs.get("embeddings") != [200]:
        raise ValidationError(f"{path}.expected_outputs.embeddings must be [200]")

    local_environment = _validate_required_object(data, path, "local_environment")
    _require_bool_value(local_environment.get("onnxruntime_available"), True, f"{path}.local_environment.onnxruntime_available")
    _require_bool_value(local_environment.get("essentia_available"), False, f"{path}.local_environment.essentia_available")
    _require_bool_value(
        local_environment.get("required_dependencies_missing"),
        True,
        f"{path}.local_environment.required_dependencies_missing",
    )
    missing_dependencies = local_environment.get("missing_dependencies")
    if missing_dependencies != ["essentia"]:
        raise ValidationError(f"{path}.local_environment.missing_dependencies must be ['essentia']")
    onnxruntime_version = local_environment.get("onnxruntime_version")
    if not isinstance(onnxruntime_version, str) or not onnxruntime_version.strip():
        raise ValidationError(f"{path}.local_environment.onnxruntime_version must be a non-empty string")

    preprocessing_probe_result = _validate_required_object(data, path, "preprocessing_probe_result")
    _require_bool_value(preprocessing_probe_result.get("attempted"), True, f"{path}.preprocessing_probe_result.attempted")
    _require_bool_value(preprocessing_probe_result.get("succeeded"), False, f"{path}.preprocessing_probe_result.succeeded")
    _require_bool_value(
        preprocessing_probe_result.get("repeated_run_stability_checked"),
        False,
        f"{path}.preprocessing_probe_result.repeated_run_stability_checked",
    )
    if preprocessing_probe_result.get("fixture_count") != 3:
        raise ValidationError(f"{path}.preprocessing_probe_result.fixture_count must be 3")
    if preprocessing_probe_result.get("produced_shape") is not None:
        raise ValidationError(f"{path}.preprocessing_probe_result.produced_shape must be null when blocked")

    probe_blockers = preprocessing_probe_result.get("blockers")
    if not isinstance(probe_blockers, list) or not probe_blockers:
        raise ValidationError(f"{path}.preprocessing_probe_result.blockers must be a non-empty list")
    probe_codes: set[str] = set()
    for index, blocker in enumerate(probe_blockers):
        context = f"{path}.preprocessing_probe_result.blockers[{index}]"
        if not isinstance(blocker, dict):
            raise ValidationError(f"{context} must be an object")
        code = blocker.get("code")
        message = blocker.get("message")
        if code not in MUSICNN_ONNX_PRAGMATIC_PREPROCESSING_PROTOTYPE_BLOCKERS:
            raise ValidationError(f"{context}.code is not allowed: {code!r}")
        if not isinstance(message, str) or not message.strip():
            raise ValidationError(f"{context}.message must be a non-empty string")
        probe_codes.add(code)
    for required_code in (
        "PRAGMATIC_PREPROCESSING_DEPENDENCY_UNAVAILABLE",
        "ESSENTIA_STANDARD_MEL_PATH_UNAVAILABLE",
    ):
        if required_code not in probe_codes:
            raise ValidationError(f"{path}.preprocessing_probe_result.blockers must include {required_code}")

    sanitized_fixtures = data["sanitized_fixtures"]
    if not isinstance(sanitized_fixtures, list) or len(sanitized_fixtures) != 3:
        raise ValidationError(f"{path}.sanitized_fixtures must be a list with 3 records")
    expected_fixtures = {
        "john_bartmann_earning_happiness_cc0": "d75937b87f8ad440d7655d33b5ffbd36e374ac71ad794976fdebd325541ae628",
        "john_bartmann_happy_clappy_cc0": "4f21570f701c07696c6b05f051528241a82156b923ab4bb3071c3c4af4a3372e",
        "john_bartmann_home_at_last_cc0": "0146392a4ea96de074197b2622ebd707ff2560586152bbd1e901095f2ea01c75",
    }
    seen_fixtures: set[str] = set()
    for index, item in enumerate(sanitized_fixtures):
        context = f"{path}.sanitized_fixtures[{index}]"
        if not isinstance(item, dict):
            raise ValidationError(f"{context} must be an object")
        fixture_id = item.get("fixture_id")
        sha256 = item.get("sha256")
        license_status = item.get("license_status")
        if not isinstance(fixture_id, str) or not fixture_id.strip():
            raise ValidationError(f"{context}.fixture_id must be a non-empty string")
        if fixture_id not in expected_fixtures:
            raise ValidationError(f"{context}.fixture_id is not part of the committed local fixture set")
        if fixture_id in seen_fixtures:
            raise ValidationError(f"{context}.fixture_id must be unique")
        seen_fixtures.add(fixture_id)
        if sha256 != expected_fixtures[fixture_id]:
            raise ValidationError(f"{context}.sha256 must match the committed local fixture hash")
        if license_status != "CC0 1.0 Universal / public domain":
            raise ValidationError(f"{context}.license_status must document the approved license")

    blockers = data["blockers"]
    if not isinstance(blockers, list) or not blockers:
        raise ValidationError(f"{path}.blockers must be a non-empty list")
    top_level_codes: set[str] = set()
    for index, blocker in enumerate(blockers):
        context = f"{path}.blockers[{index}]"
        if not isinstance(blocker, dict):
            raise ValidationError(f"{context} must be an object")
        code = blocker.get("code")
        message = blocker.get("message")
        if code not in MUSICNN_ONNX_PRAGMATIC_PREPROCESSING_PROTOTYPE_BLOCKERS:
            raise ValidationError(f"{context}.code is not allowed: {code!r}")
        if not isinstance(message, str) or not message.strip():
            raise ValidationError(f"{context}.message must be a non-empty string")
        top_level_codes.add(code)
    for required_code in (
        "PRAGMATIC_PREPROCESSING_DEPENDENCY_UNAVAILABLE",
        "ESSENTIA_STANDARD_MEL_PATH_UNAVAILABLE",
    ):
        if required_code not in top_level_codes:
            raise ValidationError(f"{path}.blockers must include {required_code}")

    serialized = json.dumps(data)
    if "/tmp/music-tools-onnx-parity" in serialized:
        raise ValidationError(f"{path} must not publish the external fixture workspace path")
    if "/opt/music-tools" in serialized:
        raise ValidationError(f"{path} must not publish private repository paths")
    _validate_no_inference_or_production_approval_claims(data, str(path))
    _validate_no_parity_or_runtime_approval_claims(data, path)


def _validate_musicnn_tensorflow_input_musiccnn_availability_probe_report(path: Path) -> None:
    data = _load_json(path)

    for field in REQUIRED_MUSICNN_TENSORFLOW_INPUT_MUSICCNN_AVAILABILITY_PROBE_FIELDS:
        if field not in data:
            raise ValidationError(f"{path} is missing required Roadmap 4.57 field: {field}")

    if data["schema_version"] != "0.1":
        raise ValidationError(f'{path}.schema_version must be "0.1"')
    if data["roadmap"] != "4.57":
        raise ValidationError(f'{path}.roadmap must be "4.57"')
    if data["report_type"] != MUSICNN_TENSORFLOW_INPUT_MUSICCNN_AVAILABILITY_PROBE_REPORT_TYPE:
        raise ValidationError(
            f'{path}.report_type must be "{MUSICNN_TENSORFLOW_INPUT_MUSICCNN_AVAILABILITY_PROBE_REPORT_TYPE}"'
        )
    if data["generated_by"] != "scripts/lightweight/musicnn_tensorflow_input_probe.py":
        raise ValidationError(f"{path}.generated_by must reference the local-only TensorflowInputMusiCNN helper")

    for field in (
        "created_at",
        "report_id",
        "target_candidate",
        "next_step_recommendation",
        "preprocessing_probe_execution",
        "recommended_isolated_probe_invocation",
    ):
        value = data[field]
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{path}.{field} must be a non-empty string")

    _require_bool_value(data["agents_md_read"], True, f"{path}.agents_md_read")
    _require_bool_value(data["not_production_decision"], True, f"{path}.not_production_decision")
    _require_bool_value(data["strict_legacy_parity_required"], False, f"{path}.strict_legacy_parity_required")
    _require_bool_value(data["output_drift_allowed"], True, f"{path}.output_drift_allowed")
    _require_bool_value(
        data["preprocessing_identical_to_legacy_required"],
        False,
        f"{path}.preprocessing_identical_to_legacy_required",
    )
    _require_bool_value(
        data["documented_reproducible_preprocessing_required"],
        True,
        f"{path}.documented_reproducible_preprocessing_required",
    )
    for field in (
        "approved_for_provider_implementation",
        "approved_for_default_provider_switch",
        "approved_for_production",
        "approved_for_dependency_changes",
        "approved_for_classify_call",
    ):
        _require_bool_value(data[field], False, f"{path}.{field}")
    _require_bool_value(data["legacy_musicnn_default_unchanged"], True, f"{path}.legacy_musicnn_default_unchanged")
    _require_bool_value(
        data["isolated_python_used_for_availability_check"],
        True,
        f"{path}.isolated_python_used_for_availability_check",
    )

    if data["preprocessing_probe_execution"] != "current_interpreter":
        raise ValidationError(f"{path}.preprocessing_probe_execution must be current_interpreter")

    if data["target_candidate"] != "official_onnx_musicnn":
        raise ValidationError(f"{path}.target_candidate must be official_onnx_musicnn")

    strategy_source = _validate_required_object(data, path, "strategy_source")
    if strategy_source.get("roadmap") != "4.55":
        raise ValidationError(f"{path}.strategy_source.roadmap must be 4.55")
    if strategy_source.get("strategy") != "essentia_standard_audio_loading_plus_standalone_mel_spectrogram_generation":
        raise ValidationError(f"{path}.strategy_source.strategy must describe the approved 4.55 strategy")

    prototype_source = _validate_required_object(data, path, "prototype_source")
    if prototype_source.get("roadmap") != "4.56":
        raise ValidationError(f"{path}.prototype_source.roadmap must be 4.56")
    if prototype_source.get("helper") != "scripts/lightweight/musicnn_pragmatic_preprocessing_prototype.py":
        raise ValidationError(f"{path}.prototype_source.helper must reference the 4.56 helper")

    probe_policy = _validate_required_object(data, path, "probe_policy")
    _require_bool_value(
        probe_policy.get("tensorflow_input_musiccnn_allowed_as_preprocessing_only_candidate"),
        True,
        f"{path}.probe_policy.tensorflow_input_musiccnn_allowed_as_preprocessing_only_candidate",
    )
    _require_bool_value(
        probe_policy.get("tensorflow_predict_musiccnn_not_used_as_preprocessing_oracle"),
        True,
        f"{path}.probe_policy.tensorflow_predict_musiccnn_not_used_as_preprocessing_oracle",
    )
    _require_bool_value(probe_policy.get("strict_legacy_parity_required"), False, f"{path}.probe_policy.strict_legacy_parity_required")
    _require_bool_value(probe_policy.get("production_decision_made"), False, f"{path}.probe_policy.production_decision_made")

    tensorflow_input_musiccnn = _validate_required_object(data, path, "tensorflow_input_musiccnn")
    _require_bool_value(tensorflow_input_musiccnn.get("checked"), True, f"{path}.tensorflow_input_musiccnn.checked")
    if not isinstance(tensorflow_input_musiccnn.get("available_in_isolated_env"), bool):
        raise ValidationError(f"{path}.tensorflow_input_musiccnn.available_in_isolated_env must be a bool")
    if not isinstance(tensorflow_input_musiccnn.get("available_in_system_python"), bool):
        raise ValidationError(f"{path}.tensorflow_input_musiccnn.available_in_system_python must be a bool")
    if not isinstance(tensorflow_input_musiccnn.get("hasattr_result"), bool):
        raise ValidationError(f"{path}.tensorflow_input_musiccnn.hasattr_result must be a bool")
    import_error_category = tensorflow_input_musiccnn.get("import_error_category")
    if import_error_category is not None and not isinstance(import_error_category, str):
        raise ValidationError(f"{path}.tensorflow_input_musiccnn.import_error_category must be a string or null")

    isolated_env = _validate_required_object(tensorflow_input_musiccnn, path, "isolated_env")
    _require_bool_value(isolated_env.get("python_available"), True, f"{path}.tensorflow_input_musiccnn.isolated_env.python_available")
    import_status = isolated_env.get("import_status")
    if not isinstance(import_status, str) or not import_status.strip():
        raise ValidationError(f"{path}.tensorflow_input_musiccnn.isolated_env.import_status must be a non-empty string")
    _require_bool_value(isolated_env.get("available"), bool(tensorflow_input_musiccnn.get("available_in_isolated_env")), f"{path}.tensorflow_input_musiccnn.isolated_env.available")
    isolated_import_error_category = isolated_env.get("import_error_category")
    isolated_import_error_message = isolated_env.get("import_error_message")
    if import_status == "imported":
        if isolated_import_error_category not in (None, ""):
            raise ValidationError(
                f"{path}.tensorflow_input_musiccnn.isolated_env.import_error_category must be null when import_status is imported"
            )
        if isolated_import_error_message not in (None, ""):
            raise ValidationError(
                f"{path}.tensorflow_input_musiccnn.isolated_env.import_error_message must be null when import_status is imported"
            )
    else:
        if not isinstance(isolated_import_error_category, str) or not isolated_import_error_category.strip():
            raise ValidationError(
                f"{path}.tensorflow_input_musiccnn.isolated_env.import_error_category must be a non-empty string when import_status is not imported"
            )
        if isolated_import_error_message is not None and not isinstance(isolated_import_error_message, str):
            raise ValidationError(
                f"{path}.tensorflow_input_musiccnn.isolated_env.import_error_message must be a string or null"
            )
    if not isinstance(isolated_env.get("hasattr_result"), bool):
        raise ValidationError(f"{path}.tensorflow_input_musiccnn.isolated_env.hasattr_result must be a bool")
    isolated_onnxruntime = _validate_required_object(isolated_env, path, "onnxruntime")
    if not isinstance(isolated_onnxruntime.get("available"), bool):
        raise ValidationError(f"{path}.tensorflow_input_musiccnn.isolated_env.onnxruntime.available must be a bool")
    if isolated_onnxruntime.get("available"):
        if not isinstance(isolated_onnxruntime.get("version"), str) or not isolated_onnxruntime["version"].strip():
            raise ValidationError(
                f"{path}.tensorflow_input_musiccnn.isolated_env.onnxruntime.version must be a non-empty string when available"
            )
        if isolated_onnxruntime.get("error_category") not in (None, ""):
            raise ValidationError(
                f"{path}.tensorflow_input_musiccnn.isolated_env.onnxruntime.error_category must be null when available"
            )
        if isolated_onnxruntime.get("error_message") not in (None, ""):
            raise ValidationError(
                f"{path}.tensorflow_input_musiccnn.isolated_env.onnxruntime.error_message must be null when available"
            )

    system_python = _validate_required_object(tensorflow_input_musiccnn, path, "system_python")
    if not isinstance(system_python.get("python_available"), bool):
        raise ValidationError(f"{path}.tensorflow_input_musiccnn.system_python.python_available must be a bool")
    system_import_status = system_python.get("import_status")
    if not isinstance(system_import_status, str) or not system_import_status.strip():
        raise ValidationError(f"{path}.tensorflow_input_musiccnn.system_python.import_status must be a non-empty string")
    if not isinstance(system_python.get("available"), bool):
        raise ValidationError(f"{path}.tensorflow_input_musiccnn.system_python.available must be a bool")
    system_import_error_category = system_python.get("import_error_category")
    system_import_error_message = system_python.get("import_error_message")
    if system_import_status == "imported":
        if system_import_error_category not in (None, ""):
            raise ValidationError(
                f"{path}.tensorflow_input_musiccnn.system_python.import_error_category must be null when import_status is imported"
            )
        if system_import_error_message not in (None, ""):
            raise ValidationError(
                f"{path}.tensorflow_input_musiccnn.system_python.import_error_message must be null when import_status is imported"
            )
    else:
        if not isinstance(system_import_error_category, str) or not system_import_error_category.strip():
            raise ValidationError(
                f"{path}.tensorflow_input_musiccnn.system_python.import_error_category must be a non-empty string when import_status is not imported"
            )
        if system_import_error_message is not None and not isinstance(system_import_error_message, str):
            raise ValidationError(
                f"{path}.tensorflow_input_musiccnn.system_python.import_error_message must be a string or null"
            )
    if not isinstance(system_python.get("hasattr_result"), bool):
        raise ValidationError(f"{path}.tensorflow_input_musiccnn.system_python.hasattr_result must be a bool")

    preprocessing_probe_result = _validate_required_object(data, path, "preprocessing_probe_result")
    if not isinstance(preprocessing_probe_result.get("attempted"), bool):
        raise ValidationError(f"{path}.preprocessing_probe_result.attempted must be a bool")
    if not isinstance(preprocessing_probe_result.get("succeeded"), bool):
        raise ValidationError(f"{path}.preprocessing_probe_result.succeeded must be a bool")
    if preprocessing_probe_result.get("expected_shape") != [187, 96]:
        raise ValidationError(f"{path}.preprocessing_probe_result.expected_shape must be [187, 96]")
    produced_shape = preprocessing_probe_result.get("produced_shape")
    if produced_shape is not None and produced_shape != [187, 96]:
        raise ValidationError(f"{path}.preprocessing_probe_result.produced_shape must be [187, 96] or null")
    fixture_count = preprocessing_probe_result.get("fixture_count")
    if not isinstance(fixture_count, int) or fixture_count < 0:
        raise ValidationError(f"{path}.preprocessing_probe_result.fixture_count must be a non-negative integer")
    repeated_run_stability_checked = preprocessing_probe_result.get("repeated_run_stability_checked")
    if not isinstance(repeated_run_stability_checked, bool):
        raise ValidationError(
            f"{path}.preprocessing_probe_result.repeated_run_stability_checked must be a bool"
        )
    stable = preprocessing_probe_result.get("stable")
    if repeated_run_stability_checked:
        if not isinstance(stable, bool):
            raise ValidationError(f"{path}.preprocessing_probe_result.stable must be a bool when stability was checked")
    elif stable is not None:
        raise ValidationError(f"{path}.preprocessing_probe_result.stable must be null when stability was not checked")
    if preprocessing_probe_result["succeeded"] and not preprocessing_probe_result["attempted"]:
        raise ValidationError(f"{path}.preprocessing_probe_result.succeeded cannot be true when attempted is false")
    if preprocessing_probe_result["succeeded"] and produced_shape != [187, 96]:
        raise ValidationError(f"{path}.preprocessing_probe_result.produced_shape must be [187, 96] when succeeded is true")
    if preprocessing_probe_result["succeeded"] and not repeated_run_stability_checked:
        raise ValidationError(
            f"{path}.preprocessing_probe_result.repeated_run_stability_checked must be true when succeeded is true"
        )
    probe_blockers = preprocessing_probe_result.get("blockers")
    if not isinstance(probe_blockers, list):
        raise ValidationError(f"{path}.preprocessing_probe_result.blockers must be a list")
    for index, blocker in enumerate(probe_blockers):
        context = f"{path}.preprocessing_probe_result.blockers[{index}]"
        if not isinstance(blocker, dict):
            raise ValidationError(f"{context} must be an object")
        code = blocker.get("code")
        message = blocker.get("message")
        if code not in MUSICNN_TENSORFLOW_INPUT_MUSICCNN_AVAILABILITY_PROBE_BLOCKERS:
            raise ValidationError(f"{context}.code is not allowed: {code!r}")
        if not isinstance(message, str) or not message.strip():
            raise ValidationError(f"{context}.message must be a non-empty string")

    sanitized_fixtures = data["sanitized_fixtures"]
    if not isinstance(sanitized_fixtures, list) or len(sanitized_fixtures) != 3:
        raise ValidationError(f"{path}.sanitized_fixtures must be a list with 3 records")
    expected_fixtures = {
        "john_bartmann_earning_happiness_cc0": "d75937b87f8ad440d7655d33b5ffbd36e374ac71ad794976fdebd325541ae628",
        "john_bartmann_happy_clappy_cc0": "4f21570f701c07696c6b05f051528241a82156b923ab4bb3071c3c4af4a3372e",
        "john_bartmann_home_at_last_cc0": "0146392a4ea96de074197b2622ebd707ff2560586152bbd1e901095f2ea01c75",
    }
    seen_fixtures: set[str] = set()
    for index, item in enumerate(sanitized_fixtures):
        context = f"{path}.sanitized_fixtures[{index}]"
        if not isinstance(item, dict):
            raise ValidationError(f"{context} must be an object")
        fixture_id = item.get("fixture_id")
        sha256 = item.get("sha256")
        license_status = item.get("license_status")
        if not isinstance(fixture_id, str) or not fixture_id.strip():
            raise ValidationError(f"{context}.fixture_id must be a non-empty string")
        if fixture_id not in expected_fixtures:
            raise ValidationError(f"{context}.fixture_id is not part of the committed local fixture set")
        if fixture_id in seen_fixtures:
            raise ValidationError(f"{context}.fixture_id must be unique")
        seen_fixtures.add(fixture_id)
        if sha256 != expected_fixtures[fixture_id]:
            raise ValidationError(f"{context}.sha256 must match the committed local fixture hash")
        if license_status != "CC0 1.0 Universal / public domain":
            raise ValidationError(f"{context}.license_status must document the approved license")

    fallback = _validate_required_object(data, path, "fallback")
    _require_bool_value(
        fallback.get("generic_melbands_fallback_evaluated"),
        True,
        f"{path}.fallback.generic_melbands_fallback_evaluated",
    )
    _require_bool_value(
        fallback.get("generic_melbands_fallback_used"),
        False,
        f"{path}.fallback.generic_melbands_fallback_used",
    )
    fallback_status = fallback.get("fallback_status")
    if not isinstance(fallback_status, str) or not fallback_status.strip():
        raise ValidationError(f"{path}.fallback.fallback_status must be a non-empty string")
    fallback_risks = fallback.get("fallback_risks")
    if not isinstance(fallback_risks, list):
        raise ValidationError(f"{path}.fallback.fallback_risks must be a list")

    blockers = data["blockers"]
    if not isinstance(blockers, list):
        raise ValidationError(f"{path}.blockers must be a list")
    for index, blocker in enumerate(blockers):
        context = f"{path}.blockers[{index}]"
        if not isinstance(blocker, dict):
            raise ValidationError(f"{context} must be an object")
        code = blocker.get("code")
        message = blocker.get("message")
        if code not in MUSICNN_TENSORFLOW_INPUT_MUSICCNN_AVAILABILITY_PROBE_BLOCKERS:
            raise ValidationError(f"{context}.code is not allowed: {code!r}")
        if not isinstance(message, str) or not message.strip():
            raise ValidationError(f"{context}.message must be a non-empty string")

    serialized = json.dumps(data)
    if "/tmp/music-tools-onnx-parity" in serialized:
        raise ValidationError(f"{path} must not publish the external fixture workspace path")
    if "/opt/music-tools" in serialized:
        raise ValidationError(f"{path} must not publish private repository paths")


def _validate_musicnn_onnx_output_capture_report(path: Path) -> None:
    data = _load_json(path)

    for field in REQUIRED_MUSICNN_ONNX_OUTPUT_CAPTURE_FIELDS:
        if field not in data:
            raise ValidationError(f"{path} is missing required Roadmap 4.51 field: {field}")

    if data["roadmap"] != "4.51":
        raise ValidationError(f'{path}.roadmap must be "4.51"')
    if data["report_type"] != MUSICNN_ONNX_OUTPUT_CAPTURE_REPORT_TYPE:
        raise ValidationError(f'{path}.report_type must be "{MUSICNN_ONNX_OUTPUT_CAPTURE_REPORT_TYPE}"')
    if data["generated_by"] != "scripts/lightweight/musicnn_onnx_output_capture.py":
        raise ValidationError(f"{path}.generated_by must reference the local-only ONNX capture helper")

    _require_bool_value(data["agents_md_read"], True, f"{path}.agents_md_read")
    _require_bool_value(data["not_production_decision"], True, f"{path}.not_production_decision")
    for field in (
        "approved_for_production",
        "approved_for_provider_implementation",
        "approved_for_default_provider_switch",
        "approved_for_full_numeric_parity_run",
        "approved_for_final_parity_decision",
        "approved_for_classify_contract_change",
    ):
        _require_bool_value(data[field], False, f"{path}.{field}")
    for field in (
        "no_audio_files_committed",
        "no_model_files_committed",
        "no_venv_committed",
        "no_dependency_changes",
        "no_dockerfile_changes",
        "no_compose_file_changes",
        "no_docker_rebuild",
        "no_classify_calls",
        "no_provider_changes",
        "no_tidal_parser_changes",
        "legacy_musicnn_remains_baseline",
    ):
        _require_bool_value(data[field], True, f"{path}.{field}")

    baseline_evidence = _validate_required_object(data, path, "baseline_evidence")
    if baseline_evidence.get("available") is not True:
        raise ValidationError(f"{path}.baseline_evidence.available must be true")
    if baseline_evidence.get("fixture_count") != 3:
        raise ValidationError(f"{path}.baseline_evidence.fixture_count must be 3")
    if baseline_evidence.get("fixture_ids") != [
        "john_bartmann_earning_happiness_cc0",
        "john_bartmann_happy_clappy_cc0",
        "john_bartmann_home_at_last_cc0",
    ]:
        raise ValidationError(f"{path}.baseline_evidence.fixture_ids must record the committed legacy fixture order")
    if baseline_evidence.get("expected_output_shapes") != [[30, 50], [35, 50], [86, 50]]:
        raise ValidationError(f"{path}.baseline_evidence.expected_output_shapes must record the committed shapes")
    if baseline_evidence.get("report_path") != (
        "docs/lightweight/evaluation/parity-scaffold/musicnn-legacy-baseline-capture-report.json"
    ):
        raise ValidationError(f"{path}.baseline_evidence.report_path must reference the committed baseline report")

    onnx_environment = _validate_required_object(data, path, "onnx_environment")
    _require_bool_value(onnx_environment.get("isolated_env_used"), True, f"{path}.onnx_environment.isolated_env_used")
    _require_bool_value(
        onnx_environment.get("onnxruntime_available"), True, f"{path}.onnx_environment.onnxruntime_available"
    )
    if not isinstance(onnx_environment.get("onnxruntime_version"), str) or not onnx_environment["onnxruntime_version"]:
        raise ValidationError(f"{path}.onnx_environment.onnxruntime_version must be a non-empty string")

    onnx_artifacts = _validate_required_object(data, path, "onnx_artifacts")
    _require_bool_value(onnx_artifacts.get("model_available"), True, f"{path}.onnx_artifacts.model_available")
    _require_bool_value(onnx_artifacts.get("metadata_available"), True, f"{path}.onnx_artifacts.metadata_available")
    _require_bool_value(onnx_artifacts.get("artifact_in_repo"), False, f"{path}.onnx_artifacts.artifact_in_repo")
    for field in ("model_sha256", "metadata_sha256"):
        _validate_sha256(onnx_artifacts.get(field), f"{path}.onnx_artifacts.{field}")

    fixture_count = data["fixture_count"]
    if fixture_count != 3:
        raise ValidationError(f"{path}.fixture_count must be 3")

    sanitized_fixtures = data["sanitized_fixtures"]
    if not isinstance(sanitized_fixtures, list) or len(sanitized_fixtures) != 3:
        raise ValidationError(f"{path}.sanitized_fixtures must contain the committed fixture set")
    for index, fixture in enumerate(sanitized_fixtures):
        context = f"{path}.sanitized_fixtures[{index}]"
        if not isinstance(fixture, dict):
            raise ValidationError(f"{context} must be an object")
        for field in ("fixture_id", "sha256", "audio_format", "source_artist", "license_status"):
            if field not in fixture:
                raise ValidationError(f"{context} is missing required field: {field}")
        if fixture["fixture_id"] not in {
            "john_bartmann_earning_happiness_cc0",
            "john_bartmann_happy_clappy_cc0",
            "john_bartmann_home_at_last_cc0",
        }:
            raise ValidationError(f"{context}.fixture_id is not an approved fixture id")
        _validate_sha256(fixture["sha256"], f"{context}.sha256")
        if fixture["audio_format"] != "mp3":
            raise ValidationError(f'{context}.audio_format must be "mp3"')
        if fixture["source_artist"] != "John Bartmann":
            raise ValidationError(f'{context}.source_artist must be "John Bartmann"')
        if fixture["license_status"] != "CC0 1.0 Universal / public domain":
            raise ValidationError(f'{context}.license_status must be "CC0 1.0 Universal / public domain"')

    onnx_model_metadata = _validate_required_object(data, path, "onnx_model_metadata")
    if onnx_model_metadata.get("preprocessing_alignment_status") != "unknown":
        raise ValidationError(f'{path}.onnx_model_metadata.preprocessing_alignment_status must be "unknown"')
    if onnx_model_metadata.get("input_names") != ["melspectrogram"]:
        raise ValidationError(f"{path}.onnx_model_metadata.input_names must record the ONNX input name")
    if onnx_model_metadata.get("output_names") != ["activations", "embeddings"]:
        raise ValidationError(f"{path}.onnx_model_metadata.output_names must record the ONNX output names")
    if not isinstance(onnx_model_metadata.get("input_shapes"), list) or not onnx_model_metadata["input_shapes"]:
        raise ValidationError(f"{path}.onnx_model_metadata.input_shapes must be a non-empty list")
    if not isinstance(onnx_model_metadata.get("output_shapes"), list) or len(onnx_model_metadata["output_shapes"]) != 2:
        raise ValidationError(f"{path}.onnx_model_metadata.output_shapes must contain two output shapes")

    input_shape = onnx_model_metadata["input_shapes"][0]
    if not isinstance(input_shape, list) or len(input_shape) != 3:
        raise ValidationError(f"{path}.onnx_model_metadata.input_shapes[0] must have three dimensions")
    if input_shape[-2:] != [187, 96]:
        raise ValidationError(f"{path}.onnx_model_metadata.input_shapes[0] must end with [187, 96]")
    for output_shape, expected_tail in zip(onnx_model_metadata["output_shapes"], ([50], [200]), strict=True):
        if not isinstance(output_shape, list) or len(output_shape) != 2:
            raise ValidationError(f"{path}.onnx_model_metadata.output_shapes entries must have two dimensions")
        if output_shape[-1:] != expected_tail:
            raise ValidationError(f"{path}.onnx_model_metadata output shapes must end with {expected_tail}")

    capture_status = _validate_required_object(data, path, "onnx_capture_status")
    if capture_status.get("succeeded") is not False:
        raise ValidationError(f"{path}.onnx_capture_status.succeeded must be false for the blocked gate report")
    if capture_status.get("blocked_preprocessing_unknown") is not True:
        raise ValidationError(f"{path}.onnx_capture_status.blocked_preprocessing_unknown must be true")
    for field in (
        "blocked_missing_baseline_evidence",
        "blocked_missing_onnx_artifact",
        "blocked_onnxruntime_unavailable",
        "blocked_capture_error",
    ):
        _require_bool_value(capture_status.get(field), False, f"{path}.onnx_capture_status.{field}")

    blockers = data["blockers"]
    if not isinstance(blockers, list) or len(blockers) != 1:
        raise ValidationError(f"{path}.blockers must contain the single blocked-preprocessing blocker")
    blocker = blockers[0]
    if not isinstance(blocker, dict):
        raise ValidationError(f"{path}.blockers[0] must be an object")
    if blocker.get("code") != "PREPROCESSING_ALIGNMENT_UNKNOWN":
        raise ValidationError(f"{path}.blockers[0].code must be PREPROCESSING_ALIGNMENT_UNKNOWN")
    if not isinstance(blocker.get("message"), str) or not blocker["message"].strip():
        raise ValidationError(f"{path}.blockers[0].message must be a non-empty string")

    outputs = data["onnx_outputs"]
    if outputs != []:
        raise ValidationError(f"{path}.onnx_outputs must be empty while capture is blocked")

    serialized = json.dumps(data)
    if "/tmp/music-tools-onnx-parity" in serialized:
        raise ValidationError(f"{path} must not publish private local paths")
    if "/opt/music-tools" in serialized:
        raise ValidationError(f"{path} must not publish repository local paths")

    _validate_no_inference_or_production_approval_claims(data, str(path))
    _validate_no_parity_or_runtime_approval_claims(data, path)


def _validate_musicnn_onnx_fixture_visibility_strategy_report(path: Path) -> None:
    data = _load_json(path)

    for field in REQUIRED_MUSICNN_ONNX_FIXTURE_VISIBILITY_STRATEGY_FIELDS:
        if field not in data:
            raise ValidationError(f"{path} is missing required Roadmap 4.47 field: {field}")

    if data["roadmap"] != "4.47":
        raise ValidationError(f'{path}.roadmap must be "4.47"')
    if data["report_type"] != MUSICNN_ONNX_FIXTURE_VISIBILITY_STRATEGY_REPORT_TYPE:
        raise ValidationError(
            f'{path}.report_type must be "{MUSICNN_ONNX_FIXTURE_VISIBILITY_STRATEGY_REPORT_TYPE}"'
        )

    _require_bool_value(data["not_production_decision"], True, f"{path}.not_production_decision")
    for field in (
        "approved_for_production",
        "approved_for_provider_implementation",
        "approved_for_default_provider_switch",
        "approved_for_full_numeric_parity_run",
        "approved_for_onnx_execution",
        "approved_for_baseline_capture_execution",
    ):
        _require_bool_value(data[field], False, f"{path}.{field}")
    for field in (
        "approved_for_future_scoped_baseline_capture_with_selected_strategy",
        "no_audio_files_committed",
        "no_model_files_committed",
        "no_venv_committed",
        "no_dependency_changes",
        "no_dockerfile_changes",
        "no_compose_file_changes",
        "no_docker_rebuild",
        "no_classify_calls",
        "legacy_musicnn_remains_baseline",
    ):
        _require_bool_value(data[field], True, f"{path}.{field}")

    fixture_source = _validate_required_object(data, path, "fixture_source")
    if fixture_source.get("host_fixture_root_sanitized") != "/tmp/music-tools-onnx-parity/fixtures/":
        raise ValidationError(f"{path}.fixture_source.host_fixture_root_sanitized must be the sanitized root")
    fixture_count = fixture_source.get("fixture_count")
    fixture_ids = fixture_source.get("fixture_ids")
    if fixture_count is not None and (
        not isinstance(fixture_count, int) or isinstance(fixture_count, bool) or fixture_count < 0
    ):
        raise ValidationError(f"{path}.fixture_source.fixture_count must be null or a non-negative integer")
    if not isinstance(fixture_ids, list):
        raise ValidationError(f"{path}.fixture_source.fixture_ids must be a list")
    for index, fixture_id in enumerate(fixture_ids):
        if not isinstance(fixture_id, str) or not fixture_id.strip():
            raise ValidationError(f"{path}.fixture_source.fixture_ids[{index}] must be a non-empty string")
        for forbidden in ("/opt/music-tools", "docs/", "tests/", "app/", "tidal-parser"):
            if forbidden in fixture_id:
                raise ValidationError(f"{path}.fixture_source.fixture_ids[{index}] must be sanitized")
    if fixture_count is not None and fixture_count != len(fixture_ids):
        raise ValidationError(f"{path}.fixture_source.fixture_count must match fixture_ids length when known")

    current_blocker = data["current_blocker"]
    if not isinstance(current_blocker, list):
        raise ValidationError(f"{path}.current_blocker must be a list")
    if set(current_blocker) != MUSICNN_ONNX_FIXTURE_VISIBILITY_CURRENT_BLOCKERS:
        raise ValidationError(f"{path}.current_blocker must record the Roadmap 4.46 mount blockers")

    evaluated_strategies = data["evaluated_strategies"]
    if not isinstance(evaluated_strategies, list):
        raise ValidationError(f"{path}.evaluated_strategies must be a list")
    seen_strategies: set[str] = set()
    for index, strategy in enumerate(evaluated_strategies):
        context = f"{path}.evaluated_strategies[{index}]"
        if not isinstance(strategy, dict):
            raise ValidationError(f"{context} must be an object")
        strategy_name = strategy.get("strategy")
        if strategy_name not in MUSICNN_ONNX_FIXTURE_VISIBILITY_STRATEGIES:
            raise ValidationError(f"{context}.strategy is not allowed: {strategy_name!r}")
        seen_strategies.add(strategy_name)
        for field in (
            "safe_for_future_scoped_baseline_capture",
            "requires_committed_compose_change",
            "requires_dockerfile_change",
            "requires_rebuild",
            "mutates_running_service",
            "keeps_fixtures_outside_repo",
        ):
            if not isinstance(strategy.get(field), bool):
                raise ValidationError(f"{context}.{field} must be a bool")
    if seen_strategies != MUSICNN_ONNX_FIXTURE_VISIBILITY_STRATEGIES:
        raise ValidationError(f"{path}.evaluated_strategies must include every fixture visibility strategy")

    if data["selected_strategy"] != "one_off_compose_run_bind_mount":
        raise ValidationError(f'{path}.selected_strategy must be "one_off_compose_run_bind_mount"')
    if data["selected_strategy_status"] != "approved_for_future_scoped_baseline_capture":
        raise ValidationError(
            f'{path}.selected_strategy_status must be "approved_for_future_scoped_baseline_capture"'
        )

    for field in ("strategy_rationale", "execution_boundaries"):
        value = data[field]
        if not isinstance(value, list) or not value:
            raise ValidationError(f"{path}.{field} must be a non-empty list")
        if not all(isinstance(item, str) and item.strip() for item in value):
            raise ValidationError(f"{path}.{field} must contain only non-empty strings")
    if not isinstance(data["blockers"], list):
        raise ValidationError(f"{path}.blockers must be a list")
    if not isinstance(data["next_step_recommendation"], str) or not data["next_step_recommendation"].strip():
        raise ValidationError(f"{path}.next_step_recommendation must be a non-empty string")

    _validate_no_inference_or_production_approval_claims(data, str(path))
    _validate_no_parity_or_runtime_approval_claims(data, path)


def _validate_musicnn_legacy_baseline_import_order_diagnostic_report(path: Path) -> None:
    data = _load_json(path)

    for field in REQUIRED_MUSICNN_LEGACY_BASELINE_IMPORT_ORDER_DIAGNOSTIC_FIELDS:
        if field not in data:
            raise ValidationError(f"{path} is missing required Roadmap 4.49 field: {field}")

    if data["roadmap"] != "4.49":
        raise ValidationError(f'{path}.roadmap must be "4.49"')
    if data["report_type"] != MUSICNN_LEGACY_BASELINE_IMPORT_ORDER_DIAGNOSTIC_REPORT_TYPE:
        raise ValidationError(
            f'{path}.report_type must be "{MUSICNN_LEGACY_BASELINE_IMPORT_ORDER_DIAGNOSTIC_REPORT_TYPE}"'
        )

    for field in LEGACY_MUSICNN_IMPORT_ORDER_DIAGNOSTIC_TRUE_FIELDS:
        _require_bool_value(data[field], True, f"{path}.{field}")
    for field in LEGACY_MUSICNN_IMPORT_ORDER_DIAGNOSTIC_FALSE_FIELDS:
        _require_bool_value(data[field], False, f"{path}.{field}")

    if data["diagnostic_scope"] != ["import_order_only"]:
        raise ValidationError(f'{path}.diagnostic_scope must be ["import_order_only"]')
    if data["observed_previous_blocker"] != ["ALREADY_EXISTS: Op with name Bitcast"]:
        raise ValidationError(f"{path}.observed_previous_blocker must record the Bitcast blocker")

    diagnostic_cases = data["diagnostic_cases"]
    if not isinstance(diagnostic_cases, list) or len(diagnostic_cases) != 5:
        raise ValidationError(f"{path}.diagnostic_cases must contain the five required import-order cases")

    seen_case_ids: set[str] = set()
    bitcast_case_seen = False
    successful_legacy_relevant_case_seen = False
    for index, case in enumerate(diagnostic_cases):
        context = f"{path}.diagnostic_cases[{index}]"
        if not isinstance(case, dict):
            raise ValidationError(f"{context} must be an object")
        for field in REQUIRED_MUSICNN_LEGACY_BASELINE_IMPORT_ORDER_CASE_FIELDS:
            if field not in case:
                raise ValidationError(f"{context} is missing required field: {field}")

        case_id = case["case_id"]
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValidationError(f"{context}.case_id must be a non-empty string")
        seen_case_ids.add(case_id)

        if not isinstance(case["import_order"], list) or not case["import_order"]:
            raise ValidationError(f"{context}.import_order must be a non-empty list")
        for order_index, import_step in enumerate(case["import_order"]):
            if not isinstance(import_step, str) or not import_step.strip():
                raise ValidationError(f"{context}.import_order[{order_index}] must be a non-empty string")

        if not isinstance(case["exit_code"], int) or isinstance(case["exit_code"], bool):
            raise ValidationError(f"{context}.exit_code must be an integer")
        if not isinstance(case["succeeded"], bool):
            raise ValidationError(f"{context}.succeeded must be a bool")
        if case["error_category"] not in MUSICNN_LEGACY_BASELINE_IMPORT_ORDER_DIAGNOSTIC_ERROR_CATEGORIES:
            raise ValidationError(f"{context}.error_category is not allowed: {case['error_category']!r}")
        if not isinstance(case["bitcast_duplicate_seen"], bool):
            raise ValidationError(f"{context}.bitcast_duplicate_seen must be a bool")
        if not isinstance(case["notes"], str) or not case["notes"].strip():
            raise ValidationError(f"{context}.notes must be a non-empty sanitized string")
        if "\n" in case["notes"]:
            raise ValidationError(f"{context}.notes must not contain raw multiline logs")

        if case["succeeded"]:
            if case["exit_code"] != 0 or case["error_category"] != "none":
                raise ValidationError(f"{context} successful cases must have exit_code 0 and error_category none")
            if case_id in {
                "essentia_then_tensorflow",
                "tensorflow_predict_musicnn_import_without_explicit_tensorflow",
                "legacy_path_like_import_order",
            }:
                successful_legacy_relevant_case_seen = True
        if case["bitcast_duplicate_seen"]:
            bitcast_case_seen = True
            if case["error_category"] != "bitcast_duplicate_registration":
                raise ValidationError(f"{context} Bitcast cases must use bitcast_duplicate_registration")

    required_case_ids = {
        "tensorflow_then_essentia",
        "essentia_then_tensorflow",
        "essentia_standard_only",
        "tensorflow_predict_musicnn_import_without_explicit_tensorflow",
        "legacy_path_like_import_order",
    }
    if seen_case_ids != required_case_ids:
        raise ValidationError(f"{path}.diagnostic_cases must include exactly the required case IDs")

    safe_import_order = _validate_required_object(data, path, "safe_import_order")
    if not isinstance(safe_import_order.get("found"), bool):
        raise ValidationError(f"{path}.safe_import_order.found must be a bool")
    for field in ("recommended_order", "recommended_helper_policy"):
        value = safe_import_order.get(field)
        if not isinstance(value, list):
            raise ValidationError(f"{path}.safe_import_order.{field} must be a list")
        for index, item in enumerate(value):
            if not isinstance(item, str) or not item.strip():
                raise ValidationError(f"{path}.safe_import_order.{field}[{index}] must be a non-empty string")

    decision_status = data["decision_status"]
    if decision_status not in MUSICNN_LEGACY_BASELINE_IMPORT_ORDER_DIAGNOSTIC_DECISION_STATUSES:
        raise ValidationError(f"{path}.decision_status is not allowed: {decision_status!r}")
    blockers = data["blockers"]
    if not isinstance(blockers, list):
        raise ValidationError(f"{path}.blockers must be a list")
    blocker_codes = _collect_blocker_codes(
        blockers,
        MUSICNN_LEGACY_BASELINE_IMPORT_ORDER_DIAGNOSTIC_BLOCKERS,
        f"{path}.blockers",
    )

    if decision_status == "safe_import_order_found":
        _require_bool_value(safe_import_order["found"], True, f"{path}.safe_import_order.found")
        if blockers:
            raise ValidationError(f"{path}.blockers must be empty when a safe import order is found")
        if not successful_legacy_relevant_case_seen:
            raise ValidationError(f"{path} safe_import_order_found requires a successful legacy-relevant case")
        if not safe_import_order["recommended_order"]:
            raise ValidationError(f"{path}.safe_import_order.recommended_order must be non-empty when safe")
    else:
        _require_bool_value(safe_import_order["found"], False, f"{path}.safe_import_order.found")
        if decision_status == "blocked_import_order_unresolved" and "IMPORT_ORDER_UNRESOLVED" not in blocker_codes:
            raise ValidationError(f"{path}.blockers must include IMPORT_ORDER_UNRESOLVED when unresolved")
        if bitcast_case_seen and decision_status == "blocked_import_order_unresolved":
            if "BITCAST_DUPLICATE_REGISTRATION" not in blocker_codes:
                raise ValidationError(f"{path}.blockers must include BITCAST_DUPLICATE_REGISTRATION when observed")

    next_step = data["next_step_recommendation"]
    if not isinstance(next_step, str) or not next_step.strip():
        raise ValidationError(f"{path}.next_step_recommendation must be a non-empty string")

    serialized = json.dumps(data)
    for forbidden_path in ("/tmp/music-tools-onnx-parity", "/opt/music-tools", "tidal-parser"):
        if forbidden_path in serialized:
            raise ValidationError(f"{path} must not publish a forbidden local or repo path: {forbidden_path}")

    _validate_no_inference_or_production_approval_claims(data, str(path))
    _validate_no_parity_or_runtime_approval_claims(data, path)


def _validate_no_inference_or_production_approval_claims(value: Any, context: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            item_context = f"{context}.{key}"
            normalized_key = key.strip().casefold()
            if normalized_key in LOCAL_ARTIFACT_APPROVAL_FLAG_FIELDS and item is True:
                raise ValidationError(f"{item_context} must not assert inference or production approval")
            if (
                isinstance(item, str)
                and ("approved" in normalized_key or "approval" in normalized_key or "status" in normalized_key)
                and item.strip().casefold() in PRODUCTION_APPROVED_STATUSES | {"approved"}
            ):
                raise ValidationError(f"{item_context} must not assert inference or production approval")
            _validate_no_inference_or_production_approval_claims(item, item_context)
        return

    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_no_inference_or_production_approval_claims(item, f"{context}[{index}]")


def _validate_sample_local_artifact(artifact: dict[str, Any], context: str) -> str:
    for field in REQUIRED_LOCAL_ARTIFACT_FIELDS:
        if field not in artifact:
            raise ValidationError(f"{context} is missing required field: {field}")

    role = artifact["artifact_role"]
    if not isinstance(role, str) or not role.strip():
        raise ValidationError(f"{context}.artifact_role must be a non-empty string")

    if not isinstance(artifact["artifact_name"], str) or not artifact["artifact_name"].strip():
        raise ValidationError(f"{context}.artifact_name must be a non-empty string")
    if artifact["artifact_downloaded"] is not False:
        raise ValidationError(f"{context}.artifact_downloaded must be false")
    if artifact["artifact_in_repo"] is not False:
        raise ValidationError(f"{context}.artifact_in_repo must be false")
    if artifact["committed_to_repo"] is not False:
        raise ValidationError(f"{context}.committed_to_repo must be false")
    if artifact["local_path"] is not None:
        raise ValidationError(f"{context}.local_path must be null in the sample report")
    if artifact["file_size_bytes"] is not None:
        raise ValidationError(f"{context}.file_size_bytes must be null in the sample report")

    sha256 = artifact["sha256"]
    if sha256 is not None:
        if isinstance(sha256, str) and _is_fake_or_placeholder_hash(sha256):
            raise ValidationError(f"{context}.sha256 must not be a fake placeholder hash")
        raise ValidationError(f"{context}.sha256 must be null in the sample report")

    return role


def _validate_local_artifact_evidence_report(path: Path) -> None:
    data = _load_json(path)

    for field in REQUIRED_LOCAL_ARTIFACT_EVIDENCE_REPORT_FIELDS:
        if field not in data:
            raise ValidationError(f"{path} is missing required local artifact evidence report field: {field}")

    for field in LOCAL_ARTIFACT_EVIDENCE_REPORT_STRING_FIELDS:
        value = data[field]
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{path}.{field} must be a non-empty string")

    if data["report_type"] != LOCAL_ARTIFACT_EVIDENCE_REPORT_TYPE:
        raise ValidationError(f'{path}.report_type must be "{LOCAL_ARTIFACT_EVIDENCE_REPORT_TYPE}"')
    if data["sample_only"] is not True:
        raise ValidationError(f"{path}.sample_only must be true")
    if data["not_production_decision"] is not True:
        raise ValidationError(f"{path}.not_production_decision must be true")
    if data["approved_for_inference"] is not False:
        raise ValidationError(f"{path}.approved_for_inference must be false")
    if data["approved_for_production"] is not False:
        raise ValidationError(f"{path}.approved_for_production must be false")

    review_status = data["review_status"].strip().casefold()
    if review_status not in LOCAL_ARTIFACT_EVIDENCE_REPORT_REVIEW_STATUSES:
        raise ValidationError(f"{path}.review_status must be a documented non-approved status")
    if review_status in PRODUCTION_APPROVED_STATUSES | {"approved"}:
        raise ValidationError(f"{path}.review_status must not be approved")

    _validate_required_list_container(data, path, "warnings")
    _validate_required_list_container(data, path, "no_go_items")
    _validate_warnings(data, str(path))

    artifacts = data["artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        raise ValidationError(f"{path}.artifacts must be a non-empty list")

    artifacts_by_role: dict[str, dict[str, Any]] = {}
    for index, artifact in enumerate(artifacts):
        context = f"{path}.artifacts[{index}]"
        if not isinstance(artifact, dict):
            raise ValidationError(f"{context} must be an object")

        role = _validate_sample_local_artifact(artifact, context)
        if role in artifacts_by_role:
            raise ValidationError(f"{context}.artifact_role must be unique: {role!r}")
        artifacts_by_role[role] = artifact

    missing_roles = set(REQUIRED_LOCAL_ARTIFACT_ROLES) - set(artifacts_by_role)
    if missing_roles:
        raise ValidationError(f"{path}.artifacts missing required roles: {sorted(missing_roles)}")

    _validate_no_inference_or_production_approval_claims(data, str(path))


def _validate_real_official_local_artifact(artifact: dict[str, Any], context: str) -> None:
    if artifact.get("local_only") is not True:
        raise ValidationError(f"{context}.local_only must be true for official/local artifacts")

    local_path = artifact.get("local_path")
    if not isinstance(local_path, str) or not local_path.startswith("/tmp/music-tools-onnx-parity/"):
        raise ValidationError(f"{context}.local_path must start with /tmp/music-tools-onnx-parity/")
    if any(
        local_path == prefix.rstrip("/") or local_path.startswith(prefix)
        for prefix in LOCAL_ARTIFACT_REPO_PATH_PREFIXES
    ):
        raise ValidationError(f"{context}.local_path must not point inside the repository")

    if artifact.get("artifact_in_repo") is not False:
        raise ValidationError(f"{context}.artifact_in_repo must be false for official/local artifacts")
    if artifact.get("committed_to_repo") is not False:
        raise ValidationError(f"{context}.committed_to_repo must be false for official/local artifacts")

    _validate_positive_integer(artifact.get("file_size_bytes"), f"{context}.file_size_bytes")
    _validate_sha256(artifact.get("sha256"), f"{context}.sha256")


def _validate_real_current_bundled_artifact(artifact: dict[str, Any], context: str) -> None:
    if artifact.get("source_reference_type") != "existing_service_runtime_baseline":
        raise ValidationError(f"{context}.source_reference_type must mark the current production baseline")
    if artifact.get("artifact_downloaded") is not False:
        raise ValidationError(f"{context}.artifact_downloaded must be false for current bundled baselines")
    if artifact.get("downloaded_manually") is not False:
        raise ValidationError(f"{context}.downloaded_manually must be false for current bundled baselines")
    if artifact.get("local_only") is not False:
        raise ValidationError(f"{context}.local_only must be false for current bundled baselines")

    verification_results = artifact.get("verification_results")
    if not isinstance(verification_results, dict):
        raise ValidationError(f"{context}.verification_results must be an object")
    if verification_results.get("existing_production_baseline_artifact") is not True:
        raise ValidationError(f"{context}.verification_results must mark the current production baseline")
    if verification_results.get("newly_downloaded") is not False:
        raise ValidationError(f"{context}.verification_results.newly_downloaded must be false")
    if verification_results.get("official_local_temp_artifact") is not False:
        raise ValidationError(f"{context}.verification_results.official_local_temp_artifact must be false")

    _validate_positive_integer(artifact.get("file_size_bytes"), f"{context}.file_size_bytes")
    _validate_sha256(artifact.get("sha256"), f"{context}.sha256")


def _validate_real_local_artifact_evidence_report(path: Path) -> None:
    data = _load_json(path)

    for field in REQUIRED_REAL_LOCAL_ARTIFACT_EVIDENCE_REPORT_FIELDS:
        if field not in data:
            raise ValidationError(f"{path} is missing required real local artifact evidence report field: {field}")

    for field in REAL_LOCAL_ARTIFACT_EVIDENCE_REPORT_STRING_FIELDS:
        value = data[field]
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{path}.{field} must be a non-empty string")

    if data["report_type"] != REAL_LOCAL_ARTIFACT_EVIDENCE_REPORT_TYPE:
        raise ValidationError(f'{path}.report_type must be "{REAL_LOCAL_ARTIFACT_EVIDENCE_REPORT_TYPE}"')
    if data.get("sample_only", False) is not False:
        raise ValidationError(f"{path}.sample_only must be absent or false")
    if data["not_production_decision"] is not True:
        raise ValidationError(f"{path}.not_production_decision must be true")
    if data["approved_for_inference"] is not False:
        raise ValidationError(f"{path}.approved_for_inference must be false")
    if data["approved_for_production"] is not False:
        raise ValidationError(f"{path}.approved_for_production must be false")
    if data["approval_status"] != "local_artifact_preparation_only":
        raise ValidationError(f'{path}.approval_status must be "local_artifact_preparation_only"')

    review_status = data["review_status"].strip().casefold()
    if review_status not in REAL_LOCAL_ARTIFACT_EVIDENCE_REPORT_REVIEW_STATUSES:
        raise ValidationError(f"{path}.review_status must be a documented non-production status")

    next_step = data["next_step_recommendation"].strip().casefold()
    if any(term in next_step for term in ("approve inference", "approve production", "production migration")):
        raise ValidationError(f"{path}.next_step_recommendation must not look like approval")

    _validate_required_list_container(data, path, "verification_commands")
    _validate_required_list_container(data, path, "warnings")
    _validate_required_list_container(data, path, "no_go_items")
    _validate_warnings(data, str(path))

    if not isinstance(data["verification_results"], dict) or not data["verification_results"]:
        raise ValidationError(f"{path}.verification_results must be a non-empty object")

    artifacts = data["artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        raise ValidationError(f"{path}.artifacts must be a non-empty list")

    artifacts_by_role: dict[str, dict[str, Any]] = {}
    for index, artifact in enumerate(artifacts):
        context = f"{path}.artifacts[{index}]"
        if not isinstance(artifact, dict):
            raise ValidationError(f"{context} must be an object")

        role = artifact.get("artifact_role")
        if not isinstance(role, str) or not role.strip():
            raise ValidationError(f"{context}.artifact_role must be a non-empty string")
        if role in artifacts_by_role:
            raise ValidationError(f"{context}.artifact_role must be unique: {role!r}")
        artifacts_by_role[role] = artifact

        for field in ("artifact_name", "local_path", "file_size_bytes", "sha256", "verification_results"):
            if field not in artifact:
                raise ValidationError(f"{context} is missing required field: {field}")

    required_roles = set(REQUIRED_LOCAL_ARTIFACT_ROLES)
    if "optional_official_local_pb" in artifacts_by_role:
        required_roles.add("optional_official_local_pb")
    missing_roles = required_roles - set(artifacts_by_role)
    if missing_roles:
        raise ValidationError(f"{path}.artifacts missing required roles: {sorted(missing_roles)}")

    for role in OFFICIAL_LOCAL_ARTIFACT_ROLES:
        if role in artifacts_by_role:
            _validate_real_official_local_artifact(artifacts_by_role[role], f"{path}.artifacts[{role}]")

    for role in ("current_bundled_pb", "current_bundled_json"):
        _validate_real_current_bundled_artifact(artifacts_by_role[role], f"{path}.artifacts[{role}]")

    for role, expected_hash in EXPECTED_REAL_LOCAL_ARTIFACT_HASHES.items():
        actual_hash = artifacts_by_role[role]["sha256"]
        if actual_hash != expected_hash:
            raise ValidationError(f"{path}.artifacts[{role}].sha256 must match the measured Roadmap 4.30 hash")

    official_pb_hash = artifacts_by_role["optional_official_local_pb"]["sha256"]
    current_pb_hash = artifacts_by_role["current_bundled_pb"]["sha256"]
    if official_pb_hash != current_pb_hash:
        raise ValidationError(f"{path} must record official/local PB sha256 matching current bundled PB")

    official_json_hash = artifacts_by_role["official_local_json"]["sha256"]
    current_json_hash = artifacts_by_role["current_bundled_json"]["sha256"]
    if official_json_hash == current_json_hash:
        raise ValidationError(f"{path} must record official/local JSON sha256 differing from current bundled JSON")

    normalized_text_values = [_normalize_report_text(text) for text in _iter_text_values(data)]
    has_pb_match_observation = _has_true_key(
        data, "current_bundled_pb_matches_official_local_pb_sha256"
    ) or _has_true_key(data, "matches_current_bundled_pb_sha256")
    has_pb_match_observation = has_pb_match_observation or any(
        ("pb sha256 match" in text or "pb hash match" in text or "pb sha256 matches" in text)
        for text in normalized_text_values
    )
    if not has_pb_match_observation:
        raise ValidationError(f"{path} must include a PB hash match observation")

    report_text = " ".join(normalized_text_values)
    if not (
        "json differs" in report_text
        and "evidence gap" in report_text
        and "not parity evidence" in report_text
    ):
        raise ValidationError(f"{path} must include a JSON mismatch warning/evidence gap")

    _validate_no_inference_or_production_approval_claims(data, str(path))
    _validate_no_parity_or_runtime_approval_claims(data, path)


def _validate_local_artifact_metadata_template(path: Path) -> None:
    data = _load_json(path)

    for field in REQUIRED_LOCAL_ARTIFACT_METADATA_FIELDS:
        if field not in data:
            raise ValidationError(f"{path} is missing required local artifact metadata field: {field}")

    for field in LOCAL_ARTIFACT_METADATA_STRING_FIELDS:
        value = data[field]
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{path}.{field} must be a non-empty string")

    if data["report_type"] != "local_musicnn_onnx_artifact_metadata_template":
        raise ValidationError(f'{path}.report_type must be "local_musicnn_onnx_artifact_metadata_template"')
    if data["not_production_decision"] is not True:
        raise ValidationError(f"{path}.not_production_decision must be true")
    if data["approved_for_inference"] is not False:
        raise ValidationError(f"{path}.approved_for_inference must be false")
    if data["approved_for_production"] is not False:
        raise ValidationError(f"{path}.approved_for_production must be false")

    _validate_required_list_container(data, path, "warnings")
    _validate_required_list_container(data, path, "no_go_items")
    _validate_warnings(data, str(path))

    validation_status = data["validation_status"]
    if not isinstance(validation_status, dict):
        raise ValidationError(f"{path}.validation_status must be an object")
    for field, expected_value in REQUIRED_LOCAL_ARTIFACT_VALIDATION_STATUS.items():
        if validation_status.get(field) is not expected_value:
            expected_text = str(expected_value).lower()
            raise ValidationError(f"{path}.validation_status.{field} must be {expected_text}")
    for field, value in validation_status.items():
        if "approved" in field.casefold() and value is True:
            raise ValidationError(f"{path}.validation_status must not record approved state")
        if isinstance(value, str) and value.strip().casefold() in PRODUCTION_APPROVED_STATUSES | {"approved"}:
            raise ValidationError(f"{path}.validation_status must not record approved state")

    artifacts = data["artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        raise ValidationError(f"{path}.artifacts must be a non-empty list")

    artifacts_by_role: dict[str, dict[str, Any]] = {}
    for index, artifact in enumerate(artifacts):
        context = f"{path}.artifacts[{index}]"
        if not isinstance(artifact, dict):
            raise ValidationError(f"{context} must be an object")
        for field in REQUIRED_LOCAL_ARTIFACT_FIELDS:
            if field not in artifact:
                raise ValidationError(f"{context} is missing required field: {field}")

        role = artifact["artifact_role"]
        if not isinstance(role, str) or not role.strip():
            raise ValidationError(f"{context}.artifact_role must be a non-empty string")
        if role in artifacts_by_role:
            raise ValidationError(f"{context}.artifact_role must be unique: {role!r}")
        artifacts_by_role[role] = artifact

        if not isinstance(artifact["artifact_name"], str) or not artifact["artifact_name"].strip():
            raise ValidationError(f"{context}.artifact_name must be a non-empty string")
        if artifact["artifact_downloaded"] is not False:
            raise ValidationError(f"{context}.artifact_downloaded must be false")
        if artifact["artifact_in_repo"] is not False:
            raise ValidationError(f"{context}.artifact_in_repo must be false")
        if artifact["committed_to_repo"] is not False:
            raise ValidationError(f"{context}.committed_to_repo must be false")
        if artifact["file_size_bytes"] is not None:
            raise ValidationError(f"{context}.file_size_bytes must be null in the template")

        sha256 = artifact["sha256"]
        if sha256 is not None:
            if not isinstance(sha256, str):
                raise ValidationError(f"{context}.sha256 must be null in the template")
            normalized_sha = sha256.strip().casefold()
            if normalized_sha in LOCAL_ARTIFACT_PLACEHOLDER_HASHES:
                raise ValidationError(f"{context}.sha256 must not be a fake placeholder hash")
            raise ValidationError(f"{context}.sha256 must be null in the template")

        if role in OFFICIAL_LOCAL_ARTIFACT_ROLES:
            if artifact["local_only"] is not True:
                raise ValidationError(f"{context}.local_only must be true for official/local artifacts")
            local_path = artifact["local_path"]
            if local_path is None:
                continue
            if not isinstance(local_path, str) or not local_path.strip():
                raise ValidationError(f"{context}.local_path must be null or an explicit placeholder path")

            normalized_path = local_path.strip()
            if any(
                normalized_path == prefix.rstrip("/") or normalized_path.startswith(prefix)
                for prefix in LOCAL_ARTIFACT_REPO_PATH_PREFIXES
            ):
                raise ValidationError(f"{context}.local_path must not point inside the repository")
            if "placeholder" not in normalized_path.casefold() and "example" not in normalized_path.casefold():
                raise ValidationError(f"{context}.local_path must be null or explicitly placeholder/example-only")

    missing_roles = set(REQUIRED_LOCAL_ARTIFACT_ROLES) - set(artifacts_by_role)
    if missing_roles:
        raise ValidationError(f"{path}.artifacts missing required roles: {sorted(missing_roles)}")


def _validate_fixture_manifest_template(path: Path) -> None:
    data = _load_json(path)

    for field in REQUIRED_FIXTURE_MANIFEST_TEMPLATE_FIELDS:
        if field not in data:
            raise ValidationError(f"{path} is missing required fixture manifest template field: {field}")

    if data["manifest_type"] != FIXTURE_MANIFEST_TEMPLATE_TYPE:
        raise ValidationError(f'{path}.manifest_type must be "{FIXTURE_MANIFEST_TEMPLATE_TYPE}"')
    if data["approval_status"] != "template_only_not_approved":
        raise ValidationError(f'{path}.approval_status must be "template_only_not_approved"')

    expected_top_level_flags = {
        "template_only": True,
        "not_production_decision": True,
        "approved_for_inference": False,
        "approved_for_production": False,
        "approved_for_local_parity_evaluation": False,
        "approved_for_repo_inclusion": False,
        "audio_files_in_repo": False,
        "real_audio_fixtures_included": False,
        "fixture_manifest_approved": False,
    }
    for field, expected_value in expected_top_level_flags.items():
        _require_bool_value(data[field], expected_value, f"{path}.{field}")

    storage_policy = _validate_required_object(data, path, "fixture_storage_policy")
    if storage_policy["recommended_local_fixture_root"] != "/tmp/music-tools-onnx-parity/fixtures/":
        raise ValidationError(f"{path}.fixture_storage_policy must recommend /tmp/music-tools-onnx-parity/fixtures/")
    _require_bool_value(
        storage_policy["audio_files_must_remain_outside_repo"],
        True,
        f"{path}.fixture_storage_policy.audio_files_must_remain_outside_repo",
    )

    forbidden_paths = storage_policy["forbidden_paths"]
    if not isinstance(forbidden_paths, list):
        raise ValidationError(f"{path}.fixture_storage_policy.forbidden_paths must be a list")
    for marker in FIXTURE_FORBIDDEN_PATH_MARKERS:
        if marker not in forbidden_paths:
            raise ValidationError(f"{path}.fixture_storage_policy.forbidden_paths must include {marker!r}")

    required_fields = data["required_fixture_fields"]
    if not isinstance(required_fields, list):
        raise ValidationError(f"{path}.required_fixture_fields must be a list")
    missing_fixture_fields = set(REQUIRED_FIXTURE_FIELDS) - set(required_fields)
    if missing_fixture_fields:
        raise ValidationError(f"{path}.required_fixture_fields missing fields: {sorted(missing_fixture_fields)}")

    categories = data["fixture_categories"]
    if not isinstance(categories, list):
        raise ValidationError(f"{path}.fixture_categories must be a list")
    missing_categories = set(FIXTURE_CATEGORIES) - set(categories)
    if missing_categories:
        raise ValidationError(f"{path}.fixture_categories missing categories: {sorted(missing_categories)}")

    sample_fixture = _validate_required_object(data, path, "sample_fixture")
    for field in REQUIRED_FIXTURE_FIELDS:
        if field not in sample_fixture:
            raise ValidationError(f"{path}.sample_fixture is missing required field: {field}")

    if sample_fixture["fixture_id"] != "template-placeholder":
        raise ValidationError(f'{path}.sample_fixture.fixture_id must be "template-placeholder"')
    for field in (
        "local_path",
        "duration_seconds",
        "file_size_bytes",
        "sha256",
        "audio_format",
        "sample_rate_hz",
        "channels",
        "source_type",
        "license_status",
        "usage_permission",
        "provenance_notes",
        "expected_quality_notes",
        "category",
    ):
        if sample_fixture[field] is not None:
            raise ValidationError(f"{path}.sample_fixture.{field} must be null in the template")

    for field, expected_value in {
        "local_only": True,
        "artifact_in_repo": False,
        "committed_to_repo": False,
        "approved_for_local_parity_evaluation": False,
        "approved_for_repo_inclusion": False,
    }.items():
        _require_bool_value(sample_fixture[field], expected_value, f"{path}.sample_fixture.{field}")

    if sample_fixture["tags"] != []:
        raise ValidationError(f"{path}.sample_fixture.tags must be an empty list")

    _validate_no_inference_or_production_approval_claims(data, str(path))
    _validate_no_parity_or_runtime_approval_claims(data, path)


def _validate_label_mapping(path: Path) -> None:
    data = _load_json(path)

    for field in REQUIRED_LABEL_MAPPING_FIELDS:
        if field not in data:
            raise ValidationError(f"{path} is missing required label mapping field: {field}")

    for field in LABEL_MAPPING_STRING_FIELDS:
        value = data[field]
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{path}.{field} must be a non-empty string")

    label_count = data["label_count"]
    if not isinstance(label_count, int) or isinstance(label_count, bool) or label_count < 0:
        raise ValidationError(f"{path}.label_count must be a non-negative integer")

    labels = data["labels"]
    if not isinstance(labels, list) or not labels:
        raise ValidationError(f"{path}.labels must be a non-empty list")
    if len(labels) != label_count:
        raise ValidationError(f"{path}.label_count must match labels length")

    for field in ("unmapped_labels", "warnings"):
        if not isinstance(data[field], list):
            raise ValidationError(f"{path}.{field} must be a list")

    _validate_warnings(data, str(path))

    approval_status = data["approval_status"].strip()
    if approval_status not in LABEL_MAPPING_APPROVAL_STATUSES:
        raise ValidationError(f"{path}.approval_status is not a documented label mapping status")

    raw_indexes: set[int] = set()
    seen_decisions: set[str] = set()
    for index, item in enumerate(labels):
        item_context = f"{path}.labels[{index}]"
        if not isinstance(item, dict):
            raise ValidationError(f"{item_context} must be an object")

        for field in REQUIRED_LABEL_MAPPING_LABEL_FIELDS:
            if field not in item:
                raise ValidationError(f"{item_context} is missing required field: {field}")

        raw_label = item["raw_label"]
        if not isinstance(raw_label, str) or not raw_label.strip():
            raise ValidationError(f"{item_context}.raw_label must be a non-empty string")

        raw_index = item["raw_index"]
        if not isinstance(raw_index, int) or isinstance(raw_index, bool) or raw_index < 0:
            raise ValidationError(f"{item_context}.raw_index must be a non-negative integer")
        if raw_index in raw_indexes:
            raise ValidationError(f"{item_context}.raw_index must be unique")
        raw_indexes.add(raw_index)

        for field in ("mapped_genre", "mapped_confidence", "mapping_notes"):
            if not isinstance(item[field], str):
                raise ValidationError(f"{item_context}.{field} must be a string")

        decision = item["mapping_decision"]
        if decision not in LABEL_MAPPING_DECISIONS:
            raise ValidationError(f"{item_context}.mapping_decision is not allowed: {decision!r}")
        seen_decisions.add(decision)

        if decision in {"mapped", "alias_mapped"} and not item["mapped_genre"].strip():
            raise ValidationError(f"{item_context}.mapped_genre must be non-empty for mapped decisions")
        if decision in {"ignored_non_genre", "unmapped", "rejected_ambiguous"} and item["mapped_genre"].strip():
            raise ValidationError(f"{item_context}.mapped_genre must be empty for non-mapped decisions")

    missing_decisions = LABEL_MAPPING_DECISIONS - seen_decisions
    if missing_decisions:
        raise ValidationError(f"{path}.labels does not demonstrate decisions: {sorted(missing_decisions)}")


def _validate_evidence_package(path: Path) -> None:
    data = _load_json(path)

    for field in REQUIRED_EVIDENCE_PACKAGE_FIELDS:
        if field not in data:
            raise ValidationError(f"{path} is missing required evidence package field: {field}")

    for field in EVIDENCE_PACKAGE_STRING_FIELDS:
        value = data[field]
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{path}.{field} must be a non-empty string")

    if data["package_type"] != EVIDENCE_PACKAGE_TYPE:
        raise ValidationError(f'{path}.package_type must be "{EVIDENCE_PACKAGE_TYPE}"')

    if data["decision_status"] not in EVIDENCE_DECISION_STATUSES:
        raise ValidationError(f"{path}.decision_status is not allowed: {data['decision_status']!r}")

    if data["not_production_decision"] is not True:
        raise ValidationError(f"{path}.not_production_decision must be true")

    artifacts = data["artifacts"]
    if not isinstance(artifacts, dict):
        raise ValidationError(f"{path}.artifacts must be an object")

    for field in EVIDENCE_PACKAGE_ARTIFACT_PATH_FIELDS:
        value = data[field]
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{path}.{field} must be a non-empty string path")

        artifact_value = artifacts.get(field)
        if artifact_value is not None and artifact_value != value:
            raise ValidationError(f"{path}.artifacts.{field} must match {field}")

    validation = data["validation"]
    if not isinstance(validation, dict):
        raise ValidationError(f"{path}.validation must be an object")
    for field in ("validator_command", "validator_result", "tests_command", "tests_result"):
        if field not in validation:
            raise ValidationError(f"{path}.validation is missing required field: {field}")
        if validation[field] != data[field]:
            raise ValidationError(f"{path}.validation.{field} must match {field}")

    approvals = data["approvals"]
    if not isinstance(approvals, dict):
        raise ValidationError(f"{path}.approvals must be an object")

    for field in EVIDENCE_PACKAGE_LIST_FIELDS:
        if not isinstance(data[field], list):
            raise ValidationError(f"{path}.{field} must be a list")


def _extract_genre_tags(value: dict[str, Any]) -> set[str]:
    fixture_results = value.get("fixture_results")
    if isinstance(fixture_results, list):
        results = fixture_results
    else:
        results = [value]

    tags: set[str] = set()
    for result in results:
        if not isinstance(result, dict):
            continue
        genres = result.get("genres")
        if not isinstance(genres, list):
            continue
        for item in genres:
            if not isinstance(item, dict):
                continue
            tag = item.get("tag")
            if isinstance(tag, str) and tag.strip():
                tags.add(tag.strip().casefold())
    return tags


def compare_genre_overlap(baseline: dict[str, Any], candidate: dict[str, Any]) -> GenreOverlapSummary:
    baseline_tags = _extract_genre_tags(baseline)
    candidate_tags = _extract_genre_tags(candidate)
    overlap_count = len(baseline_tags & candidate_tags)
    denominator = max(len(baseline_tags), len(candidate_tags))
    overlap_ratio = overlap_count / denominator if denominator else 0.0

    return GenreOverlapSummary(
        baseline_count=len(baseline_tags),
        candidate_count=len(candidate_tags),
        overlap_count=overlap_count,
        overlap_ratio=overlap_ratio,
        baseline_empty=not baseline_tags,
        candidate_empty=not candidate_tags,
    )


def compare_output_files(baseline_path: Path, candidate_path: Path) -> GenreOverlapSummary:
    return compare_genre_overlap(_load_json(baseline_path), _load_json(candidate_path))


def validate_all(root: Path) -> ValidationSummary:
    evaluation_root = root / EVALUATION_DIR
    for relative_path in REQUIRED_FILES:
        _read_non_empty_text(evaluation_root / relative_path)

    readme_path = evaluation_root / "README.md"
    _validate_markers(readme_path, _read_non_empty_text(readme_path), README_MARKERS)

    manifest_path = evaluation_root / "manifests/example-manifest.yaml"
    manifest_text = _read_non_empty_text(manifest_path)
    # Full YAML schema validation is a future step for the real offline harness.
    _validate_markers(manifest_path, manifest_text, MANIFEST_MARKERS)

    report_path = evaluation_root / "reports/example-evaluation-report.md"
    _validate_report(report_path)

    fixture_result_count = 0
    for relative_path in OUTPUT_FILES:
        fixture_result_count += _validate_output(evaluation_root / relative_path)

    model_provenance_count = 0
    for relative_path in MODEL_PROVENANCE_FILES:
        _validate_model_provenance(evaluation_root / relative_path)
        model_provenance_count += 1

    local_artifact_metadata_count = 0
    for relative_path in LOCAL_ARTIFACT_METADATA_FILES:
        _validate_local_artifact_metadata_template(evaluation_root / relative_path)
        local_artifact_metadata_count += 1

    local_artifact_evidence_report_count = 0
    for relative_path in LOCAL_ARTIFACT_EVIDENCE_REPORT_FILES:
        _validate_local_artifact_evidence_report(evaluation_root / relative_path)
        local_artifact_evidence_report_count += 1

    real_local_artifact_evidence_report_count = 0
    for relative_path in REAL_LOCAL_ARTIFACT_EVIDENCE_REPORT_FILES:
        _validate_real_local_artifact_evidence_report(evaluation_root / relative_path)
        real_local_artifact_evidence_report_count += 1

    fixture_manifest_template_count = 0
    for relative_path in FIXTURE_MANIFEST_TEMPLATE_FILES:
        _validate_fixture_manifest_template(evaluation_root / relative_path)
        fixture_manifest_template_count += 1

    parity_scaffold_dry_run_output_count = 0
    for relative_path in PARITY_SCAFFOLD_DRY_RUN_OUTPUT_FILES:
        _validate_parity_scaffold_dry_run_output(evaluation_root / relative_path)
        parity_scaffold_dry_run_output_count += 1

    musicnn_onnx_parity_spike_report_count = 0
    for relative_path in MUSICNN_ONNX_PARITY_SPIKE_REPORT_FILES:
        _validate_musicnn_onnx_parity_spike_report(evaluation_root / relative_path)
        musicnn_onnx_parity_spike_report_count += 1

    musicnn_onnx_parity_environment_preparation_report_count = 0
    for relative_path in MUSICNN_ONNX_PARITY_ENVIRONMENT_PREPARATION_REPORT_FILES:
        _validate_musicnn_onnx_parity_environment_preparation_report(evaluation_root / relative_path)
        musicnn_onnx_parity_environment_preparation_report_count += 1

    musicnn_onnx_fixtures_and_baseline_runtime_decision_report_count = 0
    for relative_path in MUSICNN_ONNX_FIXTURES_AND_BASELINE_RUNTIME_DECISION_REPORT_FILES:
        _validate_musicnn_onnx_fixtures_and_baseline_runtime_decision_report(evaluation_root / relative_path)
        musicnn_onnx_fixtures_and_baseline_runtime_decision_report_count += 1

    musicnn_onnx_fixture_set_and_baseline_runtime_strategy_report_count = 0
    for relative_path in MUSICNN_ONNX_FIXTURE_SET_AND_BASELINE_RUNTIME_STRATEGY_REPORT_FILES:
        _validate_musicnn_onnx_fixture_set_and_baseline_runtime_strategy_report(evaluation_root / relative_path)
        musicnn_onnx_fixture_set_and_baseline_runtime_strategy_report_count += 1

    musicnn_onnx_fixtures_and_scoped_baseline_capture_approval_report_count = 0
    for relative_path in MUSICNN_ONNX_FIXTURES_AND_SCOPED_BASELINE_CAPTURE_APPROVAL_REPORT_FILES:
        _validate_musicnn_onnx_fixtures_and_scoped_baseline_capture_approval_report(
            evaluation_root / relative_path
        )
        musicnn_onnx_fixtures_and_scoped_baseline_capture_approval_report_count += 1

    musicnn_onnx_fixture_placement_and_scoped_baseline_readiness_report_count = 0
    for relative_path in MUSICNN_ONNX_FIXTURE_PLACEMENT_AND_SCOPED_BASELINE_READINESS_REPORT_FILES:
        _validate_musicnn_onnx_fixture_placement_and_scoped_baseline_readiness_report(
            evaluation_root / relative_path
        )
        musicnn_onnx_fixture_placement_and_scoped_baseline_readiness_report_count += 1

    musicnn_legacy_baseline_capture_report_count = 0
    for relative_path in MUSICNN_LEGACY_BASELINE_CAPTURE_REPORT_FILES:
        _validate_musicnn_legacy_baseline_capture_report(evaluation_root / relative_path)
        musicnn_legacy_baseline_capture_report_count += 1

    musicnn_onnx_preprocessing_alignment_report_count = 0
    for relative_path in MUSICNN_ONNX_PREPROCESSING_ALIGNMENT_REPORT_FILES:
        _validate_musicnn_onnx_preprocessing_alignment_report(evaluation_root / relative_path)
        musicnn_onnx_preprocessing_alignment_report_count += 1

    musicnn_onnx_pragmatic_preprocessing_prototype_report_count = 0
    for relative_path in MUSICNN_ONNX_PRAGMATIC_PREPROCESSING_PROTOTYPE_REPORT_FILES:
        _validate_musicnn_onnx_pragmatic_preprocessing_prototype_report(evaluation_root / relative_path)
        musicnn_onnx_pragmatic_preprocessing_prototype_report_count += 1

    musicnn_tensorflow_input_musiccnn_availability_probe_report_count = 0
    for relative_path in MUSICNN_TENSORFLOW_INPUT_MUSICCNN_AVAILABILITY_PROBE_REPORT_FILES:
        _validate_musicnn_tensorflow_input_musiccnn_availability_probe_report(evaluation_root / relative_path)
        musicnn_tensorflow_input_musiccnn_availability_probe_report_count += 1

    musicnn_onnx_output_capture_report_count = 0
    for relative_path in MUSICNN_ONNX_OUTPUT_CAPTURE_REPORT_FILES:
        _validate_musicnn_onnx_output_capture_report(evaluation_root / relative_path)
        musicnn_onnx_output_capture_report_count += 1

    musicnn_onnx_fixture_visibility_strategy_report_count = 0
    for relative_path in MUSICNN_ONNX_FIXTURE_VISIBILITY_STRATEGY_REPORT_FILES:
        _validate_musicnn_onnx_fixture_visibility_strategy_report(evaluation_root / relative_path)
        musicnn_onnx_fixture_visibility_strategy_report_count += 1

    musicnn_legacy_baseline_import_order_diagnostic_report_count = 0
    for relative_path in MUSICNN_LEGACY_BASELINE_IMPORT_ORDER_DIAGNOSTIC_REPORT_FILES:
        _validate_musicnn_legacy_baseline_import_order_diagnostic_report(evaluation_root / relative_path)
        musicnn_legacy_baseline_import_order_diagnostic_report_count += 1

    label_mapping_count = 0
    for relative_path in LABEL_MAPPING_FILES:
        _validate_label_mapping(evaluation_root / relative_path)
        label_mapping_count += 1

    evidence_package_count = 0
    for relative_path in EVIDENCE_PACKAGE_FILES:
        _validate_evidence_package(evaluation_root / relative_path)
        evidence_package_count += 1

    return ValidationSummary(
        files_checked=len(REQUIRED_FILES),
        json_outputs_checked=len(OUTPUT_FILES),
        fixture_results_checked=fixture_result_count,
        model_provenance_checked=model_provenance_count,
        local_artifact_metadata_checked=local_artifact_metadata_count,
        local_artifact_evidence_reports_checked=local_artifact_evidence_report_count,
        real_local_artifact_evidence_reports_checked=real_local_artifact_evidence_report_count,
        parity_scaffold_dry_run_outputs_checked=parity_scaffold_dry_run_output_count,
        musicnn_onnx_parity_spike_reports_checked=musicnn_onnx_parity_spike_report_count,
        musicnn_onnx_parity_environment_preparation_reports_checked=(
            musicnn_onnx_parity_environment_preparation_report_count
        ),
        musicnn_onnx_fixtures_and_baseline_runtime_decision_reports_checked=(
            musicnn_onnx_fixtures_and_baseline_runtime_decision_report_count
        ),
        musicnn_onnx_fixture_set_and_baseline_runtime_strategy_reports_checked=(
            musicnn_onnx_fixture_set_and_baseline_runtime_strategy_report_count
        ),
        musicnn_onnx_fixtures_and_scoped_baseline_capture_approval_reports_checked=(
            musicnn_onnx_fixtures_and_scoped_baseline_capture_approval_report_count
        ),
        musicnn_onnx_fixture_placement_and_scoped_baseline_readiness_reports_checked=(
            musicnn_onnx_fixture_placement_and_scoped_baseline_readiness_report_count
        ),
        musicnn_legacy_baseline_capture_reports_checked=musicnn_legacy_baseline_capture_report_count,
        musicnn_onnx_preprocessing_alignment_reports_checked=(
            musicnn_onnx_preprocessing_alignment_report_count
        ),
        musicnn_onnx_pragmatic_preprocessing_prototype_reports_checked=(
            musicnn_onnx_pragmatic_preprocessing_prototype_report_count
        ),
        musicnn_tensorflow_input_musiccnn_availability_probe_reports_checked=(
            musicnn_tensorflow_input_musiccnn_availability_probe_report_count
        ),
        musicnn_onnx_output_capture_reports_checked=musicnn_onnx_output_capture_report_count,
        musicnn_onnx_fixture_visibility_strategy_reports_checked=(
            musicnn_onnx_fixture_visibility_strategy_report_count
        ),
        musicnn_legacy_baseline_import_order_diagnostic_reports_checked=(
            musicnn_legacy_baseline_import_order_diagnostic_report_count
        ),
        label_mapping_checked=label_mapping_count,
        evidence_packages_checked=evidence_package_count,
        fixture_manifest_templates_checked=fixture_manifest_template_count,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Roadmap 4.3 lightweight evaluation example artifacts.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="genre-classifier service root. Defaults to the current working directory.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = validate_all(args.root)
    except ValidationError as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1

    print(
        "validation ok: "
        f"files={summary.files_checked}, "
        f"json_outputs={summary.json_outputs_checked}, "
        f"fixture_results={summary.fixture_results_checked}, "
        f"model_provenance={summary.model_provenance_checked}, "
        f"local_artifact_metadata={summary.local_artifact_metadata_checked}, "
        f"local_artifact_evidence_reports={summary.local_artifact_evidence_reports_checked}, "
        f"real_local_artifact_evidence_reports={summary.real_local_artifact_evidence_reports_checked}, "
        f"parity_scaffold_dry_run_outputs={summary.parity_scaffold_dry_run_outputs_checked}, "
        f"musicnn_onnx_parity_spike_reports={summary.musicnn_onnx_parity_spike_reports_checked}, "
        "musicnn_onnx_parity_environment_preparation_reports="
        f"{summary.musicnn_onnx_parity_environment_preparation_reports_checked}, "
        "musicnn_onnx_fixtures_and_baseline_runtime_decision_reports="
        f"{summary.musicnn_onnx_fixtures_and_baseline_runtime_decision_reports_checked}, "
        "musicnn_onnx_fixture_set_and_baseline_runtime_strategy_reports="
        f"{summary.musicnn_onnx_fixture_set_and_baseline_runtime_strategy_reports_checked}, "
        "musicnn_onnx_fixtures_and_scoped_baseline_capture_approval_reports="
        f"{summary.musicnn_onnx_fixtures_and_scoped_baseline_capture_approval_reports_checked}, "
        "musicnn_onnx_fixture_placement_and_scoped_baseline_readiness_reports="
        f"{summary.musicnn_onnx_fixture_placement_and_scoped_baseline_readiness_reports_checked}, "
        "musicnn_legacy_baseline_capture_reports="
        f"{summary.musicnn_legacy_baseline_capture_reports_checked}, "
        "musicnn_onnx_preprocessing_alignment_reports="
        f"{summary.musicnn_onnx_preprocessing_alignment_reports_checked}, "
        "musicnn_onnx_pragmatic_preprocessing_prototype_reports="
        f"{summary.musicnn_onnx_pragmatic_preprocessing_prototype_reports_checked}, "
        "musicnn_tensorflow_input_musiccnn_availability_probe_reports="
        f"{summary.musicnn_tensorflow_input_musiccnn_availability_probe_reports_checked}, "
        "musicnn_onnx_output_capture_reports="
        f"{summary.musicnn_onnx_output_capture_reports_checked}, "
        "musicnn_onnx_fixture_visibility_strategy_reports="
        f"{summary.musicnn_onnx_fixture_visibility_strategy_reports_checked}, "
        "musicnn_legacy_baseline_import_order_diagnostic_reports="
        f"{summary.musicnn_legacy_baseline_import_order_diagnostic_reports_checked}, "
        f"label_mapping={summary.label_mapping_checked}, "
        f"evidence_packages={summary.evidence_packages_checked}, "
        f"fixture_manifest_templates={summary.fixture_manifest_templates_checked}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
