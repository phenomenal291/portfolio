#!/usr/bin/env python3
"""
manage.py - Terminal CLI Manager for Phuc's Portfolio, Blog, and Reading Log.
Author: Duong Tan Phuc
"""

import os
import sys
import re
import shutil
import subprocess
from datetime import datetime

try:
    import yaml
except ImportError:
    yaml = None

POSTS_DIR = "_posts"
BOOKS_FILE = "_data/books.yml"
SITE_DIR = "_site"

def clear_screen():
    os.system("clear" if os.name != "nt" else "cls")

def get_editor():
    return os.environ.get("EDITOR", "nvim" if shutil.which("nvim") else ("vim" if shutil.which("vim") else "nano"))

def slugify(title):
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug

def parse_post_full(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    meta = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            raw_meta = parts[1]
            body = parts[2]
            for line in raw_meta.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip().lower()] = v.strip().strip('"').strip("'")
    return meta, body

def parse_post(filepath):
    meta, _ = parse_post_full(filepath)
    return meta

def extract_title_and_description(body):
    """Extract first heading as title, and first non-empty paragraph as description."""
    title = ""
    lines = body.strip().splitlines()
    for line in lines:
        cleaned = line.strip()
        if cleaned.startswith("#"):
            title = cleaned.lstrip("#").strip()
            break

    # Extract first non-heading paragraph
    paragraphs = re.split(r"\n\s*\n", body.strip())
    desc = ""
    for p in paragraphs:
        cleaned_p = p.strip()
        if cleaned_p and not cleaned_p.startswith("#"):
            plain = re.sub(r"[*_`#\[\]]", "", cleaned_p).strip()
            desc = plain[:140] + ("..." if len(plain) > 140 else "")
            break

    return title, desc

def get_all_posts():
    if not os.path.exists(POSTS_DIR):
        return []
    posts = []
    for f in sorted(os.listdir(POSTS_DIR), reverse=True):
        if f.endswith(".md"):
            fp = os.path.join(POSTS_DIR, f)
            meta, body = parse_post_full(fp)
            ext_title, ext_desc = extract_title_and_description(body)

            date_match = re.match(r"^(\d{4}-\d{2}-\d{2})", f)
            date = meta.get("date") or (date_match.group(1) if date_match else "Undated")
            title = meta.get("title") or ext_title or f.replace(".md", "").replace("-", " ").title()
            desc = meta.get("description") or ext_desc

            posts.append({
                "filename": f,
                "filepath": fp,
                "title": title,
                "date": str(date),
                "description": desc
            })
    return posts

def load_books():
    if not os.path.exists(BOOKS_FILE):
        return []
    if yaml:
        with open(BOOKS_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, list) else []
    else:
        print("[!] PyYAML not found. Please install with: pip install pyyaml")
        return []

