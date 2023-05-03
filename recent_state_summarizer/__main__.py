import argparse

from recent_state_summarizer.fetch import fetch_titles_as_bullet_list
from recent_state_summarizer.summarize import summarize_titles


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    return parser.parse_args()


def main():
    args = parse_args()

    titles = fetch_titles_as_bullet_list(args.url)
    summary = summarize_titles(titles)
    print(summary)
