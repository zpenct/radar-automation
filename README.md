# Job Radar

A small, self-hosted pipeline that watches remote job boards, discards obvious mismatches with
cheap rules, asks an LLM to score the rest against your profile, and sends you a short Telegram
digest of the jobs worth your time.

```text
Remotive · Remote OK · We Work Remotely
              │
              ▼
   fetch ─► SQLite ─► rule-based pre-filter ─► LLM scoring ─► digest ─► Telegram
                                                   │
                                          OpenAI-compatible gateway
                                          (9router: fallback across providers)
```

## Why it exists

Job boards return hundreds of postings a day, and most are irrelevant: wrong seniority, wrong
domain, or "remote" with a hidden country restriction. Reading them is slow. Sending every
posting to an LLM is slow and expensive. Job Radar splits the work:

1. **Rules first.** A deterministic pre-filter removes postings by title, seniority and location
   before any model call. In practice this drops more than 95% of postings.
2. **LLM second.** Only the survivors are scored 0-100 with a one-sentence reason. The model
   reads the full description, so it catches restrictions that structured fields miss
   (for example a feed that says "Anywhere" while the text requires US residency).
3. **Deliver once.** Each posting is stored with a status (`new` → `scored` → `sent`) so it is
   delivered at most once, and the digest stays empty, with no message at all, on quiet days.

## Features

- Three job sources behind one adapter interface; a failing source never blocks the others.
- Deterministic pre-filter configured entirely from `profile.yaml`.
- Model access through any OpenAI-compatible endpoint. The reference setup uses
  [9router](https://github.com/decolua/9Router) so scoring fails over between providers
  automatically.
- Idempotent storage in SQLite with de-duplication on `(source, external_id)`.
- Telegram delivery that keeps the bot token out of logs and error messages.
- A strict output contract (digest on stdout, logs on stderr, silence when empty) so any
  scheduler can run it unchanged.
- Container image and Compose stack for VPS deployment, plus an optional Hermes agent.
- Unit-tested core (39 tests) with lint and CI.

## Quick start

Requirements: Python 3.11+, a Telegram bot token, and an OpenAI-compatible endpoint.

```bash
git clone <repository-url> job-radar && cd job-radar
python -m venv .venv
.venv/bin/pip install -r requirements.txt      # Windows: .venv\Scripts\pip

cp .env.example .env                           # fill in the values
cp profile.example.yaml profile.yaml           # describe yourself and your filters

.venv/bin/python -m radar run --dry-run        # print the digest, send nothing
.venv/bin/python -m radar run --send           # deliver it over Telegram
```

The full walkthrough, including setting up the gateway and Telegram bot, is in
[docs/local-setup.md](docs/local-setup.md).

## Commands

| Command | Purpose |
| --- | --- |
| `python -m radar run` | Fetch, score and print the digest to stdout |
| `python -m radar run --send` | Same, but deliver through the Telegram Bot API |
| `python -m radar run --preview --min-score 40` | Show top-scored jobs, including already sent ones |
| `python -m radar run --dry-run` | Do everything except mark jobs as sent |
| `python -m radar fetch` | Only fetch and store new postings |
| `python -m radar score --limit 20` | Only score pending postings |
| `python -m radar filter-report` | Explain how the pre-filter classifies stored jobs |

## Configuration

Secrets live in `.env`; behavior lives in `profile.yaml`. Both are git-ignored, and annotated
templates are committed. See [docs/configuration.md](docs/configuration.md) for every option.

## Documentation

| Document | Contents |
| --- | --- |
| [docs/architecture.md](docs/architecture.md) | Pipeline stages, data model, design decisions, failure handling |
| [docs/local-setup.md](docs/local-setup.md) | Step-by-step local installation and scheduling |
| [docs/deployment-vps.md](docs/deployment-vps.md) | Docker Compose and Dokploy deployment, hardening, operations |
| [docs/configuration.md](docs/configuration.md) | Environment variables, profile schema, CLI flags |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Problems encountered in practice and their fixes |
| [docs/data-sources.md](docs/data-sources.md) | Provider terms, attribution and polling etiquette |

## Project layout

```text
radar/              application package
  sources.py        job-board adapters
  filters.py        rule-based pre-filter
  score.py          LLM scoring client
  digest.py         selection and rendering
  telegram.py       delivery
  db.py             SQLite access
  pipeline.py       stage orchestration
  cli.py            command-line interface
tests/              unit tests
deploy/             Compose stack and Hermes cron wrapper
docs/               documentation
```

## Development

```bash
pip install -r requirements-dev.txt
ruff check .
pytest
```

CI runs lint and tests on Python 3.11 and 3.12 and builds the container image.

## Limitations and roadmap

- Volume is modest by design. In testing, about 155 stored postings produced 6 that passed the
  pre-filter and 2 that scored above the default threshold. Adding sources is the main lever;
  each one is a single function in `radar/sources.py`.
- Scoring quality depends on the profile and the model; there is no labelled evaluation set yet.
- Planned: more sources (including regional boards), Telegram inline actions (apply, skip),
  feedback-driven scoring, and an evaluation harness with labelled postings.

## Responsible use

Job Radar is built for personal job searching. It uses public APIs and feeds, identifies itself
with a descriptive `User-Agent`, polls infrequently, and credits the source in every digest
entry. Review each provider's terms before changing the polling frequency or redistributing
results; see [docs/data-sources.md](docs/data-sources.md).

## License

[MIT](LICENSE)
