""" markdown-link-checker
scans a markdown file for links (and images, which use the same label(url)
syntax with a leading "!") and optionally makes an http request to each http(s) link 
to see whether it's still alive """ 

import argparse
import json
import re
from urllib.error import HTTPError , URLError 
from urllib.request import Request, urlopen

LINK = re.compile(r"!?\[([^]]*)\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)")
#Breakdown of the pattern:
# !?         ---->          optional"!" for images
#\[([^]]*)\]                the [label] part; "[^]]*" means "any characters that aren't ']'"
#(?:\s+['\"][^'\"]*['\"])?    optional "title"
#\)                          the closing ")"

def extract(text):
    """"this will return every link/image in 'text' as {"label":.....,"url":...}"""
    return [{"label": match.group(1), "url": match.group(2)} for match in LINK.finditer(text)]


def local_links(text):
     """"this will return only the"local" links in 'text' ,i.e links that are 
     not HTTP(s), mailto,tel , or in-page anchors(#section)"""
    excluded = ("http://", "https://", "mailto:", "tel:")
    return [link for link in extract(text) if not link["url"].startswith(excluded) and not link["url"].startswith("#")]


def check(url, timeout=5):
    """make an HTTP request to 'url' and report whether it looks alive"""
    try:
        request = Request(url, headers={"User-Agent": "markdown-link-checker/1.0"})
        with urlopen(request, timeout=timeout) as response:
            return {"url": url, "ok": 200 <= response.status < 400, "status": response.status}
            
    except HTTPError as error:
           return {"url":url,"ok":False, "status": error.code}
        """the server responded but with a 4xx/5xx status (e.g 404 not found ,403 forbidden)
        this is the case the original code lost: 
        urlopen() raises HTTPError for these instead of returning them,
        and catching it separately here lets us keep the actual code."""

    except URLError as error : 
        #couldn't reach the server at all : DNS failure, connection refused,...etc
        return {"url":url,"ok": False, "error": type(error).__name__, "reason": str(error.reason)}
   
    except Exception as error:
        #catch-all for anything unexpected (bad URL scheme, ...etc)
        # one bad link CAN'T crash the whole run .
        return {"url": url, "ok": False, "error": type(error).__name__}


def main():
    parser = argparse.ArgumentParser(description="Extract Markdown links and optionally check HTTP URLs")
    parser.add_argument("file")
    parser.add_argument("--check", action="store_true", help="also send an HTTP request to each http(s) link")
    args = parser.parse_args()

    with open(args.file, encoding="utf-8") as source:
        links = extract(source.read())

    if args.check:
        #only http(s) links can be "checked"over the network; local file,paths, mailto: ,tel: ,and anchors are skipped here .
    result = [check(link["url"]) for link in links 
              if link["url"].startswith(("http://", "https://"))] 
   else: #no-check: just report every link/image found, of any kind.
    result = links
     
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
