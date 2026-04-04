import os
import re
from datetime import datetime

MARKDOWN_DIR = "markdown"
POSTS_FILE = "data/posts.js"

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def main():
    print("Scanning markdown directory...")
    if not os.path.exists(MARKDOWN_DIR):
        print("Markdown directory not found.")
        return

    posts = []
    
    # Read all markdown files
    for filename in os.listdir(MARKDOWN_DIR):
        if filename.endswith(".md"):
            filepath = os.path.join(MARKDOWN_DIR, filename)
            
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                
            # Naive parsing to extract title, date, and description
            lines = content.split("\n")
            title = filename.replace(".md", "").replace("-", " ").title()
            date = datetime.now().strftime("%B %d, %Y")
            desc = "A blog post by Phuc."
            
            # Simple heuristic mapping for typical markdown struct
            for line in lines:
                if line.startswith("# "):
                    title = line[2:].strip()
                elif line.startswith("*") and line.endswith("*"):
                    pot_date = line.replace("*", "").strip()
                    if len(pot_date) > 5:
                        date = pot_date
                elif line.startswith("**") and line.endswith("**"):
                    desc = line.replace("**", "").strip()
            
            slug = filename.replace(".md", "")
            
            posts.append({
                "title": title,
                "date": date,
                "description": desc,
                "slug": slug,
                # Try getting file creation time for sorting if needed
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