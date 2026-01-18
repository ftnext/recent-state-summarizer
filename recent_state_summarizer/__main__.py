import argparse
import sys
import tempfile
from textwrap import dedent

from recent_state_summarizer.fetch import _main as fetch_main
from recent_state_summarizer.fetch import build_parser as build_fetch_parser
from recent_state_summarizer.summarize import summarize_titles


def build_parser():
    help_message = """
    Summarize blog article titles with the OpenAI API.

    ⚠️ Set `OPENAI_API_KEY` environment variable.

    Example:
        omae-douyo https://awesome.hatenablog.com/archive/2023

    Retrieve the titles of articles from a specified URL.
    After summarization, prints the summary.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=dedent(help_message),
    )
    subparsers = parser.add_subparsers(dest="subcommand")

    run_parser = subparsers.add_parser(
        "run", help="Fetch article titles and generate summary (default)"
    )
    run_parser.add_argument("url", help="URL of archive page")
    run_parser.set_defaults(func=run_cli)

    fetch_parser = subparsers.add_parser(
        "fetch",
        parents=[build_fetch_parser(add_help=False)],
        help="Fetch article titles only and save to file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    fetch_parser.set_defaults(func=fetch_cli)

    return parser


def run_cli(args):
    with tempfile.NamedTemporaryFile(mode="w+") as tempf:
        fetch_main(args.url, tempf.name, save_as_title_list=True)
        tempf.seek(0)
        titles = tempf.read()
    summary = summarize_titles(titles)
    print(summary)


def fetch_cli(args):
    fetch_main(args.url, args.save_path, save_as_title_list=args.as_title_list)


def normalize_argv() -> list[str]:
    argv = sys.argv[1:]
    if len(argv) == 0:
        return ["--help"]

    help_flags = {"-h", "--help"}
    if argv[0] in help_flags:
        return argv

    known_subcommands = {"run", "fetch"}
    if argv[0] not in known_subcommands:
        return ["run"] + argv

    return argv


def main():
    parser = build_parser()
    argv = normalize_argv()
    args = parser.parse_args(argv)
    args.func(args)
