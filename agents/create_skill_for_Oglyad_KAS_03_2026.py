import os
import sys
import re
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.storage_tools import MinioStorage

def create_kas_skill():
    load_dotenv()
    load_dotenv(".env.local")
    
    target_slug = "Oglyad_KAS_03_2026"
    object_name = f"markdown/{target_slug}/{target_slug}.md"
    
    storage = MinioStorage()
    
    print(f"📂 Fetching document: {object_name}")
    content = storage.get_object_content(object_name)
    if not content:
        print(f"❌ No content found for {target_slug}")
        return

    # Categories to find
    category_markers = [
        r"1\.1\.\s",
        r"1\.2\.\s",
        r"[ІIVX]+\.\s*СПРАВИ",
        r"[ІIVX]+\.\s*ПРОЦЕСУАЛЬНІ\s+ПИТАННЯ"
    ]
    
    # Segments to find
    segment_patterns = [
        r"1\.1\.\d\.\s",
        r"1\.2\.\d\.\s",
        r"[234]\.\d\.\s"
    ]
    
    all_markers = []
    
    # Find Categories
    for m in category_markers:
        regex = re.compile(fr"^{m}(?!\s*\.\.)", re.MULTILINE)
        for match in regex.finditer(content):
            line_end = content.find("\n", match.start())
            cat_name = content[match.start():line_end].strip() if line_end != -1 else content[match.start():].strip()
            
            # If it's a Roman header, it might continue on the next line
            if re.match(r"^[ІIVX]+", cat_name):
                next_line_start = line_end + 1
                next_line_end = content.find("\n", next_line_start)
                if next_line_end != -1:
                    next_line = content[next_line_start:next_line_end].strip()
                    if next_line and not re.match(r"^\d", next_line) and not next_line.startswith("#"):
                        cat_name += " " + next_line
            
            all_markers.append({
                "type": "category",
                "pos": match.start(),
                "name": cat_name
            })
            
    # Find Segments
    for p in segment_patterns:
        regex = re.compile(fr"^{p}(?!\s*\.\.)", re.MULTILINE)
        for match in regex.finditer(content):
            all_markers.append({
                "type": "segment",
                "pos": match.start()
            })
            
    # Sort markers by position
    all_markers.sort(key=lambda x: x["pos"])
    
    # Filter out TOC: start after the first real 1.1 category header
    start_match = re.search(r"^1\.1\.\s+Оподаткування(?!\s*\.\.)", content, re.MULTILINE)
    threshold = start_match.start() if start_match else 4400
    all_markers = [m for m in all_markers if m["pos"] >= threshold] 
    
    segments = []
    current_category = "Загальна категорія"
    
    for i, marker in enumerate(all_markers):
        if marker["type"] == "category":
            current_category = marker["name"]
            continue
        
        if marker["type"] == "segment":
            start_pos = marker["pos"]
            # End is the next marker
            end_pos = all_markers[i+1]["pos"] if i + 1 < len(all_markers) else len(content)
            
            snippet_start = content[start_pos:start_pos+200].split("\n")[0].strip()
            if len(snippet_start) < 50:
                snippet_start = content[start_pos:start_pos+150].replace("\n", " ").strip()
            
            snippet_end = content[end_pos-150:end_pos].replace("\n", " ").strip()
            
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
    create_kas_skill()
