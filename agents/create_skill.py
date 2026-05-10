import os
import sys
import json
import re
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.llm_rotator import LLMRotator
from tools.storage_tools import MinioStorage

def create_generic_skill(target_slug):
    load_dotenv()
    load_dotenv(".env.local")
    
    object_name = f"markdown/{target_slug}/{target_slug}.md"
    
    storage = MinioStorage()
    rotator = LLMRotator()
    
    print(f"📂 Fetching document: {object_name}")
    content = storage.get_object_content(object_name)
    if not content:
        print(f"❌ No content found for {target_slug}")
        return

    # Use chunks for large documents
    chunk_size = 40000
    overlap = 5000
    chunks = []
    if len(content) <= chunk_size:
        chunks = [content]
    else:
        for i in range(0, len(content), chunk_size - overlap):
            chunks.append(content[i:i + chunk_size])

    all_segments = []
    seen_starts = set()

    for idx, chunk in enumerate(chunks):
        if len(chunks) > 1:
            print(f"🧠 Analyzing Part {idx+1}/{len(chunks)}...")
        else:
            print(f"🧠 Analyzing document structure...")
        
        prompt = f"""
Analyze this legal document snippet and identify ALL individual case summaries or articles.
For each case, identify:
- category: Full section/category title or article number.
- start: Unique start text (first ~100 chars of the article header).
- end: Unique end text (last ~100 chars, usually includes a link or conclusion).

Snippet:
---
{chunk}
---

Return JSON: {{ "segments": [ {{ "category": "...", "start": "...", "end": "..." }}, ... ] }}
"""
        try:
            res_text = rotator.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(res_text)
            
            segments = []
            if isinstance(data, list):
                segments = data
            elif isinstance(data, dict):
                segments = data.get("segments", [])
            
            for seg in segments:
                if not isinstance(seg, dict) or "start" not in seg or "end" not in seg:
                    continue
                
                # Check for uniqueness and basic length
                start_val = seg["start"].strip()
                if len(start_val) < 10: continue
                
                # Use first 60 chars as a fuzzy key for deduplication
                start_key = start_val[:60].lower().strip()
                if start_key not in seen_starts:
                    all_segments.append(seg)
                    seen_starts.add(start_key)
                    
        except Exception as e:
            print(f"❌ Error in part {idx+1}: {e}")

    skill_path = f"agents/skills_for_markdownfiles/skill_for_{target_slug}.md"
    print(f"✍️ Writing {len(all_segments)} segments to {skill_path}")
    
    with open(skill_path, "w", encoding="utf-8") as f:
        f.write(f"# Skill: Manual Document Segmentation\n\n")
        f.write(f"**Target File**: {target_slug}\n\n")
        f.write(f"## Prompts Guidance\n")
        f.write(f"- Автоматично згенерована навичка для {target_slug}.\n")
        f.write(f"- Витягуй повний текст кожної справи.\n\n")
        f.write(f"## Segments\n\n")
        
        for i, seg in enumerate(all_segments):
            clean_start = seg['start'].replace('\n', ' ').strip()
            clean_end = seg['end'].replace('\n', ' ').strip()
            category = seg.get('category', 'Загальна категорія')
            f.write(f"### [manual_a{i+1}]\n")
            f.write(f"- **Category**: {category}\n")
            f.write(f"- **Rule**: Один сегмент = Одна справа = Один JSON\n")
            f.write(f"- **Start**: {clean_start}\n")
            f.write(f"- **End**: {clean_end}\n\n")

    print(f"✅ DONE Local: {skill_path}")
    
    try:
        minio_path = storage.upload_skill(skill_path, target_slug)
        print(f"✅ DONE MinIO: {minio_path}")
    except Exception as e:
        print(f"⚠️ MinIO Upload Failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 agents/create_skill.py <target_slug>")
    else:
        create_generic_skill(sys.argv[1])
