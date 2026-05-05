# Roadmap 4.32 - MusiCNN JSON metadata diff review parity-readiness gate

Status: prepared for review / documentation-only JSON metadata diff gate / non-production-facing.

## Scope

Roadmap 4.32 reviews the measured JSON metadata difference recorded after
Roadmap 4.30 and validated by Roadmap 4.31.

This is a documentation and review safe-slice only.

It compares the official/local MusiCNN JSON metadata artifact prepared outside
the repository with the current bundled production baseline JSON.

It does not run inference, call `/classify`, execute ONNX Runtime, execute
TensorFlow inference, add dependencies, add model files, change providers,
change runtime behavior, or start production migration.

## Current production baseline

The current production baseline remains the existing `legacy_musicnn` path.

The current bundled production baseline JSON reviewed here is:

```text
app/models/msd-musicnn-1.json
```

The default provider, provider factory, runtime path, controlled vocabulary,
cache semantics, `/classify` contract, and response shape are unchanged.

## Why this review is needed

Roadmap 4.30 prepared real local-only MusiCNN ONNX/PB/JSON artifacts outside
the repository under `/tmp/music-tools-onnx-parity/`.

Roadmap 4.31 added validation coverage for the real local-only artifact
evidence report.

The Roadmap 4.30 evidence recorded that:

- the official/local PB and current bundled production PB match by SHA256;
- the official/local JSON and current bundled production JSON differ by
  measured size and SHA256.

That JSON difference must be reviewed before any local-only parity scaffold can
be planned, because metadata fields can define label order, output shape,
model identity, input shape, and preprocessing expectations.

## Input artifacts reviewed

| Artifact | Role | Present | Size bytes | SHA256 |
| --- | --- | --- | ---: | --- |
| `/tmp/music-tools-onnx-parity/msd-musicnn-1.json` | official/local JSON metadata artifact outside repo | yes | 3299 | `8e6b3b509f0610c0e65dce467fd459d6777509388eaddb13ed138d8ac1341ffe` |
| `app/models/msd-musicnn-1.json` | current bundled production baseline JSON | yes | 3298 | `24842b068b5c09dce033a0bcb41d450e4e469352b799e831ac7728c93bbfb6be` |

Both files were present at review time.

No artifact was downloaded again.

No artifact was moved into the repository.

## Inspection method

The review used read-only local checks from `/opt/music-tools/genre-classifier`:

```text
python3 -m json.tool /tmp/music-tools-onnx-parity/msd-musicnn-1.json
python3 -m json.tool app/models/msd-musicnn-1.json
wc -c /tmp/music-tools-onnx-parity/msd-musicnn-1.json app/models/msd-musicnn-1.json
sha256sum /tmp/music-tools-onnx-parity/msd-musicnn-1.json app/models/msd-musicnn-1.json
diff -u app/models/msd-musicnn-1.json /tmp/music-tools-onnx-parity/msd-musicnn-1.json || true
```

An inline `python3 - <<'PY' ... PY` structured comparison was also run without
saving any comparison script in the repository.

The inline comparison parsed both JSON files, compared raw bytes, compared
parsed JSON objects, compared top-level keys, detected label arrays, compared
label set equality, compared label order equality, collected model/input/output
and preprocessing-related metadata paths, and classified the result.

## Raw diff summary

The raw byte comparison is not identical.

The official/local JSON is 3299 bytes.

The bundled production baseline JSON is 3298 bytes.

The unified diff showed only the final newline difference:

```diff
@@ -123,4 +123,4 @@
         "sample_rate": 16000,
         "algorithm": "TensorflowPredictMusiCNN"
     }
-}
\ No newline at end of file
+}
```

The bundled baseline JSON has no final newline. The official/local JSON has a
final newline.

## Structured JSON comparison

Structured comparison result:

```text
official_path=/tmp/music-tools-onnx-parity/msd-musicnn-1.json
bundled_path=app/models/msd-musicnn-1.json
official_size_bytes=3299
bundled_size_bytes=3298
official_sha256=8e6b3b509f0610c0e65dce467fd459d6777509388eaddb13ed138d8ac1341ffe
bundled_sha256=24842b068b5c09dce033a0bcb41d450e4e469352b799e831ac7728c93bbfb6be
raw_equal=False
parsed_json_equal=True
top_level_only_official=[]
top_level_only_bundled=[]
official_label_arrays_found=[('$.classes', 50)]
bundled_label_arrays_found=[('$.classes', 50)]
labels_set_equal_any=True
label_order_equal_any=True
classification=harmless_formatting_only
```

The parsed JSON objects are equal.

No top-level key exists only in the official/local JSON.

No top-level key exists only in the bundled production baseline JSON.

## Labels equality result

Both files contain one detected label array:

```text
$.classes
```

Both arrays contain 50 labels.

The label set is equal.

Result:

```text
labels_set_equal_any=True
```

## Label order equality result

The detected `$.classes` arrays are equal in order.

Result:

```text
label_order_equal_any=True
```

The JSON metadata diff does not indicate any label vocabulary or label-order
change.

## Metadata fields comparison

The same model/input/output/preprocessing-related field paths were detected in
both parsed JSON objects:

