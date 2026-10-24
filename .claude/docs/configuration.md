# Configuration reference

Configure solid-coder with TOML settings in the target repository. These settings
are separate from mise's `.config/mise/config.toml`, which manages development
tools and tasks.

## File locations and overrides

Plugin version **1.7.21** merges configuration in this order:

1. Built-in defaults.
2. User config: `~/.config/solid-coder/config.toml`, falling back to `~/.solid-coder/config.toml`.
3. Each directory's repository config: `.solid-coder/config.toml`, falling back to `.config/solid.coder/config.toml`.
4. That directory's `.solid-coder/config.local.toml` — personal project overrides; keep this file out of Git.

Within a Git repository, configuration is merged from the repository root down
to the effective working directory. At each directory, project settings load
before local overrides. Deeper configuration overrides ancestor settings.
Tables merge recursively; scalar values and arrays replace earlier values.
An explicit `false`, `0`, or empty array is an override, not a missing setting.
Omitted settings use the built-in defaults listed below. This repository's own
config can override those defaults.

Only the first existing alias in each pair contributes settings. Repository
settings override user defaults; they do not merge both aliases together.
Selected unreadable, malformed, or schema-invalid files report their path and
reason without falling back to another alias. User defaults are read once per
layered lookup, below all repository settings.

External `repo:setup` automation can synchronize the canonical project file,
`.solid-coder/config.toml`. Mise can manage the primary user file. Required CI
settings should remain committed in the
repository. This repository does not implement that external synchronization.

## Minimal project example

Put this in `.solid-coder/config.toml`, or use
`~/.config/solid-coder/config.toml` to share the defaults across repositories:

```toml
code_review_on_write_enabled = true

[llm]
backend = "codex"
timeout = 1000

[feature_flags]
health_check_mode = "legacy"
```

This enables write review through the legacy healthcheck, uses Codex's default
model, and gives the review subprocess a 1,000-second timeout.
Use `health_check_mode = "workflow"` to select the flow-engine
review path instead. The two modes keep their native review rules.

TOML keys belong to the most recent `[table]`. Keep
`code_review_on_write_enabled` at the top of the file, before any table header;
putting it under `[llm]` or `[hooks.pre_write_gate]` does not configure the root flag.

For a personal override, put only the differences in
`.solid-coder/config.local.toml`:

```toml
[llm]
timeout = 900
debug = true
```

## Root settings

| Key | Type | Default | Meaning |
| --- | --- | --- | --- |
| `code_review_on_write_enabled` | Boolean | `false` | Enables source review by the pre-write gate. This does not toggle every independent hook protection. |

## `[llm]` — review backend

| Key | Type | Default | Meaning |
| --- | --- | --- | --- |
| `backend` | String | `"claude"` | Choose `"claude"`, `"codex"`, or `"local"` for the review runner. |
| `model` | String | `"local"` | Model identifier for the selected backend. For Claude/Codex, `""`, `"claude"`, `"codex"`, and `"local"` use the CLI's default model. For the local backend, the value is sent to the local server. |
| `timeout` | Integer, seconds | `300` | Timeout used for review subprocesses and associated gateway calls. The host hook's separately configured timeout can still limit a run. |
| `host` | String, URL | `"http://localhost:8080"` | Local inference server address when `backend = "local"`. |
| `debug` | Boolean | `false` | Enables extra legacy-review diagnostic output. |
| `codex_home` | String | `""` | Accepted compatibility setting with no current production consumer. Omit it; it does not redirect the current Codex runner. |
| `bare_session_model` | String | `""` | Accepted compatibility setting with no current production consumer. Use `model` instead. |

The selected backend still requires its normal installation and authentication.
Choose a model identifier compatible with that backend; the Codex runner rejects
model names beginning with `claude-`.

## `[hooks.<name>]` — per-hook exclusions

| Key | Type | Default | Meaning |
| --- | --- | --- | --- |
| `exclude` | Array of glob patterns | `[]` | Paths excluded from the named hook. For the source-write gate, use `[hooks.pre_write_gate]`. |

For example, `"tests/**"` matches files beneath a `tests` directory; `**` spans
directory segments. An override array replaces the inherited array. To extend an
existing exclusion list, include the inherited patterns in the replacement list.
These are hook exclusions, not general workflow permissions.

## `[flow_engine]` — execution permissions and concurrency

