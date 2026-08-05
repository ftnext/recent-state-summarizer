# recent-state-summarizer

Summarize blog article titles with the OpenAI API

a.k.a. _RSS_ 😃

## Setup

```
$ pip install recent-state-summarizer
```

⚠️ Set `OPENAI_API_KEY` environment variable.  
ref: https://platform.openai.com/account/api-keys

## Usage

```
$ omae-douyo https://nikkie-ftnext.hatenablog.com/archive/2023/4

この人物は最近、プログラミングに関することを中心にして活動しています。

（略）

最近は、株式会社はてなに入社したようです。
```

Currently support:

- はてなブログ（Hatena blog）
- はてなブックマークRSS
- Adventar
- Qiita Advent Calendar

To see help, type `omae-douyo -h`.

### Fetch only (save to file)

Fetch titles and URLs of articles, and save them to a file without summarization:

```
# Save as JSON format (default)
$ omae-douyo fetch https://nikkie-ftnext.hatenablog.com/archive/2023/4 articles.jsonl

# Save as bullet list
$ omae-douyo fetch https://nikkie-ftnext.hatenablog.com/archive/2023/4 titles.txt --as-title-list
```

#### GitHub Changelog

The `github-blog` sub-command fetches the GitHub Changelog without specifying its feed URL:

```
$ omae-douyo fetch github-blog articles.jsonl

# Change the period to fetch entries from (default: 30 days)
$ omae-douyo fetch github-blog articles.jsonl --days 45
```

## Development

### Sub commands

Fetch only (same as `omae-douyo fetch`):

```
python -m recent_state_summarizer.fetch -h
```

Summarize only:  
It's convenient to omit fetching in tuning the prompt.

```
python -m recent_state_summarizer.summarize -h
```

### Environment

```
$ git clone https://github.com/ftnext/recent-state-summarizer.git
$ cd recent-state-summarizer

$ python -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.lock
(venv) $ pip install -e '.'
```