def save_books(books):
    os.makedirs(os.path.dirname(BOOKS_FILE), exist_ok=True)
    if yaml:
        with open(BOOKS_FILE, "w", encoding="utf-8") as f:
            yaml.dump(books, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    else:
        print("[!] Cannot save: PyYAML not installed.")

# ----------------- BUILD & PREVIEW -----------------

def build_site():
    print("[*] Building site into _site/ ...")
    if os.path.exists("build.rb") and shutil.which("ruby"):
        res = subprocess.run(["ruby", "build.rb"])
        if res.returncode == 0:
            return True
        else:
            print("[!] ruby build.rb failed, check output above.")
            return False
    else:
        print("[!] ruby is required to run build.rb locally.")
        return False

def preview_site(port=8080):
    build_site()
    serve_dir = SITE_DIR if os.path.exists(SITE_DIR) else "."
    print(f"\n[i] Serving from '{serve_dir}' at http://localhost:{port} ...")
    print("[i] Press Ctrl+C to stop.\n")
    try:
        subprocess.run([sys.executable, "-m", "http.server", str(port), "--directory", serve_dir])
    except KeyboardInterrupt:
        print("\n[i] Preview server stopped.")

# ----------------- POST FINALIZATION -----------------

def finalize_post(filepath):
    if not os.path.exists(filepath):
        return

    meta, body = parse_post_full(filepath)
    ext_title, ext_desc = extract_title_and_description(body)

    current_title = meta.get("title", "").strip()
    current_desc = meta.get("description", "").strip()

    # 1. Determine title
    if not current_title:
        default_title = ext_title if ext_title else ""
        if default_title:
            print(f"\n[i] Detected title from markdown: \"{default_title}\"")
            user_title = input(f"Press Enter to use this title, or type a new one: ").strip()
            current_title = user_title if user_title else default_title
        else:
            user_title = input("\nEnter post title: ").strip()
            current_title = user_title if user_title else "Untitled Post"

    # 2. Determine description
    if not current_desc:
        default_desc = ext_desc if ext_desc else ""
        if default_desc:
            print(f"[i] Auto excerpt: \"{default_desc}\"")
            user_desc = input("Press Enter to use this description, or type custom: ").strip()
            current_desc = user_desc if user_desc else default_desc
        else:
            user_desc = input("Short description (optional): ").strip()
            current_desc = user_desc

    # 3. Clean duplicate leading # Title heading from body if it matches
    cleaned_body = body
    if cleaned_body.strip().startswith("#"):
        first_line = cleaned_body.strip().splitlines()[0]
        heading_text = first_line.lstrip("#").strip()
        if heading_text.lower() == current_title.lower():
            lines = cleaned_body.strip().splitlines()
            cleaned_body = "\n".join(lines[1:]).strip() + "\n"

    # 4. Write back file with updated front-matter
    today_match = re.search(r"\d{4}-\d{2}-\d{2}", os.path.basename(filepath))
    date_val = meta.get("date") or (today_match.group(0) if today_match else datetime.now().strftime("%Y-%m-%d"))

    new_content = [
        "---",
        f'title: "{current_title}"',
        f'date: {date_val}'
    ]
    if current_desc:
        new_content.append(f'description: "{current_desc}"')
    if meta.get("tags"):
        new_content.append(f'tags: [{meta["tags"]}]')
    new_content.append("---\n")
    new_content.append(cleaned_body.strip() + "\n")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(new_content))

    # 5. Rename file if it was a draft or if slug changed
    new_slug = slugify(current_title)
    if new_slug:
        expected_filename = f"{date_val}-{new_slug}.md"
        current_filename = os.path.basename(filepath)
        if current_filename != expected_filename:
            new_filepath = os.path.join(POSTS_DIR, expected_filename)
            if not os.path.exists(new_filepath):
                os.rename(filepath, new_filepath)
                print(f"[✓] Renamed file to: {expected_filename}")
                filepath = new_filepath

    print(f"[✓] Finalized post: '{current_title}'")
    build_site()
    return filepath

# ----------------- BLOG SUBMENU -----------------

def cli_list_posts():
    posts = get_all_posts()
    print("\n=== BLOG POSTS ===")
    if not posts:
        print("No posts found in _posts/.\n")
        return posts
    for idx, p in enumerate(posts, 1):
        print(f"  [{idx}] {p['date']}  {p['title']}")
        if p['description']:
            print(f"      {p['description'][:75]}...")
    print()
    return posts

def cli_create_post(title=None):
    print("\n--- NEW BLOG POST ---")
    today = datetime.now().strftime("%Y-%m-%d")

    if title:
        post_title = title
        slug = slugify(title)
        filename = f"{today}-{slug}.md"
    else:
        # User can write first and name later!
        name_input = input("Working title or slug (press Enter to write first): ").strip()
        if name_input:
            post_title = name_input
            slug = slugify(name_input)
            filename = f"{today}-{slug}.md"
        else:
            post_title = ""
            slug = f"draft-{datetime.now().strftime('%H%M%S')}"
            filename = f"{today}-{slug}.md"

    filepath = os.path.join(POSTS_DIR, filename)
    os.makedirs(POSTS_DIR, exist_ok=True)

    front_matter = [
        "---",
        f'title: "{post_title}"',
        f'date: {today}',
        'description: ""',
        "---\n\n"
    ]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(front_matter))

    print(f"[✓] Created {filepath}")
    print(f"[*] Opening {get_editor()}... Write your blog, then save & exit.\n")
    subprocess.run([get_editor(), filepath])

    # After editor closes, finalize title and description:
    finalize_post(filepath)

def cli_edit_post():
    posts = cli_list_posts()
    if not posts:
        return
    choice = input("Enter post number to edit (or 'c' to cancel): ").strip()
    if choice.lower() == 'c' or not choice.isdigit():
        return
    idx = int(choice) - 1
    if 0 <= idx < len(posts):
        filepath = posts[idx]['filepath']
        subprocess.run([get_editor(), filepath])
        update_meta = input("Review / update title & description? [y/N]: ").strip().lower()
        if update_meta == "y":
            finalize_post(filepath)
        else:
            build_site()
    else:
        print("Invalid choice.")

