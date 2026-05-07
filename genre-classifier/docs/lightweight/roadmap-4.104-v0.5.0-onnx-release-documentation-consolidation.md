# Roadmap 4.104. v0.5.0 ONNX release documentation consolidation

## Summary

Roadmap 4.104 consolidates the ONNX migration evidence into permanent release/operator documentation before the v0.5.0 release.

This step is documentation-only. It does not change runtime defaults, does not touch `tidal-parser`, and does not perform any release tag or cleanup deletion.

## What this step adds

- release summary for v0.5.0;
- operator-facing ONNX runtime document;
- compact changelog entry for the ONNX default runtime milestone;
- minimal README refresh so the repo root no longer describes the legacy default as current;
- structured report and test coverage for the documentation consolidation step.

## Current release state

- ONNX MusiCNN is the current default runtime for `genre-classifier`;
- default Docker target is `onnx-runtime-slim`;
- legacy MusicNN remains preserved as rollback/fallback context;
- `/classify` response shape is unchanged;
- `tidal-parser` code remains untouched in this step;
- full integration smoke already passed in Roadmap 4.103.

## Permanent docs created by this slice

- `genre-classifier/docs/onnx-runtime.md`
- `genre-classifier/docs/releases/v0.5.0.md`
- `CHANGELOG.md`

## Cleanup plan

This step intentionally does not delete the existing lightweight roadmap/evidence trail.

Later Roadmap 4.105 can safely handle archival or removal of older lightweight roadmap/evidence files once the permanent release docs are in place and the v0.5.0 tag exists.

Candidates for later cleanup include:

- old lightweight roadmap docs for the ONNX migration chain;
- older evidence JSON files that duplicate information now captured in release/operator docs;
- report-structure tests for obsolete lightweight JSON reports, after the permanent docs are fully established.

## Non-goals

- no runtime code changes;
- no Dockerfile changes;
- no compose changes;
- no requirements changes;
- no default provider change;
- no artifact commits;
- no tag/release creation;
- no mass deletion of lightweight docs in this step.

## Decision

The release documentation is now the durable source of truth for the ONNX default runtime state. Future cleanup should be a separate, smaller slice.
