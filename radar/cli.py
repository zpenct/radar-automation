"""Command-line interface: ``python -m radar <command>``.

Output contract: only the digest text goes to stdout. Logs go to stderr. A
scheduler such as Hermes cron can therefore forward stdout verbatim, and an
empty stdout means "nothing to report".
"""
import argparse
import logging
import sys
from collections import Counter

from radar import db, fetch, pipeline, profile, score, telegram
from radar.filters import HardFilter


def _filter_report() -> None:
    hard_filter = HardFilter(profile.load())
    rows = db.all_jobs(db.connect())
    reasons: Counter[str] = Counter()
    passed = []
    for row in rows:
        ok, reason = hard_filter.check(row)
        reasons[reason] += 1
        if ok:
            passed.append(row)
    print(f"{len(rows)} jobs stored, {len(passed)} pass the pre-filter")
    for reason, count in reasons.most_common():
        print(f"  {count:4d}  {reason}")


def _run(args: argparse.Namespace) -> int:
    message, rows = pipeline.run(
        do_fetch=not args.no_fetch,
        score_limit=args.score_limit,
        preview=args.preview,
        min_score=args.min_score,
    )
    if not message:
        logging.getLogger("radar").info("no jobs meet the threshold")
        return 0

    if args.send:
        count = telegram.send(message)
        logging.getLogger("radar").info("sent %d Telegram message(s)", count)
    else:
        sys.stdout.write(message + "\n")

    if not (args.preview or args.dry_run):
        db.mark_sent(db.connect(), rows)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="radar", description="Daily job digest pipeline.")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("fetch", help="fetch new postings from all sources")

    score_cmd = commands.add_parser("score", help="score unscored postings")
    score_cmd.add_argument("--limit", type=int, default=20)

    commands.add_parser("filter-report", help="show how the pre-filter classifies stored jobs")

    run_cmd = commands.add_parser("run", help="fetch, score and build the digest")
    run_cmd.add_argument("--no-fetch", action="store_true", help="skip the fetch stage")
    run_cmd.add_argument("--score-limit", type=int, default=40)
    run_cmd.add_argument("--min-score", type=int, help="override preferences.min_score")
    run_cmd.add_argument(
        "--preview", action="store_true", help="include already-sent jobs; mark nothing"
    )
    run_cmd.add_argument("--dry-run", action="store_true", help="do not mark jobs as sent")
    run_cmd.add_argument("--send", action="store_true", help="deliver via the Telegram Bot API")
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = build_parser().parse_args(argv)

    if args.command == "fetch":
        fetch.run()
    elif args.command == "score":
        score.run(limit=args.limit)
    elif args.command == "filter-report":
        _filter_report()
    elif args.command == "run":
        return _run(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