def cli_finalize_post():
    posts = cli_list_posts()
    if not posts:
        return
    choice = input("Enter post number to finalize/rename (or 'c' to cancel): ").strip()
    if choice.lower() == 'c' or not choice.isdigit():
        return
    idx = int(choice) - 1
    if 0 <= idx < len(posts):
        finalize_post(posts[idx]['filepath'])
    else:
        print("Invalid choice.")

def cli_delete_post():
    posts = cli_list_posts()
    if not posts:
        return
    choice = input("Enter post number to DELETE (or 'c' to cancel): ").strip()
    if choice.lower() == 'c' or not choice.isdigit():
        return
    idx = int(choice) - 1
    if 0 <= idx < len(posts):
        target = posts[idx]
        confirm = input(f"Are you sure you want to delete '{target['title']}'? [y/N]: ").strip().lower()
        if confirm == "y":
            os.remove(target['filepath'])
            print(f"[✓] Deleted {target['filename']}")
            build_site()
    else:
        print("Invalid choice.")

def blog_menu():
    while True:
        print("\n--- BLOG MANAGEMENT ---")
        print("  [1] List all posts")
        print("  [2] Create new post (write first, title later)")
        print("  [3] Edit post in editor")
        print("  [4] Finalize / rename post metadata")
        print("  [5] Delete post")
        print("  [b] Back to main menu")
        ch = input("Select an option: ").strip().lower()
        if ch == "1":
            cli_list_posts()
        elif ch == "2":
            cli_create_post()
        elif ch == "3":
            cli_edit_post()
        elif ch == "4":
            cli_finalize_post()
        elif ch == "5":
            cli_delete_post()
        elif ch in ("b", "q"):
            break

# ----------------- BOOKS SUBMENU -----------------

def cli_list_books():
    books = load_books()
    print("\n=== READING LOG ===")
    if not books:
        print("No books found in _data/books.yml.\n")
        return books

    reading = [b for b in books if b.get("status") == "Reading"]
    finished = [b for b in books if b.get("status") != "Reading"]

    if reading:
        print("\n[ Currently Reading ]")
        for b in reading:
            print(f"  * {b.get('title')} by {b.get('author')}")
            if b.get("notes"):
                print(f"    Notes: {b.get('notes')[:80]}...")

    if finished:
        print("\n[ Finished Books ]")
        for idx, b in enumerate(finished, 1):
            rating = f"[{b.get('rating')}]" if b.get('rating') else "[read]"
            print(f"  [{idx}] {b.get('title')} - {b.get('author')} {rating}")
            if b.get("notes"):
                print(f"      {b.get('notes')[:80]}...")
    print()
    return books

def cli_add_book():
    print("\n--- ADD BOOK ---")
    title = input("Title: ").strip()
    if not title:
        print("Title cannot be empty.")
        return
    author = input("Author: ").strip()
    genre = input("Genre (e.g. Mystery, Sci-Fi): ").strip()
    status_choice = input("Status [1: Read, 2: Reading] (default: 1): ").strip()
    status = "Reading" if status_choice == "2" else "Read"

    year = datetime.now().year
    if status == "Read":
        year_input = input(f"Year read (default: {year}): ").strip()
        if year_input.isdigit():
            year = int(year_input)

    rating = ""
    if status == "Read":
        rating = input("Rating (e.g. 5/5, 4.5/5, or leave blank): ").strip()

    notes = input("Your comments/impressions: ").strip()
    quote = input("Memorable quote (optional): ").strip()

    entry = {
        "title": title,
        "author": author,
        "genre": genre,
        "status": status,
        "year_read": year,
        "rating": rating if rating else ("Reading" if status == "Reading" else "5/5"),
        "notes": notes
    }
    if quote:
        entry["quote"] = quote

    books = load_books()
    books.insert(0, entry)
    save_books(books)
    print(f"\n[✓] Added '{title}' to reading log!")
    build_site()

def cli_edit_book():
    books = load_books()
    if not books:
        print("No books logged yet.")
        return
    print("\n--- SELECT BOOK TO EDIT ---")
    for idx, b in enumerate(books, 1):
        print(f"  [{idx}] {b.get('title')} ({b.get('status', 'Read')})")
    choice = input("Select number (or 'c' to cancel): ").strip()
    if choice.lower() == "c" or not choice.isdigit():
        return
    idx = int(choice) - 1
    if not (0 <= idx < len(books)):
        print("Invalid choice.")
        return

    book = books[idx]
    print(f"\nEditing: {book.get('title')}")
    new_status = input(f"Status [{book.get('status')}]: ").strip()
    if new_status:
        book['status'] = new_status

    new_rating = input(f"Rating [{book.get('rating', '')}]: ").strip()
    if new_rating:
        book['rating'] = new_rating

    new_notes = input(f"Notes (leave empty to keep current): ").strip()
    if new_notes:
        book['notes'] = new_notes

    save_books(books)
    print("[✓] Book updated successfully.")
    build_site()

