"""Extract and optionally validate links from a Markdown file."""

import argparse
import json
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

LINK = re.compile(r"!?\[([^]]*)\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)")


def extract(text):
    """Return every Markdown link or image as a label/url mapping."""
    return [{"label": match.group(1), "url": match.group(2)} for match in LINK.finditer(text)]


def local_links(text):
    """Return links that point to local files rather than web or special URLs."""
    excluded = ("http://", "https://", "mailto:", "tel:", "#")
    return [link for link in extract(text) if not link["url"].lower().startswith(excluded)]


def check_local(url, base_dir):
    """Report whether a local Markdown link resolves from the source file's directory."""
    path_part = url.split("#", 1)[0].split("?", 1)[0]
    if not path_part:
        return {"url": url, "ok": True}

    path = Path(base_dir, path_part)
    return {"url": url, "ok": path.exists()}


def check(url, timeout=5):
    """Make an HTTP request and report whether the response looks successful."""
    try:
        request = Request(url, headers={"User-Agent": "markdown-link-checker/1.0"})
        with urlopen(request, timeout=timeout) as response:
            return {"url": url, "ok": 200 <= response.status < 400, "status": response.status}
    except HTTPError as error:
        return {"url": url, "ok": False, "status": error.code}
    except URLError as error:
        return {"url": url, "ok": False, "error": type(error).__name__, "reason": str(error.reason)}
    except Exception as error:
        return {"url": url, "ok": False, "error": type(error).__name__}


def main():
    parser = argparse.ArgumentParser(description="Extract Markdown links and optionally check HTTP or local links")
    parser.add_argument("file", help="Markdown file to scan")
    parser.add_argument("--check", action="store_true", help="also check HTTP(S) links")
    parser.add_argument("--check-local", action="store_true", help="also check links to local files")
    parser.add_argument("--timeout", type=float, default=5, help="HTTP timeout in seconds (default: 5)")
    args = parser.parse_args()

    source_path = Path(args.file)
    with source_path.open(encoding="utf-8") as source:
        links = extract(source.read())

    if args.check:
        urls = dict.fromkeys(
            link["url"] for link in links
            if link["url"].lower().startswith(("http://", "https://"))
        )
        result = [check(url, timeout=args.timeout) for url in urls]
    elif args.check_local:
        urls = dict.fromkeys(link["url"] for link in local_links("\n".join(
            f"[{link['label']}]({link['url']})" for link in links
        )))
        result = [check_local(url, source_path.parent) for url in urls]
    else:
        result = links

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
