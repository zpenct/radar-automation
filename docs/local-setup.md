# Local setup

This guide takes you from a clean machine to a working digest in Telegram. Commands are shown
for Windows PowerShell and for POSIX shells where they differ.

## 1. Prerequisites

| Tool | Version | Used for |
| --- | --- | --- |
| Python | 3.11+ | The application |
| Node.js | 18+ | Running the 9router gateway (`npm`) |
| Git | any | Cloning the repository |
| A Telegram account | | Receiving the digest |

## 2. Install the application

```bash
git clone <repository-url> job-radar
cd job-radar
python -m venv .venv
```

```powershell
.venv\Scripts\pip install -r requirements.txt     # Windows
```

```bash
.venv/bin/pip install -r requirements.txt         # macOS / Linux
```

## 3. Set up the LLM gateway (9router)

Job Radar talks to any OpenAI-compatible endpoint. The reference setup uses 9router because it
gives one stable URL in front of several providers and fails over between them.

### 3.1 Install and start

```bash
npm install -g 9router
9router --host 127.0.0.1 --no-browser --skip-update
```

> **Bind to loopback.** By default 9router listens on `0.0.0.0`, which exposes the dashboard
> (and the provider keys it stores) to everyone on your network. Always pass
> `--host 127.0.0.1` unless you have a reason not to.

Open <http://localhost:20128> in a browser.

### 3.2 Add providers

In **Providers**, add one connection per provider key. Free tiers are enough for this project:

1. Create an API key with the provider (for example Google AI Studio for Gemini, or DeepSeek).
2. In the dashboard choose the provider, **Add Connection**, paste the key and save.

Use a current model name from the provider's model list in the dashboard. Providers retire models,
and a retired name returns HTTP 404 (see [troubleshooting](troubleshooting.md)).

### 3.3 Create a combo

A combo is a named, ordered list of models. Create one called `job-scorer`, with a cheap, fast
model first and a different provider second, in fallback mode. The application only ever refers
to `job-scorer`, so changing models later needs no code or configuration change.

### 3.4 Create an API key

Under **Endpoint & Key**, create a key for the application and copy it into `.env` in step 5.

### 3.5 Verify

```powershell
$key = Read-Host "Gateway API key" -AsSecureString
$plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
  [Runtime.InteropServices.Marshal]::SecureStringToBSTR($key))
$body = '{"model":"job-scorer","max_tokens":50,"messages":[{"role":"user","content":"Reply with one word: hello"}]}'
$body | curl.exe -s -X POST http://localhost:20128/v1/chat/completions `
  -H "Authorization: Bearer $plain" -H "Content-Type: application/json" --data-binary "@-"
```

A JSON (or event-stream) reply containing the model's answer means the gateway works.

## 4. Create the Telegram bot

1. In Telegram, open **@BotFather**, send `/newbot`, and follow the prompts. The username must
   end in `bot`. Save the token it gives you.
2. Send any message to your new bot so a chat exists.
3. Find your numeric user id, for example by messaging **@userinfobot**. This is your
   `TELEGRAM_CHAT_ID` for a private chat.

## 5. Configure

```bash
cp .env.example .env
cp profile.example.yaml profile.yaml
```

Edit `.env`:

```dotenv
TELEGRAM_BOT_TOKEN=<token from BotFather>
TELEGRAM_CHAT_ID=<your numeric id>
ROUTER_BASE_URL=http://localhost:20128/v1
ROUTER_API_KEY=<gateway key from step 3.4>
SCORING_MODEL=job-scorer
```

Edit `profile.yaml` with your summary, skills, target roles and filters. Every option is described
in [configuration.md](configuration.md).

## 6. First run

```bash
python -m radar run --dry-run
```

This fetches postings, scores the ones that pass the pre-filter, and prints the digest without
marking anything as sent. The first run may score a few dozen postings and take a minute.

Useful checks:

```bash
python -m radar filter-report                 # how the rules classify stored postings
python -m radar run --no-fetch --preview --min-score 30   # see lower-scoring jobs too
```

Deliver to Telegram:

```bash
python -m radar run --send
```

## 7. Schedule it

Run the command once a day. Be gentle with the job boards: once or twice daily is plenty.

### Windows Task Scheduler

```powershell
schtasks /Create /SC DAILY /ST 07:00 /TN "JobRadar" /TR "cmd /c cd /d C:\path\to\job-radar && .venv\Scripts\python.exe -m radar run --send"
```

### cron (Linux, macOS)

```cron
0 7 * * * cd /path/to/job-radar && .venv/bin/python -m radar run --send >> radar.log 2>&1
```

### Hermes cron (optional)

If you use the [Hermes agent](https://hermes-agent.nousresearch.com/docs) as your Telegram
front end, it can schedule the job and deliver the output itself, with no bot token in `.env`:

```powershell
./deploy/hermes/install.ps1
hermes cron create "0 7 * * *" --no-agent --script job_radar_daily.py `
  --deliver telegram --name job-radar-daily --timezone Asia/Jakarta --catch-up on
```

`--no-agent` makes Hermes run the script and deliver its stdout verbatim, without calling a
model, and an empty stdout is silent. The Hermes gateway must be running for the schedule
to fire, and `--catch-up on` runs a missed schedule when the machine comes back.

Whichever scheduler you choose, the gateway must be running when the job fires.

## Next

To run Job Radar on a server so it works while your computer is off, continue with
[deployment-vps.md](deployment-vps.md).
