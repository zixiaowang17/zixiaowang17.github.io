#!/usr/bin/env python3
"""Render the editable blog Markdown inside the existing homepage layout."""

import argparse
import html
import re
import subprocess
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
POST = ROOT / "blog/statistical-paper-census"
ROUTE = "/blog/statistical-paper-census/"
LOCK = Lock()


def build():
    source = (POST / "post.md").read_text()
    match = re.search(r"^# (.+)$", source, re.MULTILINE)
    if not match:
        raise ValueError("Start post.md with a title: # Your title")
    title = html.escape(match.group(1))
    fragment = subprocess.run(
        ["pandoc", "--from=gfm", "--to=html5"],
        input=source, text=True, capture_output=True, check=True,
    ).stdout
    icon = (ROOT / "assets/github-icon.html").read_text()
    repo_link = '<a href="https://github.com/zixiaowang17/AoS-2024">'
    fragment = fragment.replace(repo_link, repo_link + icon)
    homepage = (ROOT / "index.html").read_text()
    updated = re.sub(
        r'(<a href="blog/statistical-paper-census/" class="pub-title">).*?(</a>)',
        lambda m: m.group(1) + title + m.group(2), homepage,
    )
    if updated != homepage:
        (ROOT / "index.html").write_text(updated)
        homepage = updated
    styles = re.search(r"<style>(.*?)</style>", homepage, re.DOTALL).group(1)
    header = re.search(r'<header class="site-header">.*?</header>', homepage, re.DOTALL).group(0)
    header = header.replace('href="#blog"', 'href="#blog" aria-current="location"')
    header = header.replace('href="#', 'href="../../index.html#')
    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Zixiao Jolene Wang</title>
<style>{styles}
html {{ scroll-padding-top:24px; }}
.post h1 {{ font-size:28px; line-height:1.3; margin-bottom:20px; }}
.post h2 {{ margin-top:26px; margin-bottom:12px; }}
.post article ul {{ list-style:disc; padding-left:22px; margin-bottom:20px; }}
.post article li {{ margin-bottom:10px; }}
.post article code {{ font-size:.9em; overflow-wrap:anywhere; }}
.post article img {{ display:block; width:100%; height:auto; border:1px solid var(--rule); }}
.dashboard-actions {{ display:flex; flex-wrap:wrap; align-items:center; gap:12px 18px; margin:18px 0 26px; }}
.dashboard-actions span {{ color:#555; font-size:15px; }}
.post a.dashboard-cta {{ display:inline-flex; align-items:center; justify-content:center; padding:12px 20px; border-radius:4px; background:#155da0; color:#fff; font-weight:600; line-height:1.5; text-align:center; text-decoration:none; }}
.post a.dashboard-cta:hover {{ background:#104b83; }}
.post a.dashboard-cta:focus-visible {{ outline:3px solid #155da0; outline-offset:4px; }}
@media(min-width:761px) {{
  .site-header {{ position:absolute; top:40px; bottom:auto; left:clamp(24px,4.4vw,76px); width:160px; overflow:visible; }}
  .site-header nav {{ margin-top:0; }}
  main.post {{ width:auto; max-width:none; margin-left:clamp(240px,22vw,376px); margin-right:clamp(24px,5.2vw,90px); padding:38px 0 42px; }}
}}
@media(max-width:760px) {{
  .site-header {{ position:static; }}
  main.post {{ width:auto; max-width:none; margin:0; padding:24px 24px 36px; }}
  .post h1 {{ font-size:26px; }}
  .dashboard-actions {{ align-items:stretch; flex-direction:column; gap:8px; }}
}}
@media(max-width:380px) {{ main.post {{ padding-left:20px; padding-right:20px; }} }}
</style>
</head>
<body>
<a class="skip-link" href="#post">Skip to content</a>
{header}
<main class="post" id="post">
<article>
{fragment}</article>
<footer><a href="../../index.html#blog">Back to blog</a><a href="#post">Back to top</a></footer>
</main>
</body>
</html>
'''
    output = POST / "index.html"
    if not output.exists() or output.read_text() != page:
        output.write_text(page)


class PreviewHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Rebuild only the blog, leaving the archived census files unchanged.
        path = urlsplit(self.path).path
        if path in {"/", "/index.html", ROUTE, ROUTE + "index.html"}:
            try:
                with LOCK:
                    build()
            except (ValueError, OSError, subprocess.CalledProcessError) as error:
                self.send_error(500, "Blog build failed; check post.md and the preview terminal.")
                print(f"Blog build failed: {error}", flush=True)
                return
        super().do_GET()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true", help="Rebuild on refresh and preview locally.")
    parser.add_argument("--port", type=int, default=8768)
    args = parser.parse_args()
    build()
    if args.serve:
        handler = partial(PreviewHandler, directory=str(ROOT))
        server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
        print(f"Preview: http://127.0.0.1:{args.port}{ROUTE}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
    else:
        print("Built blog/statistical-paper-census/index.html")


if __name__ == "__main__":
    main()
