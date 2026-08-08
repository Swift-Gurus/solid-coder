# SRP fixture-1 workflow baseline — 2026-08-02

This report freezes the pre-crossover baseline for comparing the static SRP YAML flow with `apply-principle-review`. Both cohorts used `tests/principles/SRP/fixtures/fixture-1.swift`, expected metrics `6/2/2`, model `gpt-5.6-terra`, reasoning effort `high`, and a 1000-second timeout.

## Measurement definitions

- **Exact metrics:** `verb_count=6`, `cohesion_groups=2`, and `stakeholder_count=2`.
- **Correct findings:** the deterministic result contains `SRP-1`, `SRP-2`, and `SRP-3`, all SEVERE.
- **Time to artifact:** Codex rollout start through the first successful terminal flow result (YAML) or first successful `submit_batch_findings` result (apply).
- **Session time/tokens:** complete Codex rollout, including final responses and hook retries.
- **Hook overhead:** usage after the first final response when the duplicate Stop hooks incorrectly required another `submit_batch_findings` call.
- Timings and token counts come from Codex rollout JSONL plus `/Users/crowea/.codex/state_5.sqlite`, not UI or approval wait time.

## Aggregate result

| Measurement | YAML steps | Apply principle |
|---|---:|---:|
| Attempts | 10 | 10 |
| Completed | 9 | 10 |
| Exact metrics per attempt | 9/10 | 4/10 |
| Exact metrics when completed | 9/9 | 4/10 |
| Correct findings when completed | 9/9 | 10/10 |
| Median time to valid artifact | 86.4s | 112.8s |
| Median complete-session time | 88.9s | 148.4s |
| Mean tokens to valid artifact | 148,598 | 269,096 |
| Total session tokens | 1,668,984 | 4,009,801 |
| Total input tokens | 1,628,236 | 3,941,687 |
| Cached input tokens | 1,470,464 | 3,629,056 |
| Output tokens | 40,748 | 68,114 |
| Reasoning tokens | 2,950 | 18,464 |

The YAML failure was an orchestration/start failure and produced no metric result. Every completed YAML run returned exact `6/2/2`. Every apply run returned the correct three qualitative violations, but only four returned exact metrics.

## YAML runs

| Run | Session | Result | Session time | Session tokens | Artifact time | Artifact tokens |
|---:|---|---|---:|---:|---:|---:|
| 1 | `019fc459-a644-7ff0-acf4-85ef086d091b` | `6/2/2` | 93.0s | 172,632 | 89.7s | 144,896 |
| 2 | `019fc45b-812c-74e2-80b3-b22178b00861` | `6/2/2` | 88.1s | 172,533 | 85.5s | 144,880 |
| 3 | `019fc45d-17d3-76b2-846d-dc2a76692267` | `6/2/2` | 92.3s | 173,105 | 89.4s | 145,327 |
| 4 | `019fc45e-9880-7953-9525-d5f4046f5ffe` | `6/2/2` | 86.7s | 172,380 | 83.7s | 144,723 |
| 5 | `019fc460-0283-7050-908c-854d122fb3da` | `6/2/2` | 89.7s | 177,242 | 86.4s | 148,723 |
| 6 | `019fc461-75dc-7c63-92cf-d24a86577e22` | orchestration failure | 24.1s | 80,991 | — | — |
| 7 | `019fc461-fdaf-7441-926c-096cbc82e5c0` | `6/2/2` | 89.8s | 173,259 | 87.3s | 145,439 |
| 8 | `019fc463-6ea8-7ad1-9463-cb0867579a30` | `6/2/2` | 97.5s | 201,397 | 94.4s | 173,289 |
| 9 | `019fc465-1fda-7482-8938-87d5ab21782c` | `6/2/2` | 85.6s | 172,529 | 83.3s | 144,916 |
| 10 | `019fc489-1881-77a1-99b1-d7ab8b0f7522` | `6/2/2` | 87.2s | 172,916 | 84.7s | 145,188 |

## Apply-principle runs

| Run | Session | Metrics | Session time | Session tokens | Artifact time | Artifact tokens | Hook tokens |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | `019fc466-9515-74e2-b3c8-89179c6962db` | `6/2/2` | 150.0s | 446,520 | 116.5s | 318,261 | 65,222 |
| 2 | `019fc46a-0223-7870-89c5-a2a81bf60ccf` | `6/3/2` | 168.3s | 370,814 | 127.0s | 245,773 | 84,058 |
| 3 | `019fc46c-c75d-7a40-af67-149af4f7cad8` | `6/2/2` | 153.9s | 472,599 | 120.4s | 344,053 | 65,401 |
| 4 | `019fc46f-5268-7861-bbe2-cb2c200a63f1` | `9/2/2` | 125.0s | 396,411 | 89.3s | 244,129 | 77,253 |
| 5 | `019fc473-fc44-7720-8062-efce06d19a1c` | `6/3/2` | 160.7s | 351,460 | 127.4s | 228,869 | 82,483 |
| 6 | `019fc478-eac0-7f31-9e62-978cceecbc1a` | `6/2/2` | 127.9s | 291,031 | 91.8s | 167,828 | 62,863 |
| 7 | `019fc47b-aada-7921-8518-1afeebc15eab` | `6/2/2` | 149.7s | 471,420 | 118.1s | 343,023 | 65,307 |
| 8 | `019fc47e-78fc-7fb1-8333-b4f971d91010` | `6/3/2` | 142.7s | 395,237 | 109.0s | 268,210 | 64,648 |
| 9 | `019fc4ad-12ea-7b70-85e5-e7ac8789a342` | `7/3/2` | 147.1s | 478,770 | 107.1s | 318,146 | 65,686 |
| 10 | `019fc4b3-1403-7803-ba5e-4faa79f56ee9` | `7/2/2` | 126.9s | 335,539 | 93.4s | 212,666 | 62,515 |

