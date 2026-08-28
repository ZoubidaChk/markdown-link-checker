import argparse
import json
import re
from urllib.request import Request, urlopen

LINK = re.compile(r"!?\[([^]]*)\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)")


def extract(text):
    return [{"label": match.group(1), "url": match.group(2)} for match in LINK.finditer(text)]


def local_links(text):
    excluded = ("http://", "https://", "mailto:", "tel:")
    return [link for link in extract(text) if not link["url"].startswith(excluded) and not link["url"].startswith("#")]


def check(url, timeout=5):
    try:
        request = Request(url, headers={"User-Agent": "markdown-link-checker/1.0"})
        with urlopen(request, timeout=timeout) as response:
            return {"url": url, "ok": 200 <= response.status < 400, "status": response.status}
    except Exception as error:
        return {"url": url, "ok": False, "error": type(error).__name__}


def main():
    parser = argparse.ArgumentParser(description="Extract Markdown links and optionally check HTTP URLs")
    parser.add_argument("file")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    with open(args.file, encoding="utf-8") as source:
        links = extract(source.read())
    result = [check(link["url"]) for link in links if link["url"].startswith(("http://", "https://"))] if args.check else links
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