def cli_delete_book():
    books = load_books()
    if not books:
        print("No books logged yet.")
        return
    print("\n--- SELECT BOOK TO DELETE ---")
    for idx, b in enumerate(books, 1):
        print(f"  [{idx}] {b.get('title')} - {b.get('author')}")
    choice = input("Select number (or 'c' to cancel): ").strip()
    if choice.lower() == "c" or not choice.isdigit():
        return
    idx = int(choice) - 1
    if not (0 <= idx < len(books)):
        print("Invalid choice.")
        return
    target = books[idx]
    confirm = input(f"Delete '{target.get('title')}'? [y/N]: ").strip().lower()
    if confirm == "y":
        books.pop(idx)
        save_books(books)
        print("[✓] Removed from reading log.")
        build_site()

def books_menu():
    while True:
        print("\n--- BOOKS MANAGEMENT ---")
        print("  [1] List all books")
        print("  [2] Add new book")
        print("  [3] Edit book entry")
        print("  [4] Delete book")
        print("  [b] Back to main menu")
        ch = input("Select an option: ").strip().lower()
        if ch == "1":
            cli_list_books()
        elif ch == "2":
            cli_add_book()
        elif ch == "3":
            cli_edit_book()
        elif ch == "4":
            cli_delete_book()
        elif ch in ("b", "q"):
            break

# ----------------- GIT HELPER -----------------

def git_quick_push():
    print("\n=== GIT STATUS ===")
    subprocess.run(["git", "status", "-s"])
    commit_msg = input("\nCommit message (default: 'docs: update content'): ").strip()
    if not commit_msg:
        commit_msg = "docs: update content"
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", commit_msg])
    push = input("Push to origin main? [Y/n]: ").strip().lower()
    if push in ("", "y", "yes"):
        subprocess.run(["git", "push"])
        print("[✓] Pushed to GitHub!")

# ----------------- MAIN ENTRYPOINT -----------------

def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ("post", "new-post"):
            title = sys.argv[2] if len(sys.argv) > 2 else None
            cli_create_post(title)
            return
        elif cmd in ("book", "add-book"):
            cli_add_book()
            return
        elif cmd in ("posts", "list-posts"):
            cli_list_posts()
            return
        elif cmd in ("books", "list-books"):
            cli_list_books()
            return
        elif cmd in ("finalize",):
            cli_finalize_post()
            return
        elif cmd in ("build",):
            build_site()
            return
        elif cmd in ("preview", "serve"):
            port = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 8080
            preview_site(port)
            return
        elif cmd == "push":
            git_quick_push()
            return
        elif cmd in ("--help", "-h"):
            print("Usage: python3 manage.py [command]")
            print("Commands:")
            print("  (no args)      Open interactive Terminal CLI")
            print("  post [title]   Create a new blog post (write first, title later)")
            print("  book           Log a new book to _data/books.yml")
            print("  finalize       Finalize / rename post metadata from markdown")
            print("  posts          List all blog posts")
            print("  books          List all books")
            print("  build          Build static site into _site/")
            print("  preview [port] Build & serve local preview server (default: 8080)")
            print("  push           Commit and push changes to GitHub")
            return

    # Interactive menu loop
    while True:
        print("\n" + "=" * 60)
        print("             PHUC'S SITE MANAGER (Terminal CLI)             ")
        print("=" * 60)
        print("  [1] Blog Posts: List, Create, Edit, Finalize, Delete")
        print("  [2] Books Log: List, Add, Edit, Delete")
        print("  [3] Build Site (_site/)")
        print("  [4] Preview Site Locally (http://localhost:8080)")
        print("  [5] Git Quick Push (Commit & Push changes)")
        print("  [q] Quit")
        print("=" * 60)
        choice = input("Select an option: ").strip().lower()
        if choice == "1":
            blog_menu()
        elif choice == "2":
            books_menu()
        elif choice == "3":
            build_site()
        elif choice == "4":
            preview_site()
        elif choice == "5":
            git_quick_push()
        elif choice in ("q", "quit", "exit"):
            print("Goodbye!\n")
            break

if __name__ == "__main__":
    main()
