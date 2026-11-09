import argparse
import asyncio
import collections
import difflib
import glob
import json
import logging
import os
import sys

from datetime import timedelta

from ncaapyscraper import __version__
from ncaapyscraper.api import (
    fetch_schools,
    fetch_scoreboard,
    fetch_boxscore,
    fetch_rankings,
    fetch_standings,
    fetch_stat_list,
    fetch_stats,
    fetch_games,
)
from ncaapyscraper.constants import DATA_TYPES, NCAA_SPORTS, GAME_KEY, BOXSCORE_KEY
from ncaapyscraper.ncaa import to_date
from ncaapyscraper.output import summary, write_result, write_rows, school_tables
from ncaapyscraper.schools import SCHOOLS, ALIASES, find_school, pick_schools, conference_name


COMMANDS = {
    'scores': 'every game on a day, or a football week',
    'boxscore': 'player stats for one game',
    'rankings': 'polls like the AP Top 25',
    'standings': 'conference standings',
    'stats': 'national stat leaders',
    'games': 'every game (and box score) over a date range, merged into files',
    'export': 'school json files to players, coaches and schedules tables',
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog='ncaapyscraper',
        description='Rosters, coaches and schedules from college athletics websites, saved as JSON.',
        epilog=f'Scores and stats from ncaa.com: ncaapyscraper {{{",".join(COMMANDS)}}} -h',
    )
    parser.add_argument('schools', nargs='*', help='school keys or sites, e.g. duke alabama goduke.com')
    parser.add_argument('-a', '--all', action='store_true', help='every supported school')
    parser.add_argument('-c', '--conference', help='every school in a conference, e.g. sec, big10, "Big Sky"')
    parser.add_argument('-d', '--division', choices=['1', '2', '3', 'fbs', 'fcs'], help='every school in an NCAA division')
    parser.add_argument('-s', '--sport', action='append', default=[], help='only these sports, e.g. football or mens-basketball,baseball')
    parser.add_argument('-g', '--gender', choices=['men', 'women'], help="only men's or women's teams")
    parser.add_argument('--players', action='store_true', help='athletes only')
    parser.add_argument('--coaches', action='store_true', help='coaches and staff only')
    parser.add_argument('--schedules', action='store_true', help='schedules only')
    parser.add_argument('--no-bios', action='store_true', help='leave out bios, files get a lot smaller')
    parser.add_argument('--compact', action='store_true', help='write json without indentation')
    parser.add_argument('-o', '--output', default='output', help='folder for the json files (default: output)')
    parser.add_argument('-p', '--parallel', type=int, default=4, help='schools to scrape at once (default: 4)')
    parser.add_argument('-l', '--list', action='store_true', help='list supported schools and exit, works with -c and -d')
    parser.add_argument('--conferences', action='store_true', help='list conferences and exit')
    parser.add_argument('-v', '--verbose', action='store_true', help='log every request')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')

    return parser, parser.parse_args(argv)


def parse_command(argv):
    parser = argparse.ArgumentParser(prog='ncaapyscraper', description='Scores, box scores, rankings, standings and stat leaders from ncaa.com.')
    commands = parser.add_subparsers(dest='command', required=True)
    parsers = {command: commands.add_parser(command, help=text, description=text) for command, text in COMMANDS.items()}
    sport_help = f'one of {", ".join(NCAA_SPORTS)}'

    for command in ['scores', 'rankings', 'standings', 'stats']:
        parsers[command].add_argument('sport', help=sport_help)
        parsers[command].add_argument('-d', '--division', help='d1, d2, d3, fbs or fcs (default: fbs for football, d1 for the rest)')

    parsers['scores'].add_argument('--date', help='YYYY-MM-DD (default: today)')
    parsers['scores'].add_argument('--week', type=int, help='football week (default: the current one)')
    parsers['scores'].add_argument('--season', type=int, help='year the season started (default: the current one)')

    parsers['boxscore'].add_argument('game_id', help='game_id from scores, or the number in an ncaa.com game url')
    parsers['boxscore'].add_argument('--sport', help='saves a request when you know it')

    parsers['rankings'].add_argument('--poll', help='end of the ncaa.com rankings url, e.g. associated-press')

    parsers['stats'].add_argument('stat', nargs='?', help='stat name or id, e.g. "Rushing Yards" or 469. Leave out to list them all')
    parsers['stats'].add_argument('--team', action='store_true', help='team stats instead of individual')

    parsers['games'].add_argument('--since', help='first day, YYYY-MM-DD (default: --days before --until)')
    parsers['games'].add_argument('--until', help='last day, YYYY-MM-DD (default: yesterday)')
    parsers['games'].add_argument('--days', type=int, default=7, help='days to go back when there is no --since (default: 7)')
    parsers['games'].add_argument('-s', '--sport', action='append', default=[], help=f'only these sports (default: all), {sport_help}')
    parsers['games'].add_argument('--boxscores', action='store_true', help='box scores of finished games too')

    parsers['export'].add_argument('input', help='folder with school json files')

    folders = {
        'games': ('output', 'folder for games and boxscores files, games already in them are kept and updated (default: output)'),
        'export': ('tables', 'folder for players, coaches and schedules files (default: tables)'),
    }
    for command, (folder, folder_help) in folders.items():
        parsers[command].add_argument('-f', '--format', choices=['json', 'csv', 'parquet'], default='parquet', help='file format (default: parquet)')
        parsers[command].add_argument('-o', '--output', default=folder, help=folder_help)

    for command in ['scores', 'boxscore', 'rankings', 'standings', 'stats']:
        parsers[command].add_argument('-o', '--output', help='save to a .json, .csv or .parquet file instead of printing json')

    for command_parser in parsers.values():
        command_parser.add_argument('-v', '--verbose', action='store_true', help='log every request')

    return parser.parse_args(argv)


