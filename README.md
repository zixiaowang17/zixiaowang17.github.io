# Personal website

The site serves static HTML. The blog uses the homepage's existing styles and navigation.

## Edit the blog

Edit [blog/aos-2024/post.md](blog/aos-2024/post.md).
This is the source for the blog on the personal website.

Run from this repository with Python 3 and Pandoc installed:

```sh
python3 scripts/build_blog.py --serve
```

Open http://127.0.0.1:8768/blog/aos-2024/. Save the Markdown and refresh the
page to see changes. The preview also includes the homepage's new Blog navigation and entry.

To rebuild HTML without starting a server:

```sh
python3 scripts/build_blog.py
```

Commit the Markdown and rebuilt HTML together. Pushing to `main` deploys `index.html`,
`assets/`, `blog/` and `statistical-paper-census/` to GitHub Pages.
