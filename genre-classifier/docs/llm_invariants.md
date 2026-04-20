# LLM Path Invariants

## Scope

- This is a preparatory baseline for LLM migration only.
- Changes in Roadmap 2.8 apply only to the `llm` provider path.
- No cutover has been performed.
- The default provider remains unchanged.
- The external `/classify` contract is unchanged.
- The response shape is unchanged.
- The transport/runtime request contract is unchanged.

## Prompt Discipline

- A dedicated prompt builder seam exists for LLM prompt discipline.
- The prompt targets machine-readable JSON output.
- Explanations, prose, and markdown are explicitly disallowed.
- Returning fewer tags is preferred over inventing genres.
- Returning an empty list for weak output is acceptable behavior.

## Controlled Vocabulary

- A canonical allowed vocabulary baseline exists for the LLM path.
- Known aliases normalize to canonical tag forms.
- Unknown or out-of-vocabulary values are dropped.
- Normalization is deterministic only.
- Fuzzy matching and semantic guessing are not part of this stage.

## Post-Processing Order

The controlled LLM post-processing order is:

1. canonicalization
2. OOV filtering
3. dedupe
4. ranking
5. top-N
6. threshold filtering
7. final provider result for downstream validation

## Weak And Partial Output

- Weak scored values may be dropped.
- All weak scored values may collapse to an empty result.
- A partial result with one strong surviving tag is acceptable.
- Unscored items may survive provider-level post-processing.
- Invalid non-`None` score values do not pass through post-processing.

## Downstream Boundary

- Controlled post-processing does not replace downstream validation.
- Controlled post-processing does not replace compatibility mapping.
- Existing compatibility semantics are preserved.
- This stage does not redesign taxonomy.
- This stage does not change rollout behavior.

## Rollback Notes

- The prompt seam is isolated.
- The vocabulary layer is isolated.
- The post-processing layer is isolated.
- Golden tests are isolated.
- Each layer can be rolled back locally without requiring a cutover rollback.