def list_schools(keys):
    print(f"{'KEY':<34} {'DIV':<4} {'PLATFORM':<15} {'SITE':<30} SCHOOL")

    for key in keys:
        school = SCHOOLS[key]
        division = school['subdivision'] or school['division']
        print(f"{key:<34} {division!s:<4} {school['platform']:<15} {school['site']:<30} {school['name']}")


def list_conferences():
    counts = collections.Counter((school['conference'], school['division']) for school in SCHOOLS.values())
    print(f"{'DIV':<4} {'SCHOOLS':<8} CONFERENCE")

    for (conference, division), count in sorted(counts.items(), key=lambda row: (row[0][1], row[0][0])):
        print(f"{division:<4} {count:<8} {conference}")


def pick(args):
    if args.schools:
        keys = []
        for value in args.schools:
            school = find_school(value)
            if not school:
                close = difflib.get_close_matches(value.lower(), list(SCHOOLS) + list(ALIASES), n=3)
                hint = close and f", did you mean {', '.join(close)}?" or ', run with --list to see them all'
                sys.exit(f'Unknown school "{value}"{hint}')

            keys.append(school['key'])

        return list(dict.fromkeys(keys))

    if args.conference and not conference_name(args.conference):
        sys.exit(f'Unknown conference "{args.conference}", run with --conferences to see them all')

    if args.all or args.conference or args.division:
        return pick_schools(args.conference, args.division)

    return []


async def scrape(keys, args, data):
    failed = await scrape_batch(keys, args, data)

    # Busy school sites time out now and then, one more go before giving up
    if failed:
        failed = await scrape_batch(failed, args, data)

    return failed


async def scrape_batch(keys, args, data):
    failed = []
    options = {'sports': args.sport, 'data': data, 'gender': args.gender, 'bios': not args.no_bios}

    async for key, result in fetch_schools(keys, parallel=args.parallel, **options):
        if isinstance(result, Exception):
            failed.append(key)
            print(f"{key:<34} failed: {result}")
            continue

        path = write_result(result, args.output, None if args.compact else 2)
        counts = summary(result)
        print(
            f"{key:<34} {counts['sports']:>3} sports {counts['players']:>5} players "
            f"{counts['coaches']:>4} coaches {counts['games']:>4} games  -> {path}"
        )

    return failed


async def run_ncaa(args):
    if args.command == 'scores':
        rows = await fetch_scoreboard(args.sport, args.date, args.division, args.week, args.season)
    elif args.command == 'boxscore':
        rows = await fetch_boxscore(args.game_id, args.sport)
    elif args.command == 'rankings':
        rows = await fetch_rankings(args.sport, args.division, args.poll)
    elif args.command == 'standings':
        rows = await fetch_standings(args.sport, args.division)
    elif args.stat:
        rows = await fetch_stats(args.sport, args.stat, args.division, args.team)
    else:
        rows = await fetch_stat_list(args.sport, args.division)

    if not args.output:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return

    write_rows(rows, args.output)
    print(f'{len(rows)} rows -> {args.output}')


async def run_games(args):
    until = args.until and to_date(args.until) or to_date() - timedelta(days=1)
    since = args.since and to_date(args.since) or until - timedelta(days=args.days - 1)

    games, players = await fetch_games(since, until, args.sport, args.boxscores)
    print(f'{len(games)} games and {len(players)} box score rows from {since} to {until}')

    files = [('games', games, GAME_KEY)] + (args.boxscores and [('boxscores', players, BOXSCORE_KEY)] or [])
    for name, rows, key in files:
        path = os.path.join(args.output, f'{name}.{args.format}')
        print(f'{write_rows(rows, path, key):>8} rows -> {path}')


def run_export(args):
    results = []
    for path in sorted(glob.glob(os.path.join(args.input, '*.json'))):
        with open(path, encoding='utf-8') as input_file:
            result = json.load(input_file)

        # index.json and anything else that isn't a school
        if isinstance(result, dict) and 'sports' in result:
            results.append(result)

    for name, rows in school_tables(results).items():
        path = os.path.join(args.output, f'{name}.{args.format}')
        print(f'{write_rows(rows, path):>8} rows -> {path}')


def run_command(argv):
    args = parse_command(argv)
    setup_logging(args.verbose)

    try:
        if args.command == 'export':
            run_export(args)
        elif args.command == 'games':
            asyncio.run(run_games(args))
        else:
            asyncio.run(run_ncaa(args))
    except (ValueError, ConnectionError, ImportError) as error:
        sys.exit(str(error))
    except KeyboardInterrupt:
        sys.exit(130)


def setup_logging(verbose):
    logging.basicConfig(
        level=verbose and logging.DEBUG or logging.WARNING,
        format='%(asctime)s %(levelname)s %(message)s',
    )
    for noisy in ['httpx', 'httpcore', 'asyncio']:
        logging.getLogger(noisy).setLevel(logging.WARNING)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in COMMANDS:
        run_command(argv)
        return

    parser, args = parse_args(argv)
    setup_logging(args.verbose)

    if args.conferences:
        list_conferences()
        return

    keys = pick(args)

    if args.list:
        list_schools(keys or (not args.schools and list(SCHOOLS)) or [])
        return

    if not keys:
        parser.print_help()
        return

    data = [data_type for data_type in DATA_TYPES if getattr(args, data_type)] or DATA_TYPES

    try:
        failed = asyncio.run(scrape(keys, args, data))
    except KeyboardInterrupt:
        sys.exit(130)

    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