Apply metric distribution: `6/2/2` ×4, `6/3/2` ×3, `9/2/2` ×1, `7/3/2` ×1, and `7/2/2` ×1.

## Known instrumentation defect

Every apply run received two erroneous Stop-hook prompts after a successful batch submission. Across ten runs this added 695,436 tokens and approximately 185.5 seconds. The artifact measurements above stop before these retries, so they remain the fairest comparison of the two review paths.

## Crossover starting point

This baseline predates replacement of the SRP `<detection>` blocks in `references/principles/SRP/rule.md` with the more explicit procedures from `.solid-coder/harness/flows/srp_validation.yaml`. Any post-change cohort must use new session IDs and must not be mixed into these baseline rows.

## Post-change apply cohort: YAML detection instructions in `rule.md`

The three SRP `<detection>` blocks were replaced with the YAML flow's explicit measurement procedures. Definitions, exceptions, severity thresholds, fixture, model, reasoning effort, timeout, apply workflow, and output schema remained unchanged. Nine completed samples were collected; a tenth invocation was intentionally stopped at user request and is excluded from all figures below.

| Run | Session | Metrics | Session time | Session tokens | Artifact time | Artifact tokens | Hook tokens |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | `019fc4c2-efde-77a0-abc1-92273425e42c` | `6/2/2` | 150.9s | 502,910 | 111.9s | 346,029 | 79,619 |
| 2 | `019fc4c6-39e6-7881-b70d-9b4ebc6db8b0` | `6/2/2` | 143.4s | 563,418 | 109.0s | 408,218 | 78,668 |
| 3 | `019fc4c9-0f51-7250-acd6-d13572ce5393` | `6/2/2` | 137.8s | 415,388 | 104.2s | 253,873 | 81,878 |
| 4 | `019fc4cb-5686-7311-a73d-a08a49f3bcea` | `6/2/2` | 133.7s | 530,168 | 100.6s | 373,688 | 79,376 |
| 5 | `019fc4ce-cd12-7ae3-94c6-86186c6aebcd` | `6/2/2` | 143.5s | 445,740 | 109.4s | 318,154 | 64,955 |
| 6 | `019fc4d2-5883-7d52-9ece-3f3d76485dbb` | `6/2/2` | 138.6s | 364,203 | 103.3s | 230,104 | 68,130 |
| 7 | `019fc4d4-af3e-7a92-bd08-c4d4dc6ff177` | `6/2/2` | 103.1s | 206,083 | 73.5s | 117,792 | 59,590 |
| 8 | `019fc4d8-7f90-7822-8241-f8f6be7feaa3` | `6/2/2` | 122.6s | 285,887 | 92.3s | 193,050 | 62,559 |
| 9 | `019fc4e0-4c54-7611-9c85-845cfa403d78` | `6/2/2` | 138.3s | 451,879 | 99.9s | 321,704 | 66,229 |

### Crossover comparison

| Measurement | Original apply | Revised apply | YAML steps |
|---|---:|---:|---:|
| Completed samples | 10 | 9 | 9 |
| Exact metrics | 4/10 (40%) | 9/9 (100%) | 9/9 (100%) |
| Median time to artifact | 112.8s | 103.3s | 86.4s |
| Mean tokens to artifact | 269,096 | 284,735 | 148,598 |
| Median complete-session time | 148.4s | 138.3s | 89.7s among completed runs |
| Mean complete-session tokens | 400,980 | 418,408 | 176,444 among completed runs |

For this single-principle fixture, precise detection instructions—not the step engine—were sufficient to restore exact metric repeatability. The revised apply workflow was about 8% faster to its first artifact than the original apply cohort, but used about 6% more tokens. Compared with the YAML flow, revised apply retained the same completed-run accuracy but was about 20% slower to its first artifact and used about 92% more tokens on average.

This result does not establish behavior when multiple principles compete for attention in one review context. The next useful experiment is a multi-principle cohort with exact per-principle expectations, comparing a combined apply review against isolated MCP steps while preserving identical detection text.