```text
$.classes
$.dataset.name
$.inference.sample_rate
$.name
$.schema
$.schema.inputs
$.schema.inputs[0].name
$.schema.outputs
$.schema.outputs[0].name
$.schema.outputs[1].name
$.schema.outputs[2].name
$.version
```

Because `parsed_json_equal=True`, the values at these paths are equivalent.

Relevant unchanged metadata includes:

- model name: `MSD MusiCNN`;
- version: `1`;
- input tensor name: `model/Placeholder`;
- input shape: `[187, 96]`;
- prediction output tensor name: `model/Sigmoid`;
- prediction output shape: `[1, 50]`;
- embedding output tensor name: `model/dense/BiasAdd`;
- embedding output shape: `[1, 200]`;
- sample rate: `16000`;
- inference algorithm metadata: `TensorflowPredictMusiCNN`.

## Formatting versus semantic meaning

The difference is formatting/newline-only.

Evidence:

- raw bytes differ;
- SHA256 values differ;
- file sizes differ by one byte;
- parsed JSON objects are equal;
- top-level keys are equal;
- label set is equal;
- label order is equal;
- detected metadata paths are equal;
- raw diff shows only the final newline.

Classification:

```text
harmless_formatting_only
```

## Impact assessment for ONNX parity scaffold

The JSON metadata difference does not block the next documentation/planning
step toward a local-only parity scaffold.

It does not prove ONNX/PB numeric parity.

It does not prove preprocessing parity.

It does not prove output parity.

It does not prove `/classify` parity.

It only resolves the Roadmap 4.30 JSON metadata evidence gap as a
formatting-only newline difference.

## No-go checklist

The following remain no-go after this review:

- no inference approved;
- no `/classify` call approved;
- no ONNX Runtime execution approved;
- no TensorFlow inference execution approved;
- no `onnxruntime` dependency approved;
- no provider implementation approved;
- no provider factory change approved;
- no default provider change approved;
- no production runtime change approved;
- no Dockerfile or Docker Compose change approved;
- no controlled vocabulary change approved;
- no cache semantics change approved;
- no response shape change approved;
- no model files in the repository approved;
- no audio fixtures approved;
- no shadow execution approved;
- no canary rollout approved;
- no production migration approved.

## Decision options

- Allow only the next documentation/planning step toward a local-only parity
  scaffold, with all runtime and inference no-go items still active.
- Request deeper metadata review before scaffold planning if a reviewer wants
  an independent manual confirmation of the newline-only diff.
- Block parity scaffold planning if any future review finds label,
  preprocessing, model identity, input, or output metadata differences not
  captured by this artifact.
- Keep Roadmap 4 blocked if either reviewed JSON artifact becomes unavailable
  and the comparison cannot be reproduced.

## Recommended decision

Allow the next documentation/planning step toward a local-only parity scaffold.

Reason: the official/local JSON and current bundled production baseline JSON
are parsed-JSON equivalent. The only observed raw difference is the final
newline. Labels, label order, top-level keys, and detected model/input/output
and preprocessing-related metadata paths are equivalent.

This recommendation does not approve inference.

This recommendation does not approve `onnxruntime`.

This recommendation does not approve provider implementation.

This recommendation does not approve production migration.

## Explicit non-goals

Roadmap 4.32 does not:

- run inference;
- call `/classify`;
- run ONNX Runtime;
- run TensorFlow inference;
- add dependencies;
- add model files;
- add audio fixtures;
- add download or network logic;
- change controlled vocabulary;
- change production code path;
- connect providers;
- change provider factory;
- change default provider;
- change runtime;
- change Dockerfile or Docker Compose;
- change `/classify` contract;
- change response shape;
- change cache semantics;
- touch `tidal-parser`;
- perform shadow execution;
- perform canary rollout;
- perform LLM cutover;
- start production migration.

## Allowed next steps

Allowed next steps are documentation/planning-only unless separately approved:

- reference this review from a future local-only parity scaffold plan;
- preserve `/tmp/music-tools-onnx-parity/` as local-only external artifact
  storage if future work needs the prepared artifacts;
- plan future parity checks without adding runtime dependencies or executing
  inference in this step;
- continue review of preprocessing, tensor outputs, and rollback planning as
  documentation-only gates.

## Prohibited next steps

The following are prohibited by this gate:

- adding `onnxruntime` or other runtime dependencies;
- adding ONNX/PB/JSON model files to the repository;
- adding audio fixtures;
- adding network/download logic;
- implementing or connecting an ONNX provider;
- changing provider factory/default provider/runtime behavior;
- changing controlled vocabulary;
- calling `/classify`;
- running ONNX Runtime or TensorFlow inference;
- changing Dockerfile or Docker Compose;
- changing response shape or cache semantics;
- starting shadow execution, canary rollout, LLM cutover, or production
  migration;
- committing, tagging, pushing, or creating a release as part of this review.

## Rollback considerations

This review adds only a documentation artifact.

No production files, dependencies, runtime settings, provider code, model files,
audio fixtures, Docker files, or API contracts were changed.

Rollback is therefore documentation-only: remove or revise this Roadmap 4.32
artifact if review finds that the recorded local comparison was invalid or
non-reproducible.
