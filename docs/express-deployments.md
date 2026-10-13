# Express deployments (Model Serving)

[Express deployments](https://docs.databricks.com/aws/en/machine-learning/model-serving/express-deployments)
pack the registering Python environment into the model version
(`mlflow.register_model(..., env_pack="databricks_model_serving")`). The serving
endpoint then skips the container image build.

dao-ai requests this by default (`app.express_deployment: true`). It applies only
when registration runs on **x86 Databricks serverless** compute. Everywhere else,
registration quietly uses the standard container build, and the deploy log says
which path was taken:

| Where `create_agent` runs | Result | Log line |
|---|---|---|
| Local machine / CI (`agent up --direct`) | standard build | `Express deployment skipped: registration is not running on Databricks serverless` |
| Serverless job on ARM (`agent up`, `workflow up` → `07_deploy_agent`) | standard build | `Express deployment skipped: serverless compute is ARM ...` |
| Serverless on x86 | express | `Express deployment enabled` |
| `app.express_deployment: false` | standard build | `Express deployment disabled` |

## Why ARM matters

Serving runs on x86, and the packed environment includes the interpreter and
compiled wheels, so an ARM-packed env cannot be served as-is.

Serverless compute can run on ARM (aarch64). In testing on AWS, serverless **job** tasks
reported `DATABRICKS_CPU_ARCH=aarch64` and interactive serverless **notebooks** reported
`x86_64`. Check yours with `os.environ.get("DATABRICKS_CPU_ARCH")`.

MLflow >= 3.15.1 ignores `env_pack` on ARM with a warning
([mlflow/mlflow#24762](https://github.com/mlflow/mlflow/pull/24762)). dao-ai checks
`DATABRICKS_CPU_ARCH` itself, so older MLflow versions behave the same way. The
deploy-job environment pins one of these older versions.

So a job-based deploy (`agent up`, `workflow up`) gets express only when the job runs on
x86. Otherwise it uses the standard container build.

## Behavior when express applies

- The served environment is the registering serverless environment, for example
  Python 3.12.3 on notebook environment version 6. `app.python_version` is ignored (a
  warning is logged on mismatch).
- MLflow's `install_dependencies` is `False`. dao-ai installs missing requirements
  itself (see below), because the development wheel's `code/<wheel>` requirement is a
  relative path that `pip install -r` would not resolve.
- Custom code (`src/`, `app.code_paths`), skills and `pip_requirements` are logged
  exactly as before.

## Validation status (2026-10-12, AWS workspace)

Fixtures are in `tests/config/express/`. Each endpoint was checked with tool calls that
report where the code was loaded from and which libraries imported.

| Run | Compute | Path taken | Endpoint ready | Custom code (`src/`, `code_paths`) | `pip_requirements` |
|---|---|---|---|---|---|
| `agent up` bundle job, `express_basic` (dev) | job, `client.5.12`, aarch64 | fallback | ✅ | n/a | n/a |
| `agent up` bundle job, `express_code` (dev) | job, `client.5.12`, aarch64 | fallback | ✅ | ✅ `/model/code/...` | n/a (reported MISSING, as expected) |
| `agent up` bundle job, `express_full` (dev) | job, `client.5.12`, aarch64 | fallback | ✅ 10m41s (7.5 min container build) | ✅ | ✅ humanize 4.16.0, rapidfuzz 3.14.6 |
| Interactive serverless notebook, `express_full` (dev) | notebook, `client.6.3`, x86_64 | **express** | ✅ **4m25s**, no container-build events | ✅ `/databricks/model/code/...` | ✅ same versions |
| Interactive notebook, `express_full` v2: **only dao-ai installed**, no `pip_requirements` | notebook, `client.6.3`, x86_64 | **express** (dao-ai installed humanize/rapidfuzz before packing) | ✅ ~10.5 min as an *update* (v1 was re-provisioned from scale-to-zero alongside it); no container-build events | ✅ | ✅ same versions |

Notes:
- Express registration (log, register, pack the ~519 MB env and stage it) took 40s.
- Before **logging** the model, dao-ai checks that the running environment satisfies
  the model's pip requirements and installs any that are missing
  (`_prepare_express_env`). If that install fails, it falls back to the standard
  container build.
  - The check runs before `log_model`, not just before the pack, because `log_model`
    imports the model to validate it. A tool module that imports a pip requirement at
    load time fails there otherwise; this was hit live and fixed.
  - This matters wherever dao-ai is not running from a bundle job, for example
    `07_deploy_agent.py` run by hand. That notebook only installs `dao_ai_dep`.
  - The bundle job already has every requirement installed through its environment
    spec, so nothing is installed there.
- Under express, the served Python is the notebook's (3.12.3), not the conda build's
  (3.12.14).
- Still pending x86 serverless *jobs*: published-mode express, plus the `workflow up`
  and `--direct` paths.

## Deep dive: where deploy time goes (2026-10-12)

The `serving-endpoints/{name}/events` API breaks every deploy into phases. To print one:
`python tests/scripts/express_spike/timeline.py <endpoint> [HH:MM:SS]`.

| Deploy | Path | Entity created → Provisioning | Provisioning → READY | Total |
|---|---|---|---|---|
| `express_interactive_dao` v1, create (notebook) | express | 11s | 3m 22s | ~4m 25s |
| `express_interactive_dao` v2, `agents.deploy` update (notebook) | express | 8m 8s, silent | 2m 28s | ~11m 40s |
| `express_exp_a` v3, fresh create (SDK) | express | 5m 6s, silent | 2m 38s | 9m 21s |
| `express_interactive_dao` v4, single-entity `update_config` (SDK) | express | 5m 21s, silent | 4m 17s | 10m 38s |
| `express_full_dao` v1, create (job) | container build | 8m 17s (7.5 min build) | 1m 38s | 10m 41s |
| `express_full_dao` v2, `agents.deploy` update (job) | container build | 9m 4s (6m 20s build, then a 2m 42s wait) | 1m 54s | 11m 20s |

Findings:
1. **The long gap is a platform-side provisioning wait, not express.**
   - Three independent endpoints entered `Provisioning resources` within 5 seconds of each
     other (19:20:53, 19:20:55, 19:20:57): two express, one container build.
   - The container-build entity had finished its image at 19:18:15 and still waited for
     that same moment.
   - The wait varied from 11s to more than 8 minutes. No events are emitted during it.
2. **Express removes the container build, but the provisioning wait can hide the
   saving.**
   - When the wait is short, express is about 4.5 min against about 10.5 min.
   - When the wait is long, a container build runs inside it, so both paths finish
     around 10–11 min.
3. **The express `Deploying` phase on first deploy is longer** (1.2–3 min against
   0.6–1.6 min) while the ~519 MB packed environment is downloaded and unpacked.
   **Cold start (scale from zero) is the same.** Both endpoints were woken at the same
   moment:
   - express went from `Scaling from zero` to READY in 79s, first 200 at 89s;
   - the container build also took 79s, first 200 at 108s.

   An earlier single sample of 2m 42s for express was noise.
4. **`agents.deploy` updates re-create every previous version** at 0% traffic, up to 15
   per endpoint. That applies to both paths, and an old version that has scaled to zero
   is re-provisioned with the new one. This is expected behavior, not express-specific.
5. **Mixing paths works.** Express versions (from a notebook) and container-built
   versions (from a job) coexist on one endpoint's history. dao-ai picks the path per
   registration, based on where `create_agent` runs.

Functional parity (same `express_full` config, one probe query each):

| Path | Code served from | Python | humanize / rapidfuzz | `src/` tool | `code_paths` factory |
|---|---|---|---|---|---|
| express (notebook) | `/databricks/model/code/...` | 3.12.3 (notebook env) | 4.16.0 / 3.14.6 | ✅ | ✅ |
| container build (job) | `/model/code/...` | 3.12.14 (conda, `python_version`) | 4.16.0 / 3.14.6 | ✅ | ✅ |

## Inference validation from MLflow traces (2026-10-13)

The source of truth is the TOOL span in each request's MLflow trace, not the LLM's
reply. `tests/scripts/express_spike/validate_traces.py` does the following:
1. Sends one request per endpoint, retrying through scale-from-zero.
2. Waits for the trace.
3. Checks the `fuzzy_product_lookup` span. That tool
   (`tests/config/express/src/express_tools/catalog.py`) calls
   `rapidfuzz.process.extractOne(..., scorer=fuzz.ratio)` on the LLM-supplied query and
   formats the result with `humanize.intcomma` and `humanize.intword`.
4. Compares the span's output to values computed independently: the `fuzz.ratio` score
   from a stdlib LCS, and the formatting by hand.

| Endpoint / version | Path | TOOL spans | `fuzzy_product_lookup` output (trace) | Result |
|---|---|---|---|---|
| `express_full_dao` v3 | container build (job), no packed env | environment_probe, fuzzy_product_lookup, greet | `best=Cordless Hammer Drill score=76.92 price=$129.99 units_sold=1,250,000 (1.2 million) [rapidfuzz=3.14.6 humanize=4.16.0]` | PASS |
| `express_interactive_dao` v5 | express (notebook), packed env, no container events | environment_probe, fuzzy_product_lookup, greet | identical | PASS |

The same traces show the colocated `src/` tool and the `app.code_paths` factory running:
- under `/model/code/...` on Python 3.12.14 for the container build;
- under `/databricks/model/code/...` on Python 3.12.3 for express.

Run it: `python tests/scripts/express_spike/validate_traces.py <endpoint>=<experiment_id> ...`.