| Key | Type | Default | Meaning |
| --- | --- | --- | --- |
| `permitted_executables` | Array of strings | `[]` | Executors allowed for workflow command/script steps, such as `["python3", "bash", "sh"]`. An empty list rejects command/script executors when loading workflows. |
| `max_parallel_sessions` | Integer, at least `1` | `4` | Maximum concurrent session delegates started by a delegate fan-out. |

See the [workflow YAML reference](workflow-yaml-reference.md#flow-engine-configuration)
for the workflow execution contract.

## `[feature_flags]` — review and workflow modes

| Key | Type | Default | Meaning |
| --- | --- | --- | --- |
| `health_check_mode` | `"workflow"` or `"legacy"` | `"workflow"` | Selects the source-health review implementation. This repository explicitly selects `"legacy"`. |
| `flow_plain_text_response` | Boolean | `true` | Presents flow responses as compact text. Set `false` for structured JSON responses. |
| `flow_submission_format` | `"nested"` or `"flat_array"` | `"nested"` | Selects the model-facing output-submission envelope recorded for a workflow run. |

See [experimental flat submissions](workflow-yaml-reference.md#experimental-flat-submissions)
for examples. Presentation format and submission format are separate settings.

## `[frontmatter]` — project metadata vocabulary

| Key | Type | Default | Meaning |
| --- | --- | --- | --- |
| `additional_categories` | Array of strings | `[]` | Adds project-specific `solid-category` names to the bundled vocabulary. |

Names must contain lowercase ASCII letters, with optional single hyphens between
words, such as `"domain-policy"`. Empty names and placeholders such as `"misc"`,
`"other"`, `"stuff"`, and `"todo"` are rejected. Adding categories does not disable
frontmatter review.

## `[inference]` — local model requests

These settings apply to the local inference path, not Claude/Codex CLI generation.

| Key | Type | Default | Meaning |
| --- | --- | --- | --- |
| `temperature` | Number | `0` | Sampling temperature; lower values reduce randomness. |
| `top_k` | Integer | `20` | Limits sampling to the highest-ranked candidate tokens. |
| `top_p` | Number | `0.95` | Probability-mass cutoff for nucleus sampling. |
| `min_p` | Number | `0.05` | Filters tokens by probability relative to the most likely token. |
| `repeat_penalty` | Number | `1.1` | Penalty applied to repetition. |
| `max_tokens` | Integer | `4096` | Maximum generated tokens requested from the local server; `-1` requests no configured limit. |

## `[server]` — legacy local llama-server launcher

These settings configure `scripts/run-local-llm.sh`; they do not configure hosted
Claude or Codex models. The shell launcher supplies its own fallbacks for missing
keys, which differ from the Python model defaults in several places. Set those
keys explicitly when using the launcher.

| Key | Type | Python default | Launcher fallback | Meaning |
| --- | --- | --- | --- | --- |
| `model` | String | `""` | `"Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf"` | GGUF filename searched for beneath `~/.cache/huggingface`. |
| `port` | Integer | `8080` | `8080` | HTTP server port; align it with `[llm].host`. |
| `ctx_size` | Integer, tokens | `65536` | `32768` | Server context size. |
| `gpu_layers` | Integer | `99` | `99` | Layers requested for GPU offloading. |
| `parallel` | Integer | `1` | `1` | Parallel server request slots. |
| `batch_size` | Integer | `2048` | `2048` | Logical prompt-processing batch size. |
| `ubatch_size` | Integer | `512` | `512` | Physical prompt-processing micro-batch size. |
| `mlock` | Boolean | `true` | `false` | Requests locked model memory with `--mlock`. |
| `seed` | Integer | `42` | `-1` | RNG seed passed to the local server. |
| `reasoning` | String | `"auto"` | `"off"` | Reasoning mode forwarded to the launcher: `"on"`, `"off"`, or `"auto"`. |

## Applying changes and diagnosing configuration

- Review settings are read for subsequent operations; the local llama-server must
  be restarted to apply `[server]` changes. Existing workflow runs retain their
  recorded submission format.
- Repository/local settings can override a value you expect to inherit. Check
  both files and any nested configs before changing a default.
- Unknown fields inside typed settings sections, invalid field values, and
  malformed selected TOML files report configuration errors. Check the reported
  file, syntax, and table placement before retrying.
- `SOLID_CODER_TEST_MODEL_PROFILE` is a test-harness override for the `[llm]`
  section, not the normal user-defaults mechanism.

The settings schema lives in `mcp-server/health/config/`; the committed
`.solid-coder/config.toml` is a project example, not a list of built-in defaults.
