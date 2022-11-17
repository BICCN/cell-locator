import argparse
import json
import sys
from pathlib import Path

from cl_convert import converters


def convert(args):
    # if src is '-', use stdin
    if args.src != Path('-'):
        with open(args.src) as src:
            data = json.load(src)
    else:
        data = json.load(sys.stdin)

    # if -v?, infer version
    if args.version.lower() in ('?', 'infer'):
        v, doc = converters.infer_normalize(data)
        print(f'Inferred version {v!r}', file=sys.stderr)
    else:
        v, vc = converters.find_latest(args.version)
        doc = vc.normalize(data)

    # convert to target version
    t, tc = converters.find_latest(args.target)
    data = tc.specialize(doc)

    # convert boolean indent to json.dump argument
    indent = 2 if args.indent else None

    # if dst is '-', use stdout
    if args.dst != Path('-'):
        args.dst.parent.mkdir(exist_ok=True, parents=True)
        dst = args.dst.open('w')
    else:
        dst = sys.stdout

    # dump output
    json.dump(data, dst, indent=indent)


def versions(args):
    print('\n'.join(converters.match(args.target)))


def infer(args):
    # if src is '-', use stdin
    if args.src != Path('-'):
        with open(args.src) as src:
            data = json.load(src)
    else:
        data = json.load(sys.stdin)

    v, doc = converters.infer_normalize(data)

    print(v)


def make_parser():
    parser = argparse.ArgumentParser(
        description=f'Convert Cell Locator annotation files between versions.',
    )

    subs = parser.add_subparsers(dest='cmd', title='subcommands', required=True)

    sub_convert = subs.add_parser(
        'convert',
        help='Convert between file versions.'
    )
    sub_convert.add_argument(
        'src', type=Path,
        help="Source JSON file. Use '-' to read from stdin.",
    )
    sub_convert.add_argument(
        'dst', type=Path,
        help="Destination JSON file. Use '-' to write to stdout.",
    )
    sub_convert.add_argument(
        '-v', '--version', required=True,
        help="Source file version. Use '-v?' to infer the version.",
    )
    sub_convert.add_argument(
        '-t', '--target', default='',
        help='Target file version. Defaults to the latest version.',
    )
    sub_convert.add_argument(
        '--no-indent', dest='indent', action='store_false', default=True,
        help='Do not indent output JSON.',
    )
    sub_convert.set_defaults(func=convert)

    sub_versions = subs.add_parser(
        'versions',
        help='Show all versions and exit.',
    )
    sub_versions.add_argument(
        'target', nargs='?', default='',
        help='Show versions matching this target. If empty, show all versions.',
    )
    sub_versions.set_defaults(func=versions)

    sub_infer = subs.add_parser(
        'infer',
        help='Show inferred version of file and exit.'
    )
    sub_infer.add_argument(
        'src', type=Path,
        help="Source JSON file. Use '-' to read from stdin.",
    )
    sub_infer.set_defaults(func=infer)

    return parser


def main():
    parser = make_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
