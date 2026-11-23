# Troubleshooting

Problems met while building and running the project, with the cause and the fix.

## LLM gateway

| Symptom | Cause | Fix |
| --- | --- | --- |
| Adding a provider key always shows "invalid" in the dashboard, for every provider | A bug in the validation button of an older gateway release (observed on 0.5.116) | Upgrade (`npm install -g 9router@latest`) and retry. Update first when behavior looks wrong. |
| HTTP 404 "model is no longer available to new users" | The provider retired that model name | Pick a current model from the dashboard's model list. Reference a combo instead of a raw model name so a retirement is a one-place fix. |
| HTTP 503 "high demand" / "UNAVAILABLE" | Provider capacity, usually on popular models | Retry later, or add a second provider to the combo so the gateway fails over. |
| HTTP 401 "Invalid API key" from the application | The application holds a provider key instead of the **gateway** key, or the key has stray whitespace | Use the key from the gateway's *Endpoint & Key* page. |
| Gateway prints "Exiting..." repeatedly in a background shell | The default launch expects an interactive terminal | Start it with `9router --host 127.0.0.1 --no-browser --skip-update --log`. |
| Gateway reachable from other machines on the network | The default bind address is `0.0.0.0` | Start with `--host 127.0.0.1`, or bind the Docker port to `127.0.0.1`. |
| Prompt token counts far above the prompt you sent | Something in the gateway path adds content to every request (the cause was not identified in this project) | Compare `usage.prompt_tokens` against a minimal request, then review gateway features that rewrite prompts and disable them one by one. |

Seeing the real error body: some shells hide response bodies on HTTP errors. `curl.exe -s` shows
the JSON error the provider returned, which usually names the exact cause.

## Pipeline

| Symptom | Cause | Fix |
| --- | --- | --- |
| No digest arrives | Nothing new met `min_score`. This is normal and silent by design | Run `python -m radar filter-report`, then `python -m radar run --no-fetch --preview --min-score 30` to see what was scored. |
| Few postings pass the pre-filter | Rules are strict | Adjust `profile.yaml` using `filter-report` to see which rule removes what. |
| `Missing required setting: ROUTER_API_KEY` | `.env` not found or empty | Create `.env` in the repository root (or pass real environment variables). |
| A job was marked `sent` but never arrived | A run delivered nothing (for example stdout was discarded) after marking | Reset it: `UPDATE jobs SET status='scored' WHERE ...`, then run again with `--send`. Always check that the delivery step succeeded before trusting the status. |
| Scoring log shows `scoring 0 jobs` | Everything pending was already scored or filtered out | Expected after a run with no new matching postings. |

## Telegram

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Telegram rejected the message: HTTP 400 chat not found` | You never messaged the bot, or the chat id is wrong | Send a message to the bot first; use your numeric user id. |
| `HTTP 401` from Telegram | Wrong or revoked token | Create a new token in @BotFather (`/token`). |

## Windows

| Symptom | Cause | Fix |
| --- | --- | --- |
| `hermes` is "not recognized" in a shell that was already open | The installer updates the user `PATH`, which existing shells do not see | Open a new terminal. |
| `UnicodeEncodeError` when printing text | Console code page cannot encode some characters | Run Python with `-X utf8` (the Hermes wrapper already does). |
| Messages like `NativeCommandError` after a command that succeeded | PowerShell wraps anything a native program writes to stderr | Check the exit code (`$LASTEXITCODE`), not the red text. Job Radar logs to stderr by design. |

## Security hygiene

- If a key ever appears in a chat, log, terminal capture or commit, revoke and replace it.
- Check history before publishing: `git log -p | grep -iE "token|secret|api_key"` should find
  nothing but placeholders.
