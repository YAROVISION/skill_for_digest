import os
import sys
import json
import time
import re
import ollama
from agents.llm_rotator import LLMRotator
from tools.storage_tools import MinioStorage
from tools.text_tools import TextProcessor
from agents.prompts import STRUCTURE_PROMPT, SEGMENT_PROMPT

class LegalSegmenterAgent:
    def __init__(self, model_name="qwen2.5-coder:14b"):
        self.storage = MinioStorage()
        self.processor = TextProcessor()
        self.model_name = model_name
        self.rotator = LLMRotator()
        self.skip_files = ['1775151844836_fiche_thematique_comunity_designs', '1775151838405_Oglyad_SES_05_2024']
        self.list_structured_path = os.path.join(os.path.dirname(__file__), 'lists', 'list_of_structured.md')
        self.list_missing_path = os.path.join(os.path.dirname(__file__), 'lists', 'list_of_missing_structured.md')
        
        if not os.getenv('MY_PRIVATE_AI_KEY'):
            print("⚠️ Warning: MY_PRIVATE_AI_KEY missing in .env")

    def run(self, target_file=None):
        print(f"--- 🤖 Legal Article Segmenter Agent ({self.model_name}) ---")
        
        md_files = self.storage.list_markdown_files()
        if target_file:
            md_files = [f for f in md_files if target_file in f.object_name]
        print(f"✅ Found {len(md_files)} Markdown files in storage.")

        processed_slugs = self.storage.get_processed_slugs()
        
        # Update missing structured list (Queue)
        self._update_missing_queue(md_files, processed_slugs)

        for i, obj in enumerate(md_files):
            doc_slug = os.path.basename(obj.object_name).split('.')[0]
            
            if doc_slug in self.skip_files or doc_slug.lower().startswith('zved_oglyad'):
                continue

            print(f"\n[Doc {i+1}/{len(md_files)}] Processing: {obj.object_name} ({obj.size/1024:.1f} KB)")
            
            existing_ids = self.storage.get_existing_ids(doc_slug)
            content = self.storage.get_object_content(obj.object_name)
            clean_text = self.processor.clean_noise(content)
            
            skill = self._parse_skill(doc_slug)
            new_articles_count = 0
            
            if skill:
                print(f"  🎯 Using skill file '{skill['skill_file']}' for {doc_slug}")
                new_articles_count = self._handle_skill_segmentation(doc_slug, clean_text, obj.object_name, skill['segments'], skill.get('guidance', ""))
            else:
                # Special cases
                if doc_slug == '1775151833044_Oglyad_SES_06_2024':
                    self._handle_manual_override_06_2024(doc_slug, clean_text, obj.object_name)
                    new_articles_count = 1
                elif doc_slug == '1775151780288_Oglyad_ESPL_09_2024':
                    self._handle_manual_override_09_2024(doc_slug, clean_text, obj.object_name)
                    new_articles_count = 1
                elif doc_slug == '1775151779171_Oglyad_SES_4_5_2025':
                    self._handle_manual_override_4_5_2025(doc_slug, clean_text, obj.object_name)
                    new_articles_count = 1
                else:
                    sections = self.processor.segment_by_sections(clean_text)
                    for s_idx, sec in enumerate(sections):
                        category = sec["category"]
                        articles = self._segment_with_ai(sec["content"], category)
                        if not articles: continue
                        for a_idx, article_raw in enumerate(articles):
                            article_id = f"{doc_slug}_s{s_idx+1}_a{a_idx+1}"
                            if f"{article_id}.json" in existing_ids: continue
                            structured_data = self._structure_article(article_raw, category, obj.object_name)
                            if structured_data:
                                self.storage.save_structured_json(doc_slug, article_id, structured_data)
                                print(f"      ✅ Saved {article_id}")
                                new_articles_count += 1
            
            if new_articles_count > 0:
                self._update_structured_list(doc_slug)

    def _update_missing_queue(self, md_files, processed_slugs):
        """Update the list of markdown files that haven't been structured yet."""
        missing = []
        for obj in md_files:
            doc_slug = os.path.basename(obj.object_name).split('.')[0]
            if doc_slug not in processed_slugs and doc_slug not in self.skip_files and not doc_slug.lower().startswith('zved_oglyad'):
                missing.append(doc_slug)
        
        print(f"📋 Updating missing structured queue: {len(missing)} items.")
        with open(self.list_missing_path, 'w', encoding='utf-8') as f:
            f.write("# Queue: Markdown files missing structured JSON output\n\n")
            for slug in missing:
                f.write(f"- {slug}\n")
        
        try:
            self.storage.client.fput_object(
                self.storage.bucket_name,
                "lists/list_of_missing_structured.md",
                self.list_missing_path,
                content_type='text/markdown'
            )
            print("✅ Remote queue list updated.")
        except Exception as e:
            print(f"⚠️ Failed to update remote queue list: {e}")

    def _update_structured_list(self, doc_slug):
        exists = False
        if os.path.exists(self.list_structured_path):
            with open(self.list_structured_path, 'r', encoding='utf-8') as f:
                if f"- {doc_slug}" in f.read():
                    exists = True
        
        if not exists:
            with open(self.list_structured_path, 'a', encoding='utf-8') as f:
                f.write(f"- {doc_slug} (done)\n")
            
            try:
                self.storage.client.fput_object(
                    self.storage.bucket_name,
                    "lists/list_of_structured.md",
                    self.list_structured_path,
                    content_type='text/markdown'
                )
                print(f"✅ Updated remote success list.")
            except Exception as e:
                print(f"⚠️ Failed to update remote success list: {e}")

    def _parse_skill(self, target_slug):
        agents_dir = os.path.dirname(__file__)
        skills_subdir = os.path.join(agents_dir, "skills_for_markdownfiles")
        skill_candidates = []
        if os.path.exists(agents_dir):
            for f in os.listdir(agents_dir):
                if f.startswith("skill") and f.endswith(".md"):
                    skill_candidates.append((agents_dir, f))
        if os.path.exists(skills_subdir):
            for f in os.listdir(skills_subdir):
                if f.startswith("skill") and f.endswith(".md"):
                    skill_candidates.append((skills_subdir, f))
        
        for s_dir, sf in skill_candidates:
            skill_path = os.path.join(s_dir, sf)
            try:
                with open(skill_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                target_match = re.search(r'\*\*Target File\*\*:\s*([^\s\n]+)', content)
                if not target_match: continue
                skill_target = target_match.group(1).strip()
                if skill_target == target_slug or skill_target in target_slug or target_slug in skill_target:
                    guidance_match = re.search(r'## Prompts Guidance\n(.*?)(?=\n## |$)', content, re.DOTALL)
                    guidance = guidance_match.group(1).strip() if guidance_match else ""
                    segments = []
                    segment_blocks = re.findall(r'### \[(.*?)\]\n(.*?)(?=\n### |$)', content, re.DOTALL)
                    for segment_id, block in segment_blocks:
                        category_match = re.search(r'- \*\*Category\*\*:\s*(.*)', block)
                        start_match = re.search(r'- \*\*Start\*\*:\s*(.*)', block)
                        end_match = re.search(r'- \*\*End\*\*:\s*(.*)', block)
                        if category_match and start_match and end_match:
                            segments.append({"id": segment_id.strip(), "category": category_match.group(1).strip(), "start": start_match.group(1).strip(), "end": end_match.group(1).strip()})
                    return {"target": skill_target, "guidance": guidance, "segments": segments, "skill_file": sf}
            except Exception as e:
                print(f"      ⚠️ Error reading skill file {sf}: {e}")
        return None

    def _handle_skill_segmentation(self, doc_slug, clean_text, source_name, segments, guidance=""):
        existing_ids = self.storage.get_existing_ids(doc_slug)
        saved_count = 0
        
        # Track occurrence indices of start texts in the segments list
        start_pattern_counts = {}
        for seg in segments:
            start_text = seg["start"]
            start_pattern_counts[start_text] = start_pattern_counts.get(start_text, 0) + 1
            seg["occurrence_index"] = start_pattern_counts[start_text] - 1

        for seg in segments:
            article_id = seg["id"]
            if f"{article_id}.json" in existing_ids: continue
            def make_fuzzy_pattern(text):
                p = re.escape(text); p = p.replace(r'\ ', r'\s+'); p = re.sub(r'(\\([.,!?;:]))', r'\\s*\1', p)
                return p
            start_pattern = make_fuzzy_pattern(seg["start"])
            start_matches = list(re.finditer(start_pattern, clean_text, re.MULTILINE))
            if not start_matches:
                short_start = seg["start"][:50]; start_pattern = make_fuzzy_pattern(short_start)
                start_matches = list(re.finditer(start_pattern, clean_text, re.MULTILINE))
            if not start_matches: continue
            
            occ_idx = seg.get("occurrence_index", 0)
            if occ_idx < len(start_matches):
                start_match = start_matches[occ_idx]
            else:
                start_match = start_matches[-1]
                
            remaining_text = clean_text[start_match.end():]
            end_pattern = make_fuzzy_pattern(seg["end"])
            end_match = re.search(end_pattern, remaining_text, re.MULTILINE)
            if not end_match:
                short_end = seg["end"][:50]; end_pattern = make_fuzzy_pattern(short_end)
                end_match = re.search(end_pattern, remaining_text, re.MULTILINE)
            article_raw = clean_text[start_match.start():start_match.end() + end_match.end()].strip() if end_match else clean_text[start_match.start():].strip()
            structured_data = self._structure_article(article_raw, seg["category"], source_name, guidance)
            if structured_data:
                self.storage.save_structured_json(doc_slug, article_id, structured_data)
                print(f"      ✅ Saved {article_id} (via skill)")
                saved_count += 1
        return saved_count

    def _segment_with_ai(self, text, category):
        if not text.strip() or len(text.strip()) < 100: return []
        ai_text = text[:40000] + "\n...[TRUNC]" if len(text) > 45000 else text
        prompt = SEGMENT_PROMPT.format(text=ai_text)
        for attempt in range(5):
            try:
                res_text = self.rotator.chat_completion(messages=[{'role': 'user', 'content': prompt}], response_format={'type': 'json_object'})
                data = json.loads(res_text)
                if isinstance(data, list): return data
                elif isinstance(data, dict):
                    for key in ["articles", "items", "result"]:
                        if key in data and isinstance(data[key], list): return data[key]
                return [text] if len(text.strip()) > 300 else []
            except: time.sleep(5)
        return [text]

    def _structure_article(self, article_raw, category, source_name, guidance=""):
        prompt_instructions = STRUCTURE_PROMPT
        if guidance:
            prompt_instructions = STRUCTURE_PROMPT.replace("### Instructions:", f"### Instructions:\n\n### ADDITIONAL SKILL INSTRUCTIONS:\n{guidance}")
        prompt = prompt_instructions.format(text=article_raw, category=category, source=source_name)
        for attempt in range(5):
            try:
                res_text = self.rotator.chat_completion(messages=[{'role': 'user', 'content': prompt}], response_format={'type': 'json_object'})
                structured_data = json.loads(res_text)
                if not structured_data.get("teza") and not structured_data.get("case_number"): return None
                structured_data["full_markdown"] = article_raw
                return structured_data
            except: time.sleep(5)
        return None

    def _handle_manual_override_06_2024(self, doc_slug, clean_text, source_name): pass
    def _handle_manual_override_09_2024(self, doc_slug, clean_text, source_name): pass
    def _handle_manual_override_4_5_2025(self, doc_slug, clean_text, source_name): pass

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else None
    agent = LegalSegmenterAgent()
    agent.run(target_file)
