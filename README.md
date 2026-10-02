# Yggdrasil model data

Public, versioned aggregate snapshots of [Yggdrasil](https://github.com/yeixio/yggdrasil-core)'s community model ratings. They answer:

> **How well does this model work for people with hardware like mine?**

This repository holds **aggregates only**: averages and counts per model configuration and hardware cohort. It has no per-person records. Live ratings go to the ratings service ([yeixio/yggdrasil-ratings](https://github.com/yeixio/yggdrasil-ratings)), and a daily job publishes what it may share here. Yggdrasil uses these files as a cache when the service can't be reached, and anyone may use them: they are dedicated to the public domain ([CC0](LICENSE)).

## Layout

| Path | |
| --- | --- |
| `schema/ratings-v1.schema.json` | The format, version 1 |
| `ratings/summary.json` | The latest snapshot: every configuration |
| `models/<model>/<quantization>-<runtime>-<backend>-<format>.json` | One configuration, such as `models/qwen2.5-coder-7b-instruct/q4_k_m-llamacpp-metal-gguf.json` |
| `hardware/cohorts.json` | How hardware is grouped |
| `snapshots/<date>.json` | Each day's snapshot, as published |

## What a configuration says

```json
{
  "model": "qwen2.5-coder-7b-instruct",
  "format": "gguf", "quantization": "Q4_K_M", "runtime": "llamacpp", "backend": "metal",
  "cohorts": [
    {"tier": "family", "cohort": "apple:m4-max", "ratings": 18, "average": 4.67, "weighted_score": 4.51, "confidence": "community",
     "tags": {"fast": 12, "great_for_coding": 9}, "median_tokens_per_second": 18.2, "successful_start_rate": 0.96},
    {"tier": "global", "ratings": 126, "average": 4.4, "weighted_score": 4.38, "confidence": "community"}
  ]
}
```

| Field | Meaning |
| --- | --- |
| `tier` / `cohort` | Hardware similarity. `family` is an accelerator model, such as `apple:m4-max`. `class` is an accelerator class and memory band, such as `nvidia:rtx-40:16-32`. `backend` is a runtime backend and memory band, such as `metal:32-64`. `global` is everyone. |
| `average` | The plain mean of the stars |
| `weighted_score` | `(weight × prior + sum of stars) / (weight + ratings)`, so few ratings lean toward the prior; rank by this |
| `confidence` | `limited` (1–2 ratings), `early` (3–9), `community` (10+) |
| `tags` | How many ratings gave each reason |
| `median_*`, `*_rate` | From ratings whose authors chose to share runtime observations (`observed` of them) |

## Privacy

A cohort appears only with at least `min_ratings` (3) ratings, and exact-hardware cohorts, which are a machine's precise model and memory band, are never published. The publish script refuses a snapshot that breaks either rule, or that doesn't match the schema. Ratings carry no names, addresses, prompts, responses, or files. See the [service's privacy notes](https://github.com/yeixio/yggdrasil-ratings#privacy).

## Updating

`.github/workflows/snapshot.yml` runs daily. It fetches `<RATINGS_URL>/v1/aggregates`, validates and lays it out with `scripts/publish.py`, and commits any change with this repository's own token. Set the `RATINGS_URL` repository variable to turn it on; until then it does nothing.
