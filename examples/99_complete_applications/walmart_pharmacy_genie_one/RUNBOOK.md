# Setup guide — Walmart Pharmacy assistant

This guide shows how to install, deploy, and use the Walmart Pharmacy assistant.
It is written to be followed top to bottom. For how it works internally, see [`README.md`](./README.md).

> **Prefer to click through it in Databricks?** [`01_deploy_agent.py`](./01_deploy_agent.py) does the deploy and a live test inference from a notebook — fill in the widgets, choose Apps (MCP) or Model Serving, and run it top to bottom instead of using the terminal below.

## What this is

Walmart's environment does not allow certain provider models. Databricks' built-in Genie One uses
one to *answer* questions, so that native answering path can't run here. This assistant is the
workaround: it answers the same pharmacy questions using an approved OpenAI-style model instead, and
pulls its data from your three Genie spaces (Clinical Outcomes, Core Business Growth, Digital
Accounts).

You can run it two ways — as a **chat app** (a web page you open in the browser) and as an **MCP
server** (a tool other systems can call). This guide covers both. Note that Genie One can still act
as a *consumer* of the MCP server (you add this assistant to a Genie One chat as a tool, Step 4);
what doesn't run is Genie One generating answers with an unsupported model.

---

## Before you start

Ask your Databricks administrator to confirm these are ready:

- Serverless compute, Databricks Apps, and the Unity AI Gateway are turned on.
- An approved OpenAI-style model endpoint exists (the default name is `databricks-gpt-oss-120b`).
- The three Genie spaces exist, and you have their IDs.
- You have a catalog and schema you can write to.

On your machine you need Python 3.12 or newer and the Databricks CLI.

