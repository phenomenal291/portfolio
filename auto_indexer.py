import os
import re
from datetime import datetime

POSTS_DIR = "_posts"
POSTS_FILE = "data/posts.js"

def parse_front_matter(content):
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, content

    metadata = {}
    body_start = 0
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            body_start = i + 1
            break

        if ":" not in lines[i]:
            continue

        key, value = lines[i].split(":", 1)
        metadata[key.strip().lower()] = value.strip().strip('"').strip("'")

    return metadata, "\n".join(lines[body_start:]).strip()


def parse_post_filename(filename):
    # Expected Jekyll format: YYYY-MM-DD-slug.md
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})-(.+)\.md$", filename)
    if not match:
        return None, filename.replace(".md", "")

    year, month, day, slug = match.groups()
    iso_date = f"{year}-{month}-{day}"
    return iso_date, slug


def title_from_slug(slug):
    return slug.replace("-", " ").replace("_", " ").title()

def main():
    print("Scanning _posts directory...")
    if not os.path.exists(POSTS_DIR):
        print("_posts directory not found.")
        return

    posts = []
    
    for filename in os.listdir(POSTS_DIR):
        if filename.endswith(".md"):
            filepath = os.path.join(POSTS_DIR, filename)
            
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()

            metadata, body = parse_front_matter(content)
            file_date, slug = parse_post_filename(filename)

            title = metadata.get("title") or title_from_slug(slug)
            date_raw = metadata.get("date") or file_date or datetime.now().strftime("%Y-%m-%d")
            try:
                date = datetime.fromisoformat(date_raw).strftime("%B %d, %Y")
            except ValueError:
                date = date_raw

            desc = metadata.get("description") or "A blog post by Phuc."
            if not metadata.get("description") and body:
                first_line = next((ln.strip() for ln in body.splitlines() if ln.strip()), "")
                if first_line:
                    desc = first_line.lstrip("# ").strip()[:160]
            
            posts.append({
                "title": title,
                "date": date,
                "description": desc,
                "slug": slug,
                "sort_key": os.path.getctime(filepath)
            })
            
    # Sort posts by newest (using file time as heuristic, or just alphabet)
    posts.sort(key=lambda x: x["sort_key"], reverse=True)
    
    # Write to posts.js
    print(f"Found {len(posts)} posts. Updating {POSTS_FILE}...")
    
    with open(POSTS_FILE, "w", encoding="utf-8") as f:
        f.write("const BLOG_POSTS = [\n")
        for p in posts:
            f.write("  {\n")
            f.write(f'    title: "{p["title"]}",\n')
            f.write(f'    description: "{p["description"]}",\n')
            f.write(f'    date: "{p["date"]}",\n')
            f.write(f'    slug: "{p["slug"]}"\n')
            f.write("  },\n")
        f.write("];\n")
        
    print("Done!")

if __name__ == "__main__":
    main()