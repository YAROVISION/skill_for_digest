import os
import sys
import json
import time
import re
import ollama
from tools.storage_tools import MinioStorage
from tools.text_tools import TextProcessor
from agents.prompts import STRUCTURE_PROMPT, SEGMENT_PROMPT

class LegalSegmenterAgent:
    def __init__(self, model_name="qwen2.5-coder:14b"):
        self.storage = MinioStorage()
        self.processor = TextProcessor()
        self.model_name = model_name
        self.skip_files = ['1775151844836_fiche_thematique_comunity_designs', '1775151838405_Oglyad_SES_05_2024']
        
        # Verify AI key exists (used in original script, though ollama doesn't strictly need it if local)
        if not os.getenv('MY_PRIVATE_AI_KEY'):
            print("⚠️ Warning: MY_PRIVATE_AI_KEY missing in .env")

    def run(self, target_file=None):
        print(f"--- 🤖 Legal Article Segmenter Agent ({self.model_name}) ---")
        
        # 1. Get Markdown files from MinIO
        md_files = self.storage.list_markdown_files()
        if target_file:
            md_files = [f for f in md_files if target_file in f.object_name]
        print(f"✅ Found {len(md_files)} Markdown files in storage.")

        # 2. Get processed docs
        processed_slugs = self.storage.get_processed_slugs()

        for i, obj in enumerate(md_files):
            doc_slug = os.path.basename(obj.object_name).split('.')[0]
            
            if doc_slug in self.skip_files:
                print(f"\n[Doc {i+1}/{len(md_files)}] ⏭️ Skipping {doc_slug} (restricted).")
                continue

            print(f"\n[Doc {i+1}/{len(md_files)}] Processing: {obj.object_name} ({obj.size/1024:.1f} KB)")
            
            # Get existing IDs for this doc
            existing_ids = self.storage.get_existing_ids(doc_slug)
            
            # Fetch and clean content
            content = self.storage.get_object_content(obj.object_name)
            clean_text = self.processor.clean_noise(content)
            
            # Check for a specific skill for this document
            skill = self._parse_skill(doc_slug)
            if skill:
                print(f"  🎯 Using skill file '{skill['skill_file']}' for {doc_slug}")
                self._handle_skill_segmentation(doc_slug, clean_text, obj.object_name, skill['segments'], skill.get('guidance', ""))
                continue

            # Special cases: Hardcoded Manual overrides
            if doc_slug == '1775151833044_Oglyad_SES_06_2024':
                self._handle_manual_override_06_2024(doc_slug, clean_text, obj.object_name)
                continue
            elif doc_slug == '1775151780288_Oglyad_ESPL_09_2024':
                self._handle_manual_override_09_2024(doc_slug, clean_text, obj.object_name)
                continue
            elif doc_slug == '1775151779171_Oglyad_SES_4_5_2025':
                self._handle_manual_override_4_5_2025(doc_slug, clean_text, obj.object_name)
                continue

            # Standard processing
            sections = self.processor.segment_by_sections(clean_text)
            print(f"  -> Found {len(sections)} document sections.")

            for s_idx, sec in enumerate(sections):
                category = sec["category"]
                
                # Check if already processed (simplified check)
                first_article_id = f"{doc_slug}_s{s_idx+1}_a1.json"
                if first_article_id in existing_ids:
                    print(f"    -> Section {s_idx+1} '{category}': Already partially/fully processed.")
                
                # Semantic segmentation via AI
                articles = self._segment_with_ai(sec["content"], category)
                
                if not articles:
                    continue
                    
                print(f"    -> Section {s_idx+1} '{category}': Found {len(articles)} semantically distinct articles.")

                for a_idx, article_raw in enumerate(articles):
                    article_id = f"{doc_slug}_s{s_idx+1}_a{a_idx+1}"
                    
                    if f"{article_id}.json" in existing_ids:
                        continue

                    # Structure individual article
                    structured_data = self._structure_article(article_raw, category, obj.object_name)
                    
                    if structured_data:
                        self.storage.save_structured_json(doc_slug, article_id, structured_data)
                        print(f"      ✅ Saved {article_id}")

    def _parse_skill(self, target_slug):
        """
        Scans agents/ directory and agents/skills_for_markdownfiles/ for skill_*.md files 
        and returns the matching one for the given target_slug.
        """
        agents_dir = os.path.dirname(__file__)
        skills_subdir = os.path.join(agents_dir, "skills_for_markdownfiles")
        
        # Collect skill files from both root and subdirectory
        skill_candidates = []
        
        # Root directory
        if os.path.exists(agents_dir):
            for f in os.listdir(agents_dir):
                if f.startswith("skill") and f.endswith(".md"):
                    skill_candidates.append((agents_dir, f))
                    
        # Subdirectory
        if os.path.exists(skills_subdir):
            for f in os.listdir(skills_subdir):
                if f.startswith("skill") and f.endswith(".md"):
                    skill_candidates.append((skills_subdir, f))
        
        for s_dir, sf in skill_candidates:
            skill_path = os.path.join(s_dir, sf)
            try:
                with open(skill_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse target file
                target_match = re.search(r'\*\*Target File\*\*:\s*([^\s\n]+)', content)
                if not target_match:
                    continue
                
                skill_target = target_match.group(1).strip()
                
                # Match if skill_target is exactly target_slug or part of it
                if skill_target == target_slug or skill_target in target_slug or target_slug in skill_target:
                    # Found matching skill file!
                    # Parse Guidance
                    guidance_match = re.search(r'## Prompts Guidance\n(.*?)(?=\n## |$)', content, re.DOTALL)
                    guidance = guidance_match.group(1).strip() if guidance_match else ""

                    # Parse segments
                    segments = []
                    segment_blocks = re.findall(r'### \[(.*?)\]\n(.*?)(?=\n### |$)', content, re.DOTALL)
                    
                    for segment_id, block in segment_blocks:
                        category_match = re.search(r'- \*\*Category\*\*:\s*(.*)', block)
                        start_match = re.search(r'- \*\*Start\*\*:\s*(.*)', block)
                        end_match = re.search(r'- \*\*End\*\*:\s*(.*)', block)
                        
                        if category_match and start_match and end_match:
                            segments.append({
                                "id": segment_id.strip(),
                                "category": category_match.group(1).strip(),
                                "start": start_match.group(1).strip(),
                                "end": end_match.group(1).strip()
                            })
                    
                    return {
                        "target": skill_target,
                        "guidance": guidance,
                        "segments": segments,
                        "skill_file": sf
                    }
            except Exception as e:
                print(f"      ⚠️ Error reading skill file {sf}: {e}")
                
        return None

    def _handle_skill_segmentation(self, doc_slug, clean_text, source_name, segments, guidance=""):
        print(f"  🎯 Using skill.md for {doc_slug}")
        existing_ids = self.storage.get_existing_ids(doc_slug)
        
        for seg in segments:
            article_id = seg["id"]
            if f"{article_id}.json" in existing_ids:
                print(f"    ⏭️ Skipping {article_id} (already exists).")
                continue
            
            # Find start and end using fuzzy regex to handle newlines, extra spaces, and minor punctuation differences
            def make_fuzzy_pattern(text):
                # 1. Escape literal characters
                p = re.escape(text)
                # 2. Replace escaped spaces with \s+ (one or more whitespace)
                p = p.replace(r'\ ', r'\s+')
                # 3. Handle punctuation: allow optional whitespace before punctuation
                # This fixes issues like "норм ." vs "норм."
                # We use \\s* to insert a literal \s* into the resulting pattern
                p = re.sub(r'(\\([.,!?;:]))', r'\\s*\1', p)
                return p

            start_pattern = make_fuzzy_pattern(seg["start"])
            start_matches = list(re.finditer(start_pattern, clean_text, re.MULTILINE))
            
            if not start_matches:
                # Try an even fuzzier match: just the beginning of the header (first 50 chars)
                # but we will only use this to find the position, not as the final match
                short_start = seg["start"][:50]
                start_pattern = make_fuzzy_pattern(short_start)
                start_matches = list(re.finditer(start_pattern, clean_text, re.MULTILINE))
                
            if not start_matches:
                print(f"    ❌ Could not find start: {seg['start']}")
                continue
                
            # If multiple matches, take the last one (usually actual content follows TOC)
            start_match = start_matches[-1]
            
            # Find end match AFTER start using fuzzy regex
            remaining_text = clean_text[start_match.end():]
            end_pattern = make_fuzzy_pattern(seg["end"])
            end_match = re.search(end_pattern, remaining_text, re.MULTILINE)
            
            if not end_match:
                # Try fuzzy for end as well (first 50 chars)
                short_end = seg["end"][:50]
                end_pattern = make_fuzzy_pattern(short_end)
                # If we use the short version, we might truncate early, 
                # so we warn and take a bit more context if possible
                end_match = re.search(end_pattern, remaining_text, re.MULTILINE)
                if end_match:
                    print(f"    ⚠️ Used fuzzy match for end marker of {article_id}. Check for truncation.")

            if end_match:
                end_pos = start_match.end() + end_match.end() # Use end() to include the end marker itself in the segment
                article_raw = clean_text[start_match.start():end_pos].strip()
            else:
                print(f"    ⚠️ Could not find end marker '{seg['end']}' after start. Taking till end of doc.")
                article_raw = clean_text[start_match.start():].strip()

            print(f"    -> Processing {article_id} ({seg['category']})...")
            structured_data = self._structure_article(article_raw, seg["category"], source_name, guidance)
            if structured_data:
                self.storage.save_structured_json(doc_slug, article_id, structured_data)
                print(f"      ✅ Saved {article_id}")

    def _segment_with_ai(self, text, category):
        if not text.strip() or len(text.strip()) < 100:
            return []
            
        ai_text = text
        if len(text) > 45000:
            print(f"      ⚠️ Section '{category}' too large. Truncating for AI.")
            ai_text = text[:40000] + "\n\n...[TRUNCATED]..."
            
        prompt = SEGMENT_PROMPT.format(text=ai_text)
        
        for attempt in range(5):
            try:
                response = ollama.chat(
                    model=self.model_name,
                    messages=[{'role': 'user', 'content': prompt}],
                    format='json'
                )
                res_text = response['message']['content'].strip()
                articles = json.loads(res_text)
                if isinstance(articles, list):
                    return articles
                return [text] if len(text.strip()) > 300 else []
            except Exception as e:
                print(f"      ❌ AI Segment error: {str(e)}. Retrying...")
                time.sleep(5)
        return [text]

    def _structure_article(self, article_raw, category, source_name, guidance=""):
        prompt_instructions = STRUCTURE_PROMPT
        if guidance:
            # Inject guidance into instructions section of the prompt
            # STRUCTURE_PROMPT has a "### Instructions:" section
            guidance_text = f"\n\n### ADDITIONAL SKILL INSTRUCTIONS:\n{guidance}"
            prompt_instructions = STRUCTURE_PROMPT.replace("### Instructions:", f"### Instructions:{guidance_text}")

        prompt = prompt_instructions.format(text=article_raw, category=category, source=source_name)
        
        for attempt in range(5):
            try:
                response = ollama.chat(
                    model=self.model_name,
                    messages=[{'role': 'user', 'content': prompt}],
                    format='json'
                )
                res_text = response['message']['content'].strip()
                structured_data = json.loads(res_text)
                
                if not structured_data.get("teza") and not structured_data.get("case_number"):
                    return None # Likely not a legal article
                
                # ALWAYS set full_markdown from the original raw text to avoid AI truncation or placeholder issues
                structured_data["full_markdown"] = article_raw
                    
                return structured_data
            except Exception as e:
                print(f"      ❌ Structuring error: {str(e)}. Retrying...")
                time.sleep(5)
        return None

    def _handle_manual_override_06_2024(self, doc_slug, clean_text, source_name):
        print(f"  ⚡ Manual Override: Processing {doc_slug}")
        # Re-using the logic from original script for this specific document
        marker_positions = []
        # Updated markers with character classes for Cyrillic/Latin flexibility
        flexible_markers = [
            (r'[ІI]\.\s+', "Section I"),
            (r'[ІI]{2}\.\s+', "Section II"),
            (r'[ІI]{3}\.\s+', "Section III"),
            (r'1\.\s+Авторське право', "IV.1 Copyright"),
            (r'2\.\s+Публічні закупівлі', "IV.2 Procurement"),
            (r'[VѴ]\.\s+Соціальна політика', "Section V"),
            (r'[VѴ][ІI]\.\s+Навколишнє середовище', "Section VI"),
            (r'1\.\s+Європейська цивільна служба', "VII.1 Civil Service"),
            (r'2\.\s+Спільна зовнішня політика', "VII.2 Security Policy"),
            (r'VII[ІI]\.\s+', "END") # A marker for the end if needed, but VII is usually last
        ]
        
        for m_regex, m_label in flexible_markers:
            # Use ^ to ensure it's at the start of a line
            matches = list(re.finditer(r'^' + m_regex, clean_text, re.MULTILINE))
            if matches:
                # Debug: print all matches for this marker
                print(f"    DEBUG: Found {m_label} at positions: {[m.start() for m in matches]}")
                
                # Heuristic: The actual section is usually the first one AFTER the TOC (if TOC is present)
                # or just the first one if TOC is removed.
                # However, sometimes there is a summary at the end.
                # Let's take the first one that is NOT in the very beginning (if there are multiple)
                # or just the first one if we trust clean_noise.
                if len(matches) > 1 and matches[0].start() < 1000:
                    # Likely TOC entry
                    m = matches[1]
                else:
                    m = matches[0]
                
                marker_positions.append((m_label, m.start()))
        
        marker_positions.sort(key=lambda x: x[1])
        print(f"    DEBUG: Sorted markers: {[(m[0], m[1]) for m in marker_positions]}")
        
        for i in range(len(marker_positions)):
            m_name, start = marker_positions[i]
            if i + 1 < len(marker_positions):
                _, end = marker_positions[i+1]
            else:
                end = len(clean_text)
                
            article_raw = clean_text[start:end].strip()
            
            article_id = f"{doc_slug}_manual_v1_a{i+1}"
            
            # Special numbering for Section IV (Copyright and Procurement)
            if "IV.1" in m_name:
                article_id = f"{doc_slug}_manual_v1_a4-1"
            elif "IV.2" in m_name:
                article_id = f"{doc_slug}_manual_v1_a4-2"
            elif "VII.1" in m_name:
                article_id = f"{doc_slug}_manual_v1_a7-1"
            elif "VII.2" in m_name:
                article_id = f"{doc_slug}_manual_v1_a7-2"
            elif i >= 5:
                # Adjust numbering for subsequent sections if needed (V becomes a5, VI becomes a6)
                article_id = f"{doc_slug}_manual_v1_a{i}"
            
            # Check if already processed
            existing_ids = self.storage.get_existing_ids(doc_slug)
            if f"{article_id}.json" in existing_ids:
                print(f"    ⏭️ Skipping Manual Article {i+1} (already exists).")
                continue
                
            category = m_name.split('\\')[0].strip() # Clean name
            
            print(f"    -> Manual Article {i+1} ({m_name})...")
            structured_data = self._structure_article(article_raw, category, source_name)
            if structured_data:
                self.storage.save_structured_json(doc_slug, article_id, structured_data)
                print(f"      ✅ Saved {article_id}")
        
        print("🏁 Manual override processing complete.")

    def _handle_manual_override_09_2024(self, doc_slug, clean_text, source_name):
        print(f"  ⚡ Manual Override: Processing {doc_slug}")
        
        # Use more flexible markers to handle Markdown links and other variations
        start_marker = r'DE JESUS LOURENÇO JÓIA v\. Portugal.*4976/23'
        end_marker = r'РІШЕННЯ ЄСПЛ ПРОТИ УКРАЇНИ'
        
        start_match = re.search(start_marker, clean_text, re.IGNORECASE)
        
        if start_match:
            # Find the first occurrence of end_marker AFTER start_match
            end_match = re.search(end_marker, clean_text[start_match.end():], re.IGNORECASE)
            
            if end_match:
                # Adjust end index (add start_match.end() because we searched in a slice)
                end_pos = start_match.end() + end_match.start()
                article_raw = clean_text[start_match.start():end_pos].strip()
                
                article_id = f"{doc_slug}_manual_v13_a1"
                print(f"    -> Manual Article (DE JESUS to Decisions Against Ukraine). Length: {len(article_raw)} chars...")
            
            structured_data = self._structure_article(article_raw, "ESPL", source_name)
            if structured_data:
                # Force the ID or slug if needed, but save_structured_json handles it.
                structured_data["full_markdown"] = article_raw # DOUBLE ENSURE FULL TEXT
                self.storage.save_structured_json(doc_slug, article_id, structured_data)
                print(f"      ✅ Saved {article_id}")
                
                # Also save a copy with a simple name as requested "one json file"
                # The user might want a specific filename. I'll use a descriptive one.
                local_result_path = "result_1775151780288.json"
                with open(local_result_path, 'w', encoding='utf-8') as f:
                    json.dump(structured_data, f, ensure_ascii=False, indent=2)
                print(f"      ✅ Local result saved to {local_result_path}")
        else:
            if not start_match:
                print(f"    ❌ Could not find start marker: {start_marker}")
            if not end_match:
                print(f"    ❌ Could not find end marker: {end_marker}")

    def _handle_manual_override_4_5_2025(self, doc_slug, clean_text, source_name):
        print(f"  ⚡ Manual Override: Processing {doc_slug}")
        
        articles_to_process = [
            {
                "id": f"{doc_slug}_manual_v1_a1",
                "start": r'Рішення Суду справедливості ЄС \(Велика Палата\) від 3 квітня 2025 року,[\s\n]+Alchaster II,[\s\n]+C-743/24',
                "end": r'ІІ\. Захист персональних даних',
                "cat": "SES"
            },
            {
                "id": f"{doc_slug}_manual_v1_a2",
                "start": r'Постанова Загального Суду \(Десята Палата\) від 29 квітня 2025 року,[\s\n]+Meta Platforms[\s\n]+Ireland v European Data Protection Board,[\s\n]+T-319/24',
                "end": r'ІІІ\. Інституційні положення',
                "cat": "SES"
            },
            {
                "id": f"{doc_slug}_manual_v1_a3",
                "start": r'1\. Доступ до документів',
                "end": r'2\. Імунітети членів Європейського Парламенту',
                "cat": "SES"
            },
            {
                "id": f"{doc_slug}_manual_v1_a4",
                "start": r'2\. Імунітети членів Європейського Парламенту',
                "end": r'IV\. Провадження Європейського Союзу: позови про скасування',
                "cat": "SES"
            },
            {
                "id": f"{doc_slug}_manual_v1_a5",
                "start": r'IV\. Провадження Європейського Союзу: позови про скасування',
                "end": r'V\. Наближення законодавства: торговельна марка Європейського Союзу',
                "cat": "SES"
            },
            {
                "id": f"{doc_slug}_manual_v1_a6",
                "start": r'V\. Наближення законодавства: торговельна марка Європейського Союзу',
                "end": r'VI\. Судове співробітництво у кримінальних справах: Європейська прокуратура',
                "cat": "SES"
            },
            {
                "id": f"{doc_slug}_manual_v1_a7",
                "start": r'VI\. Судове співробітництво у кримінальних справах: Європейська прокуратура',
                "end": r'VII\. Судове співробітництво у цивільних справах: Регламент Брюссель Іа',
                "cat": "SES"
            },
            {
                "id": f"{doc_slug}_manual_v1_a8",
                "start": r'VII\. Судове співробітництво у цивільних справах: Регламент Брюссель Іа',
                "end": r'VIIІ\. Спільна зовнішня політика та політика безпеки: обмежувальні заходи',
                "cat": "SES"
            },
            {
                "id": f"{doc_slug}_manual_v1_a9",
                "start": r'VIIІ\. Спільна зовнішня політика та політика безпеки: обмежувальні заходи',
                "end": r'Огляд практики Суду справедливості Європейського Союзу\. Рішення за квітень – травень 2025 року\.',
                "cat": "SES"
            }
        ]
        
        existing_ids = self.storage.get_existing_ids(doc_slug)
        
        for art in articles_to_process:
            if f"{art['id']}.json" in existing_ids:
                print(f"    ⏭️ Skipping {art['id']} (already exists).")
                continue
                
            all_starts = list(re.finditer(art['start'], clean_text))
            all_ends = list(re.finditer(art['end'], clean_text))
            
            if not all_starts:
                print(f"    ❌ Could not find start marker: {art['start']}")
                continue
            if not all_ends:
                print(f"    ❌ Could not find end marker: {art['end']}")
                continue
                
            # Content match usually index 1 (0 is TOC)
            start_match = all_starts[1] if len(all_starts) > 1 else all_starts[0]
            
            end_match = None
            for m in all_ends:
                if m.start() > start_match.end():
                    end_match = m
                    break
                    
            if start_match and end_match:
                article_raw = clean_text[start_match.start():end_match.start()].strip()
                print(f"    -> Processing {art['id']}. Length: {len(article_raw)} chars...")
                
                structured_data = self._structure_article(article_raw, art['cat'], source_name)
                if structured_data:
                    structured_data["full_markdown"] = article_raw
                    self.storage.save_structured_json(doc_slug, art['id'], structured_data)
                    print(f"      ✅ Saved {art['id']}")
            else:
                print(f"    ❌ Could not find appropriate match pair for {art['id']}.")

if __name__ == "__main__":
    import sys
    target_file = sys.argv[1] if len(sys.argv) > 1 else None
    agent = LegalSegmenterAgent()
    agent.run(target_file)
