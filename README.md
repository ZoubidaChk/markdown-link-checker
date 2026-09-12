# Markdown Link Checker

A dependency-free Python utility that extracts links and images from Markdown files and optionally checks HTTP(S) links for reachability. Results are emitted as readable JSON, making the tool useful in local scripts and CI jobs.

## Features

- Extract Markdown links and images, including optional titles
- Separate local file references from web links, email addresses, telephone links, and anchors
- Check HTTP(S) URLs with status-aware error reporting
- Configure network timeouts and avoid checking duplicate URLs
- Run with only Python’s standard library

## Requirements

- Python 3.8 or newer

## Usage

List every link and image found in a Markdown file:

```bash
python markdown_link_checker.py README.md
```

Check each unique HTTP(S) URL and return JSON status results:

```bash
python markdown_link_checker.py README.md --check
```

Set a custom network timeout in seconds:

```bash
python markdown_link_checker.py README.md --check --timeout 10
```

Example output:

```json
[
  {
    "url": "https://example.com",
    "ok": true,
    "status": 200
  }
]
```

## Development

The project uses Python’s built-in `unittest` framework, so no package installation is required. Run the test suite from the repository root:

```bash
python -m unittest discover -s tests -v
```

The tests cover Markdown extraction, local-link filtering, successful and failed HTTP checks, timeout forwarding, and duplicate URL handling.

## License

This project is provided as-is for personal and educational use.
