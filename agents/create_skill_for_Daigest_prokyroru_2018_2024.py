import os
import re
from tools.storage_tools import MinioStorage

# ПЕРЕЛІК ФРАЗ ДЛЯ ПОЧАТКУ СЕГМЕНТІВ (згідно з вимогами користувача)
START_PHRASES = [
    "Прокурор звернувся",
    "Заступник керівника",
    "Заступник прокурора",
    "ТОВ «Росава Агро» звернулося до суду",
    "Прокурор місцевої прокуратури",
    "Прокурор в особі Кабінету Міністрів України",
    "Прокурор в інтересах держави в особі Кабінету Міністрів України",
    "Заступник військового прокурора звернувся з позовом",
    "Заступник військового прокурора",
    "Прокурор, діючи в інтересах держави в особі",
    "Керівник окружної прокуратури",
    "Заступник керівника місцевої прокуратури",
    "Керівник місцевої прокуратури",
    "Прокурор в інтересах держави",
    "Перший заступник прокурора Київської області",
    "ТОВ «Старонаводницький парк» звернулося",
    "Керівник Полтавської окружної прокуратури",
    "Перший заступник керівника",
    "Перший заступник військового прокурора",
    "Перший заступник прокурора області",
    "Прокурор Києво-Святошинського району Київської області",
    "Перший заступник керівника місцевої прокуратури",
    "САП звернулася з позовом",
    "Франківська окружна прокуратура",
    "Першим заступником прокурора",
    "Позвачі звернулися до суду",
    "У 2012 році ДП «Житомирське лісове господарство»",
    "ПП звернулося до суду з позово",
    "ОСОБА_1 звернувся з позовом",
    "Заступник Генерального прокурора",
    "Керівник САП подав скаргу",
    "Фізична особа звернулася із позовом",
    "ТОВ «Транслегіон-Альфа» звернулося з позовною",
    "У цій справі прокурор не брав участі у судовому процесі під час розгляду",
    "Прокурор Одеської області звернувся",
    "Керівником окружної прокуратури",
    "У листопаді 2018 року перший заступник керівника",
    "Заступник прокурора міста Києва",
    "Міська рада звернулась до місцевої прокуратури"
]

def create_skill_file(target_slug="Daigest_prokyroru_2018_2024"):
    """
    Створює файл навички (skill file) на основі заданих параметрів сегментації.
    """
    storage = MinioStorage()
    content = storage.get_object_content(f"markdown/{target_slug}/{target_slug}.md")
    if not content:
        print(f"❌ Не вдалося отримати контент для {target_slug}")
        return

    # Нормалізація пробілів
    content = content.replace('\xa0', ' ')
    lines = content.split('\n')
    
    # 1. Пошук усіх початків сегментів
    sorted_phrases = sorted(START_PHRASES, key=len, reverse=True)
    starts = []
    for i, line in enumerate(lines):
        clean = line.strip()
        if not clean: continue
        for phrase in sorted_phrases:
            if clean.startswith(phrase):
                starts.append((i, clean))
                break
    
    # 2. Пошук усіх кінців сегментів (абзаци "Детальніше...")
    ends = []
    for i, line in enumerate(lines):
        clean = line.strip()
        if clean.startswith("Детальніше з текстом постанови"):
            # Захоплюємо весь абзац до першого подвійного переносу рядка
            # або до початку секції "Аналогічний..."
            block_lines = []
            for j in range(i, len(lines)):
                l = lines[j].strip()
                if not l and j > i: break
                if "Аналогічний правовий висновок" in l: break
                block_lines.append(l)
            
            full_end = " ".join(block_lines)
            if "https://reyestr.court.gov.ua/Review/" in full_end:
                ends.append((i, full_end))

    # 3. Створення пар Сегментів
    segments = []
    current_end_ptr = 0
    for i in range(len(starts)):
        start_idx, start_text = starts[i]
        
        while current_end_ptr < len(ends) and ends[current_end_ptr][0] < start_idx:
            current_end_ptr += 1
            
        if current_end_ptr < len(ends):
            end_idx, end_text = ends[current_end_ptr]
            
            # Обмежуємо відстань між початком і кінцем (макс 100 рядків)
            if end_idx - start_idx < 100:
                segments.append({
                    "start": start_text,
                    "end": end_text
                })
                current_end_ptr += 1

    # 4. Запис у файл навички
    skill_path = f"agents/skills_for_markdownfiles/skill_for_{target_slug}.md"
    os.makedirs(os.path.dirname(skill_path), exist_ok=True)
    
    with open(skill_path, 'w', encoding='utf-8') as f:
        f.write("# Skill: Manual Document Segmentation\n\n")
        f.write(f"**Target File**: {target_slug}\n\n")
        f.write("## Prompts Guidance\n")
        f.write("- Сегменти починаються з визначених фраз (Прокурор, Заступник, ТОВ тощо).\n")
        f.write("- Сегмент закінчується на абзаці \"Детальніше з текстом постанови...\" (включаючи посилання).\n")
        f.write("- Один сегмент = Одна справа = Один JSON.\n")
        f.write("- **ВАЖЛИВО**: Якщо після абзацу \"Детальніше...\" йде абзац \"Аналогічний правовий висновок...\", він НЕ повинен входити до сегменту.\n\n")
        f.write("## Segments\n\n")
        
        for idx, seg in enumerate(segments, 1):
            f.write(f"### [manual_a{idx}]\n")
            f.write(f"- **Category**: (Визначити з контексту)\n")
            f.write(f"- **Rule**: Один сегмент = Одна справа = Один JSON\n")
            f.write(f"- **Start**: {seg['start']}\n")
            f.write(f"- **End**: {seg['end']}\n\n")

    print(f"✅ Успішно створено файл навички: {skill_path}")
    print(f"📊 Всього виділено сегментів: {len(segments)}")

if __name__ == "__main__":
    create_skill_file()
