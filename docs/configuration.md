# Configuration reference

Configuration is split by sensitivity:

- **Secrets and endpoints:** environment variables, or a `.env` file in the repository root.
- **Behavior:** `profile.yaml`.

Real environment variables take precedence over `.env`.

## Environment variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | for `--send` | | Bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | for `--send` | | Numeric id of the chat that receives the digest |
| `ROUTER_BASE_URL` | no | `http://localhost:20128/v1` | OpenAI-compatible base URL |
| `ROUTER_API_KEY` | yes (scoring) | | Bearer key for the gateway |
| `SCORING_MODEL` | no | `job-scorer` | Model or gateway combo used for scoring |
| `RADAR_DB_PATH` | no | `./data/jobs.db` | SQLite database location |
| `RADAR_PROFILE` | no | `./profile.yaml` | Profile location; falls back to `profile.example.yaml` |

Never commit real values. `.env.example` documents each variable.

## `profile.yaml`

The profile drives both the pre-filter and the model prompt. Start from `profile.example.yaml`.

### Candidate description (used in the prompt)

| Key | Type | Description |
| --- | --- | --- |
| `summary` | text | Short description of experience and strengths |
| `skills` | map of lists | Grouped skills, for example `languages`, `backend` |
| `target_roles` | list | Roles you are looking for |
| `levels` | list | Seniority you accept (`intern`, `junior`, `mid`, ...) |

### Preferences

| Key | Default | Description |
| --- | --- | --- |
| `preferences.min_score` | `60` | Minimum score (0-100) for a job to be included in the digest |
| `preferences.language` | `English` | Language of the one-sentence reason in each entry |
| `preferences.work_mode` | `remote` | Informational |

### Pre-filter rules

All matching is case-insensitive and whole-word (so `ai` does not match `mail`).

| Key | Effect |
| --- | --- |
| `filters.title_include` | The title must contain at least one of these terms |
| `filters.title_exclude` | The title is rejected if it contains any of these terms |
| `filters.location_allow` | Location terms that welcome you; they override `location_block` |
| `filters.location_block` | Location terms that exclude you; the job is rejected unless an allow term is also present |
| `filters.description_exclude` | Phrases in the description that imply residency or work-authorization requirements |

An empty or unrecognised location always passes the pre-filter and is left to the model.

Use `python -m radar filter-report` to see how many stored postings each rule removes before
you commit to a change.

## Command-line flags

`python -m radar <command>`:

| Command | Flags |
| --- | --- |
| `fetch` | none |
| `score` | `--limit N` (default 20) |
| `filter-report` | none |
| `run` | `--no-fetch`, `--score-limit N` (default 40), `--min-score N`, `--preview`, `--dry-run`, `--send` |

Exit codes: `0` success (including "nothing to report"), non-zero on failure.
