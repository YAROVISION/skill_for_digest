import os
import sys
import re
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.storage_tools import MinioStorage

def create_kgs_fond_skill():
    load_dotenv()
    load_dotenv(".env.local")
    
    target_slug = "Oglyad_KGS_fond_vidshkodyvannya"
    object_name = f"markdown/{target_slug}/{target_slug}.md"
    
    storage = MinioStorage()
    
    print(f"📂 Fetching document: {object_name}")
    content = storage.get_object_content(object_name)
    if not content:
        print(f"❌ No content found for {target_slug}")
        return

    # Skip Table of Contents
    threshold = 10000
    print(f"  🔍 Content body threshold set to {threshold}")

    category_patterns = [
        r"1\.\s+",
        r"2\.\s+",
        r"2\.1\.\s+",
        r"2\.2\.\s+",
        r"3\.\s+",
        r"4\.\s+",
        r"4\.1\.\s+",
        r"4\.2\.\s+",
        r"4\.3\.\s+",
        r"4\.4\.\s+",
    ]
    
    segment_patterns = [
        r"1\.\d+\.\s+",
        r"2\.1\.\d+\.\s+",
        r"2\.2\.\d+\.\s+",
        r"3\.\d+\.\s+",
        r"4\.1\.\d+\.\s+",
        r"4\.2\.\d+\.\s+",
        r"4\.3\.\d+\.\s+",
        r"4\.4\.\d+\.\s+",
        r"5\.\s+",
        r"6\.\s+",
        r"7\.\s+",
        r"8\.\s+",
        r"9\.\s+",
    ]
    
    all_markers = []
    
    # 1. Find Categories
    for p in category_patterns:
        regex = re.compile(fr"^{p}(?!\s*\.\.)", re.MULTILINE)
        for match in regex.finditer(content):
            if match.start() < threshold: continue
            line_end = content.find("\n", match.start())
            cat_name = content[match.start():line_end].strip() if line_end != -1 else content[match.start():].strip()
            all_markers.append({
                "type": "category",
                "pos": match.start(),
                "name": cat_name
            })
            
    # 2. Find Segments
    for p in segment_patterns:
        regex = re.compile(fr"^{p}(?!\s*\.\.)", re.MULTILINE)
        for match in regex.finditer(content):
            if match.start() < threshold: continue
            # Avoid duplicate matches with category patterns (e.g. 5.)
            if any(m["pos"] == match.start() for m in all_markers if m["type"] == "category"):
                # But wait, 5., 6., 7., 8., 9. are defined as categories AND segments. We want them to act as SEGMENTS!
                # So we remove the category marker if it's also a segment leaf.
                all_markers = [m for m in all_markers if m["pos"] != match.start()]
                
            all_markers.append({
                "type": "segment",
                "pos": match.start()
            })
            
    # Sort markers by position
    all_markers.sort(key=lambda x: x["pos"])
    
    segments = []
    current_category = "Загальна категорія"
    
    for i, marker in enumerate(all_markers):
        if marker["type"] == "category":
            current_category = marker["name"]
            continue
            
        if marker["type"] == "segment":
            start_pos = marker["pos"]
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
                start_idx = last_link.start()
                if start_idx > 0 and chunk[max(0, start_idx-10):start_idx].rfind('[') != -1:
                    bracket_offset = chunk[max(0, start_idx-10):start_idx].rfind('[')
                    start_idx = max(0, start_idx-10) + bracket_offset
                
                end_idx = last_link.end()
                if chunk[end_idx:end_idx+200].find(')') != -1:
                    paren_offset = chunk[end_idx:end_idx+200].find(')')
                    end_idx = end_idx + paren_offset + 1
                
                snippet_end = chunk[start_idx:end_idx].strip()
            else:
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

    print(f"✅ DONE Local: {skill_path}")
    
    try:
        minio_path = storage.upload_skill(skill_path, target_slug)
        print(f"✅ DONE MinIO: {minio_path}")
    except Exception as e:
        print(f"⚠️ MinIO Upload Failed: {e}")

if __name__ == "__main__":
    create_kgs_fond_skill()
