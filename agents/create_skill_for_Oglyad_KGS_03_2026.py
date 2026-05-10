import os
import sys
import re
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.storage_tools import MinioStorage

def create_kgs_skill():
    load_dotenv()
    load_dotenv(".env.local")
    
    target_slug = "Oglyad_KGS_03_2026"
    object_name = f"markdown/{target_slug}/{target_slug}.md"
    
    storage = MinioStorage()
    
    print(f"📂 Fetching document: {object_name}")
    content = storage.get_object_content(object_name)
    if not content:
        print(f"❌ No content found for {target_slug}")
        return

    # Find where content starts (skip TOC)
    # The first category in content is around 3400
    threshold = 3000
    print(f"  🔍 Content starts at position {threshold}")

    all_markers = []
    
    # Categories: "1. ", "2. ", etc. (at start of line, followed by capital letter, no dots)
    cat_regex = re.compile(r"^\d+\.\s+[А-ЯІ].*(?!\s*\.\.)", re.MULTILINE)
    for match in cat_regex.finditer(content):
        if match.start() < threshold: continue
        line_end = content.find("\n", match.start())
        cat_name = content[match.start():line_end].strip()
        all_markers.append({
            "type": "category",
            "pos": match.start(),
            "name": cat_name
        })
        
    # Segments: "1.1.", "2.1.", etc.
    seg_regex = re.compile(r"^\d+\.\d+\s*\.?\s+.*(?!\s*\.\.)", re.MULTILINE)
    for match in seg_regex.finditer(content):
        if match.start() < threshold: continue
        # Verify it's not a category (already matched)
        if any(m["pos"] == match.start() for m in all_markers if m["type"] == "category"):
            continue
        all_markers.append({
            "type": "segment",
            "pos": match.start()
        })
        
    all_markers.sort(key=lambda x: x["pos"])
    
    segments = []
    current_category = "Загальна категорія"
    
    for i, marker in enumerate(all_markers):
        if marker["type"] == "category":
            current_category = marker["name"]
            continue
            
        if marker["type"] == "segment":
            start_pos = marker["pos"]
            # Find the end position: next marker OR end of document
            end_pos = all_markers[i+1]["pos"] if i + 1 < len(all_markers) else len(content)
            
            chunk = content[start_pos:end_pos]
            
            # Start snippet: first line
            snippet_start = chunk.split("\n")[0].strip()
            if len(snippet_start) < 50:
                snippet_start = chunk[:150].replace("\n", " ").strip()
            
            # End snippet: look for the last registry link in the chunk
            links = list(re.finditer(r'(?:https?://reyestr.court.gov.ua/Review/\d+|\[https?://reyestr.court.gov.ua/Review/\d+\]\(https?://reyestr.court.gov.ua/Review/\d+\))', chunk))
            if links:
                last_link = links[-1]
                snippet_end = chunk[last_link.start():last_link.end()].strip()
            else:
                # Fallback: last 150 chars of the chunk
                snippet_end = chunk[-150:].replace("\n", " ").strip()
                
            segments.append({
                "category": current_category,
                "start": snippet_start,
                "end": snippet_end
            })

    # Write skill file
    skill_dir = "agents/skills_for_markdownfiles"
    os.makedirs(skill_dir, exist_ok=True)
    skill_path = f"{skill_dir}/skill_for_{target_slug}.md"
    print(f"✍️ Writing {len(segments)} segments to {skill_path}")
    
    with open(skill_path, "w", encoding="utf-8") as f:
        f.write(f"# Skill: Manual Document Segmentation\n\n")
        f.write(f"**Target File**: {target_slug}\n\n")
        f.write(f"## Prompts Guidance\n")
        f.write(f"- Спеціально розроблена навичка для {target_slug}.\n")
        f.write(f"- Витягуй повний текст кожної справи.\n\n")
        f.write(f"## Segments\n\n")
        
        for i, seg in enumerate(segments):
            f.write(f"### [manual_a{i+1}]\n")
            f.write(f"- **Category**: {seg['category']}\n")
            f.write(f"- **Rule**: Один сегмент = Одна справа = Один JSON\n")
            f.write(f"- **Start**: {seg['start']}\n")
            f.write(f"- **End**: {seg['end']}\n\n")

    print(f"✅ DONE: {skill_path}")

if __name__ == "__main__":
    create_kgs_skill()
