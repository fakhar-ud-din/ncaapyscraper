import argparse
import asyncio
import collections
import difflib
import logging
import sys

from ncaapyscraper import __version__
from ncaapyscraper.api import fetch_schools
from ncaapyscraper.constants import DATA_TYPES
from ncaapyscraper.output import summary, write_result
from ncaapyscraper.schools import SCHOOLS, ALIASES, find_school, pick_schools, conference_name


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog='ncaapyscraper',
        description='Rosters, coaches and schedules from college athletics websites, saved as JSON.',
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


def main(argv=None):
    parser, args = parse_args(argv)

    logging.basicConfig(
        level=args.verbose and logging.DEBUG or logging.WARNING,
        format='%(asctime)s %(levelname)s %(message)s',
    )
    for noisy in ['httpx', 'httpcore', 'asyncio']:
        logging.getLogger(noisy).setLevel(logging.WARNING)

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
