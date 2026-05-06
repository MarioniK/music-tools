# Roadmap 4.66 - ONNX/MusiCNN activation-to-genre semantic mapping smoke

## Контекст

Roadmap 4.66 следует сразу за Roadmap 4.65, потому что 4.65 уже подтвердил локально и без production-runtime:

- patch shape `187 x 96`;
- ONNX output `activations [50]`;
- ONNX output `embeddings [200]`;
- repeated-run stability с `stable=true`, `max_abs_diff=0.0`, `mean_abs_diff=0.0`.

На этом шаге мы не проверяем `/classify`, не трогаем provider wiring и не делаем migration-claim. Задача только в том, чтобы показать, как уже подтверждённые activations можно сопоставить с текущим controlled vocabulary.

## Что было проверено

- Локальный ONNX artifact и fixture из `/tmp/music-tools-onnx-parity`.
- Metadata/classes из `msd-musicnn-1.json`.
- Совпадение количества `classes` с размерностью activations: `50 == 50`.
- Индексный порядок классов пригоден для прямого сопоставления с выходом activations.
- Top-10 activation labels и scores.
- Маппинг top-10 к текущему controlled vocabulary без изменения production-кода.

## Как выполнялся mapping

Сопоставление делалось по текущему JSON metadata:

- `classes[i]` использовался как label для `activations[i]`;
- label нормализовался через текущую vocabulary/normalization логику;
- если label попадал в controlled vocabulary, он считался mapped;
- если label не попадал, он считался leakage-кандидатом только как локальный smoke evidence, без попытки подогнать результат.

Для этого шага отдельный helper:

- [`scripts/lightweight/musicnn_onnx_semantic_mapping_smoke.py`](../../scripts/lightweight/musicnn_onnx_semantic_mapping_smoke.py)

Helper не импортируется production-application и не меняет runtime wiring.

## Top-N результат

Top-10 activation labels:

1. `electronic` - `0.2679`
2. `rock` - `0.1716`
3. `indie` - `0.1285`
4. `pop` - `0.1112`
5. `dance` - `0.0952`
6. `alternative` - `0.0878`
7. `Progressive rock` - `0.0741`
8. `electronica` - `0.0666`
9. `ambient` - `0.0616`
10. `House` - `0.0567`

Все 10 top-N labels были сопоставлены с текущим controlled vocabulary.

## Leakage check

В этом smoke-run не найдено non-genre descriptor leakage в top-10:

- `mapped_count`: `10`
- `unmapped_count`: `0`
- `non_genre_descriptor_count`: `0`
- `leakage_controlled`: `true`

Это не означает, что любые будущие top-N позиции тоже будут чистыми. Это только локальное evidence для данного fixture и данного local-only output.

## Candidate output shape

Диагностический candidate сохраняет текущую shape-идею production-ответа:

- `genres`: список объектов `{tag, prob}`;
- `genres_pretty`: список строк.

Для smoke evidence был сформирован такой candidate shape:

- `genres`:
  - `electronic`
  - `rock`
  - `indie`
  - `pop`
  - `dance`
  - `alternative`
  - `progressive rock`
  - `electronica`
- `genres_pretty`:
  - `indie rock`
  - `alternative rock`
  - `electronic`
  - `rock`
  - `indie`
  - `pop`
  - `dance`
  - `alternative`

Важно: `genres_pretty` здесь следует текущей normalization policy, включая существующий cap на 8 элементов. Это диагностический вывод, а не обещание нового production behavior.

## Что это не означает

Этот шаг не является:

- `/classify` integration;
- provider implementation;
- default provider switch;
- production migration;
- strict legacy parity proof;
- TensorFlow baseline run;
- TensorFlow vs ONNX comparison;
- production readiness claim.

Default provider по-прежнему остаётся `legacy_musicnn`.

## Response shape и contract

Для 4.66 не требуется менять response shape или `/classify` contract:

- `response_shape_change_required`: `false`
- `classify_contract_change_required`: `false`

Это smoke evidence о semantic mapping, а не изменение публичного API.

## Sanity summary

Санитизированный report:

- [`docs/lightweight/evaluation/parity-scaffold/onnx-musicnn-semantic-mapping-smoke-report.json`](./evaluation/parity-scaffold/onnx-musicnn-semantic-mapping-smoke-report.json)

Ключевой вывод:

- activations `[50]` и classes `[50]` согласованы;
- index order usable;
- top-10 labels mapped to current controlled vocabulary;
- non-genre descriptor leakage в этом smoke-run не обнаружен;
- production contract менять не нужно.

## Next recommended step

Roadmap 4.67 логично использовать как следующий gate для одной из двух вещей:

1. зафиксировать policy для того, как semantic-mapping diagnostic должен трактовать lower-ranked labels и aliases;
2. или подготовить отдельный guarded candidate-scaffold, если появится потребность в более строгом canonical output review перед любым provider work.

Пока это остаётся diagnostic-only evidence.
