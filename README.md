# Duong Tan Phuc - Portfolio & Blog

Minimalist, monospace personal portfolio, technical blog, and reading log.

## Stack & Architecture

- **Static Site Engine**: [Jekyll](https://jekyllrb.com/) natively hosted on GitHub Pages.
- **Design System**: Monospace typography stack, responsive centered container (`max-width: 720px`), zero decorative bloat, zero runtime framework dependencies.
- **Blog**: Markdown files stored in `_posts/` with YAML front-matter.
- **Reading Log**: Structured YAML library in `_data/books.yml` with native HTML5 `<details><summary>` click-to-expand reviews.

## Repository Structure

```
├── index.html               # Main portfolio landing page
├── blog.html                # Blog archive page
├── books.html               # Reading log with expandable notes
├── _posts/                  # Markdown blog posts (YYYY-MM-DD-title.md)
├── _data/
│   └── books.yml            # Structured reading list and reflections
├── _layouts/
│   └── post.html            # Article reading layout
├── project-pages/           # Dedicated project deep-dives
├── css/                     # Typography, layout, and utilities
├── js/                      # Minimal smooth scroll script
├── manage.py                # Terminal CLI management tool
└── build.rb                 # Local static builder (Liquid + Kramdown)
```

## Management CLI (`manage.py`)

A terminal CLI tool to manage content, preview locally, and deploy:

```bash
# Interactive menu:
./manage.py

# Quick commands:
./manage.py post             # Create a new blog post (write first, title later)
./manage.py book             # Add a new book to the reading log
./manage.py preview          # Build and start local preview server (http://localhost:8080)
./manage.py build            # Build static site into _site/
./manage.py push             # Quick git commit & push
```

## License

CC0 1.0 Universal.
