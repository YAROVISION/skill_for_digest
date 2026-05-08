import re

class TextProcessor:
    @staticmethod
    def clean_noise(text):
        # Remove standard noise
        text = re.sub(r'#### \d+\s+Рішення, внесені до ЄДРСР.*?\n', '', text)
        text = re.sub(r'#### \d+\s+Огляд судової практики.*?ВС.*?\n', '', text)
        text = re.sub(r'#### Дайджест судової практики.*?ВС.*?\n', '', text)
        text = re.sub(r'#### Огляд судової практики.*?ВС.*?\n', '', text)
        text = re.sub(r'\.\.\.*\s+\d+\s*\n', '\n', text)
        
        # Remove Table of Contents (Зміст) if found
        toc_match = re.search(r'\nЗміст\n(.*?)\n([IVXLCDM]+\.|#{1,4}\s+)', text, re.DOTALL)
        if toc_match:
            # Keep everything before "Зміст" and skip the TOC block
            text = text[:toc_match.start()] + "\n" + text[toc_match.end()-2:]

        # Remove Page Headers (Title ... PageNum or Title PageNum)
        text = re.sub(r'^[IVXLCDM]+\.\s+.*?\s+\d+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^.*?[ \.]{3,}\d+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        
        return text

    @staticmethod
    def segment_by_sections(text):
        # Split by major headers ONLY (at the start of the line)
        pattern = r'\n(#{1,4}\s+\d+\s+.*?|^[IVXLCDM]+\.\s+[А-ЯІЄЇ][^0-9\n]*?|^###\s+Огляд практики.*?)\n'
        sections = re.split(pattern, text, flags=re.MULTILINE)
        segmented = []
        if sections and len(sections) > 0 and sections[0].strip():
            segmented.append({"category": "Вступ", "content": sections[0]})
        for i in range(1, len(sections), 2):
            header = sections[i].strip()
            header = re.sub(r'^#{1,4}\s+', '', header) # Clean markdown hash
            content = sections[i+1] if i+1 < len(sections) else ""
            segmented.append({"category": header, "content": content})
        return segmented if segmented else [{"category": "Весь документ", "content": text}]

    @staticmethod
    def extract_links_segmentation(section_content):
        """
        Regex-based segmentation based on court links. 
        Good for specific formats like Ukrainian registry.
        """
        pattern = r'(\[.*?\]\(https://(?:reyestr\.court\.gov\.ua/Review/|curia\.europa\.eu/juris/document/)\d+.*?\))'
        parts = re.split(pattern, section_content, flags=re.DOTALL)
        blocks = []
        for i in range(0, len(parts)-1, 2):
            article_text = parts[i].strip()
            link = parts[i+1].strip()
            article_text = re.sub(r'^\s*[–-]\s*\n', '', article_text).strip()
            blocks.append(article_text + "\n\n" + link)
        return blocks
