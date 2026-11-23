# Data sources

Job Radar reads public job feeds. This page records how each one is used and what etiquette
applies. It is a summary of our understanding, not legal advice; read each provider's current
terms before changing how often you poll or what you do with the data.

| Source | Interface | Adapter |
| --- | --- | --- |
| Remotive | JSON API (`/api/remote-jobs`, categories `software-dev` and `data`) | `fetch_remotive` |
| Remote OK | JSON API (`/api`) | `fetch_remoteok` |
| We Work Remotely | RSS (programming category) | `fetch_weworkremotely` |

## Etiquette built in

- **Identification.** Requests send a descriptive `User-Agent`.
- **Low frequency.** The intended schedule is once a day. Providers ask consumers not to poll
  aggressively; do not run the fetch stage in a tight loop. For local experiments use
  `--no-fetch` to reuse stored data.
- **Attribution.** Every digest entry names its source and links to the original posting.
- **No scraping of pages.** Only the published API and feed endpoints are used.
- **Legal notices.** Remote OK's response begins with a notice object; the adapter skips it
  and the source is credited in every entry.

## Region data is unreliable

Feeds describe location loosely. One provider labels most postings "Anywhere" even when the
description restricts applicants to specific countries. The pre-filter therefore does not trust
an "Anywhere" label on its own; the scoring model reads the description and penalises
residency or work-authorization requirements.

## Adding a source

1. Confirm the provider offers an API or feed intended for programmatic use and read its terms.
2. Add an adapter to `radar/sources.py` that returns the shared schema and register it in
   `SOURCES`.
3. Add a parser test using a saved sample payload.
4. Add the display name to `SOURCE_NAMES` in `radar/digest.py` so entries are attributed.

## Personal use

The project is designed for an individual's own job search. If you adapt it into a service that
redistributes postings to other people, review each provider's terms for redistribution and
commercial-use restrictions first.