The administrator also needs to grant access. See [Access the administrator must grant](#access-the-administrator-must-grant) at the end.

---

## Step 1 — Install

Run these once in your terminal. Replace `<walmart-workspace-host>` with your workspace URL.

```bash
databricks auth login --host https://<walmart-workspace-host> --profile walmart
pip install dao-ai
dao-ai --version
```

---

## Step 2 — Fill in your values

Set these once so you can paste the later commands unchanged. Replace each `<...>` with a real value.

```bash
P=walmart
CAT=<catalog>
SCH=<schema>
LLM=databricks-gpt-oss-120b
CLIN=<clinical_space_id>
GROW=<growth_space_id>
DIG=<digital_space_id>

PARAMS="--param catalog=$CAT --param schema=$SCH --param llm=$LLM \
  --param clinical_space_id=$CLIN --param growth_space_id=$GROW --param digital_space_id=$DIG"
```

> **Which `LLM` value?** The default `databricks-gpt-oss-120b` works where the AI Gateway serves
> that endpoint by name. Some workspaces instead require the UC model-service address — in that case
> use `LLM=system.ai.gpt-oss-120b` (any approved OpenAI-style model). If a deploy later errors with
> *"…is no longer available. Use Unity Catalog model services (v3)"*, switch to the `system.ai.…`
> form. 

Check that the config reads correctly (this does not deploy anything):

```bash
dao-ai validate -c walmart_pharmacy_genie_one.yaml $PARAMS
```

You should see it report success.

---

## Step 3 — Deploy

**As a chat app** (a web page you open in the browser):

```bash
dao-ai agent up -c walmart_pharmacy_genie_one.yaml -p $P $PARAMS
```

**As an MCP server** (so Genie One and other tools can call it):

```bash
dao-ai agent up --as-mcp --with-connection -c walmart_pharmacy_genie_one.yaml -p $P $PARAMS
```

You can deploy both. They use different names, so they don't conflict.

> **Run each user's data as themselves (optional).** By default every request runs as one shared
> service account. To have the assistant act as the signed-in user instead, add the three lines
> below. The `client-id` and `client-secret` come from your administrator (see the last section).
>
> ```bash
> dao-ai agent up --as-mcp --with-connection -c walmart_pharmacy_genie_one.yaml -p $P $PARAMS \
>   --param on_behalf_of_user=true \
>   --param mcp_oauth_client_id=<client-id> \
>   --param mcp_oauth_client_secret=<client-secret>
> ```
>
> Supply **both** the client id and secret. The deploy validates the **client id** — turning OBO on
> without it stops the deploy with a clear error. The **secret is not checked at deploy time**, but
> it is required for a confidential OAuth app: if you omit it, the deploy still succeeds and then the
> user consent step fails later with an opaque OAuth error. So always pass both together.

---

## Step 4 — Use it

**Open the chat app.** Get its web address, then open it in the browser:

```bash
databricks apps get walmart-pharmacy-genie-one -p $P
```

Look for the `url` value in the output and open it.

**Test the MCP server from the terminal.** First check it's healthy, then ask it a question:

```bash
dao-ai mcp inspect --app mcp-walmart-pharmacy-genie-one -p $P

dao-ai mcp call walmart_pharmacy_genie_one \
  --app mcp-walmart-pharmacy-genie-one \
  --args '{"input":"What is the OutcomesOne successful completion rate at the LOB level?"}' \
  -p $P
```

**Add it to Genie One.** In the Genie One screen, add the MCP connection named
`mcp_walmart_pharmacy_genie_one_conn` to a chat. You do this once.

**Use it from the AI Playground.** Pick the OpenAI-style model, add the same MCP tool, and ask a
question.

Questions to try:

- "Show completion rate and validation rate by market."
- "Script sales this year vs last year by market."
- "What's the digital population at the LOB level?"
- "Compare digital adoption and refill rates by region."

---

## Step 5 — Confirm it worked (optional checks)

**The connection was created (per-user mode).** It should show `OAUTH_U2M_MAPPING`:

```bash
databricks connections get mcp_walmart_pharmacy_genie_one_conn -p $P
```

**The MCP service is registered and active:**

```bash
databricks api get "/api/2.1/unity-catalog/mcp-services/$CAT.$SCH.mcp_walmart_pharmacy_genie_one" -p $P
```

**Requests are running as the signed-in user (per-user mode).** The app log line for each request
shows `obo_present=True` and the caller's email:

```bash
databricks apps logs mcp-walmart-pharmacy-genie-one -p $P | grep obo_present
```

---

## Stop it or redeploy

Tear down the **MCP server** (app, experiment, and — in per-user mode — the connection):

```bash
dao-ai agent down --as-mcp -c walmart_pharmacy_genie_one.yaml -p $P $PARAMS
```

If you also deployed the **chat app** (Step 3, the `dao-ai agent up` without `--as-mcp`), it's a
separate app (`walmart-pharmacy-genie-one`) and the command above does **not** remove it. Tear it
down too:

```bash
dao-ai agent down -c walmart_pharmacy_genie_one.yaml -p $P $PARAMS
```

To redeploy after a failed or stuck deploy, run `dao-ai agent down` first, then `dao-ai agent up`
again. A clean teardown avoids leftover state from a previous attempt.

---

## If something goes wrong

| What you see | What to do |
|--------------|------------|
| `--with-connection requires --as-mcp` | Add `--as-mcp` to the command. |
| Deploy stops asking for a client id/secret | You turned on the per-user option. Add `mcp_oauth_client_id` and `mcp_oauth_client_secret`, or remove `on_behalf_of_user=true`. |
| Microsoft 365 / Google / Atlassian tools are missing | Each person must connect their account once, from the workspace, before those tools appear. |
| "Model not found" or a model error | The `LLM` value must be an approved OpenAI-style endpoint. |
| Model error: "'databricks-…' is no longer available. Use Unity Catalog model services (v3)." | This workspace's AI Gateway wants the UC model-service address. Set `--param llm=system.ai.<model>` (e.g. `system.ai.gpt-oss-120b`) instead of the `databricks-<model>` name. |
| Consent screen: "OAuth application with client_id '…' not available in Databricks account '…'." | The OAuth app is in the wrong account. It must be created in the same account that owns the workspace you deployed into (see the admin section). |
| Deploy fails: "Unexpectedly failed to update app's OAuth scopes. Please try again later." | Changing the model or scopes on an already-running app can fail the in-place scope update. Run `dao-ai agent down …` then `dao-ai agent up …` for a clean redeploy. |
| The connection stops working after about an hour | Ask your administrator to recreate the OAuth app with the `offline_access` scope. |
| Deploy fails because the app is still starting | Wait a moment and run the same command again. |
| Deploy fails with "No command to run and no Python file found" | The app was left in a bad state by an earlier deploy. Run `dao-ai agent down …` then `dao-ai agent up …` for a clean redeploy. Do not hand-edit the generated files. |
| `ModuleNotFoundError: No module named 'databricks...'` when running `dao-ai` | `dao-ai` isn't fully installed in the Python you're using. Install it into a clean virtual environment and run it from there. |

---

## Access the administrator must grant

Give this section to your Databricks administrator. There are two modes — pick one:

- **Shared account (default):** everyone's requests run as one service account. Simplest to set up.
- **Per-user:** each request runs as the signed-in user. Needed if you want each person to see only
  their own data, or to use the Microsoft 365 / Google / Atlassian tools.

**Grants for both modes** (grant to the service account for shared mode, or to the users/group for
per-user mode):

- `USE CATALOG` on the catalog and `USE SCHEMA` + `CREATE` on the schema (for the deployer).
- `CAN QUERY` on the OpenAI-style model endpoint.
- `CAN RUN` on the three Genie spaces.
- `CAN MANAGE` on the app for whoever deploys it.

The deploy step grants the connection and MCP service permissions automatically.

**Extra steps for per-user mode only:**

1. Create a dedicated OAuth app (account admin, one time). Replace `<workspace-host>` with the host
   of the workspace you deploy into (e.g. `dbc-xxxx.cloud.databricks.com`):

   ```bash
   databricks account custom-app-integration create --json '{
     "name": "walmart-mcp-u2m",
     "redirect_urls": ["https://<workspace-host>/login/oauth/http.html"],
     "confidential": true,
     "scopes": ["all-apis","offline_access","openid","email","profile"],
     "token_access_policy": {"access_token_ttl_in_minutes": 60,
                              "refresh_token_ttl_in_minutes": 10080}}'
   ```

   Give the returned **client id** and **client secret** to whoever deploys. Keep `offline_access`
   in the list — without it the connection stops working about an hour after each sign-in.

   > **Critical — same account:** the OAuth app must be created in the **same Databricks account
   > that owns the workspace you deploy into**. If the app lives in a different account, the consent
   > screen fails with *"OAuth application with client_id '…' not available in Databricks account
   > '…'."* Confirm the account with `databricks auth describe -p <account-profile>` before creating.
   >
   > **Redirect URL:** it is the **workspace host** + `/login/oauth/http.html` — not the app's URL,
   > and not `/.auth/callback` (that belongs to the deployed app's *own* auto-generated integration,
   > which cannot be reused here). If you move the deployment to a different workspace, update this
   > app's `redirect_urls` to the new workspace host.

2. Each user signs in to approve access once, and needs `CAN USE` on the app.

3. To use the Microsoft 365 / Google / Atlassian tools, each user connects their account once from
   `…/explore/data/mcp-services/system/ai/<service>` in the workspace.
