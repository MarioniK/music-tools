# Roadmap 2.9 Sample Manifests

These files are offline evaluation metadata for Roadmap 2.9 only.

They exist to define a stable manifest layout for:

- the curated sample set
- the golden subset
- the repeat-run subset

They are not runtime data sources.
They do not affect provider selection.
They do not change the default provider.
They do not change the `/classify` contract or response shape.

The intended follow-up use is offline-only:

- comparison helpers
- evaluation runners
- aggregate reporting

`samples.master.json` is the source-of-truth scaffold for sample metadata.
`curated_samples.json`, `golden_subset.json`, and `repeat_run_subset.json` are the source of truth for subset membership.
Subset manifests list `sample_id` membership only, so future tooling can consume a small and explicit subset view without duplicating per-sample metadata.

`input_ref` is a placeholder reference only at this stage.
It may point to an eventual offline evaluation input location, and a real file is not required for this scaffold slice.
