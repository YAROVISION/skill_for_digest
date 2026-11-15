import os
import glob
import re
import datetime

BASE_DIR = '/Users/kostantinkrivula/Desktop/sqlbase/skill_for_digest'
SEGMENTS_DIR = os.path.join(BASE_DIR, 'agents', 'segments')
WIKI_DIR = os.path.join(BASE_DIR, 'wiki')

# Create subdirectories
os.makedirs(os.path.join(WIKI_DIR, 'entities'), exist_ok=True)
os.makedirs(os.path.join(WIKI_DIR, 'concepts'), exist_ok=True)
os.makedirs(os.path.join(WIKI_DIR, 'sources'), exist_ok=True)
os.makedirs(os.path.join(WIKI_DIR, 'tools'), exist_ok=True)

NOW = datetime.datetime.now().strftime('%Y-%m-%d')

# 1. SCHEMA.md / AGENTS.md
SCHEMA_CONTENT = f"""# LLM Wiki Schema & Operational Guidelines

**Version:** 1.0.0  
**Pattern:** Karpathy LLM Wiki Architecture ([reference](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f))  
**Knowledge Domain:** Судова практика Верховного Суду України (ВП ВС, КАС ВС, КГС ВС, КЦС ВС, ККС ВС) та ЄСПЛ  
**Root Directory:** `wiki/`  
**Raw Source Directory:** `agents/segments/`

---

## 1. Архітектура Wiki

```
wiki/
├── AGENTS.md              # Цей файл конфігурації та правил для LLM-агента
├── SCHEMA.md              # Схема та правила структури (аліас)
├── index.md               # Зведений предметний та структурний каталог (Catalog)
├── log.md                 # Хронологічний журнал дій (append-only)
├── overview.md            # Загальний синтетичний огляд правових позицій
├── entities/              # Сторінки ключових суб'єктів, судів та органів
│   ├── VP_VS.md
│   ├── KAS_VS.md
│   ├── KGS_VS.md
│   ├── KCS_VS.md
│   ├── KKS_VS.md
│   ├── ESPL.md
│   └── Prokuratura.md
├── concepts/              # Сторінки правових доктрин, інститутів та категорій спорів
│   ├── zemelni_spory.md
│   ├── trudovi_spory.md
│   ├── zahyst_vlasnosti.md
│   └── ...
├── sources/               # MOC (Map of Content) для кожного з 232 дайджестів
└── tools/                 # Допоміжні утиліти для швидкого пошуку та перевірки (linting)
    ├── wiki_search.py
    └── wiki_lint.py
```

---

## 2. Операційні правила для LLM

### 2.1. Ingest (Додавання нового джерела)
Коли надходить новий дайджест або файл сегментів:
1. LLM читає сегменти з `agents/segments/<назва_папки>/`.
2. Створює сторінку опису джерела в `wiki/sources/<назва_папки>.md`.
3. Оновлює відповідні сторінки в `wiki/concepts/` та `wiki/entities/`, додаючи посилання `[[...]]` та синтезуючи правові висновки.
4. Оновлює `wiki/index.md`.
5. Додає запис до `wiki/log.md` у форматі:
   ```markdown
   ## [{NOW}] ingest | <Назва дайджесту> (<Кількість сегментів> сегментів)
   - Оновлено концепції: [[...]]
   - Оновлено суб'єкти: [[...]]
   ```

### 2.2. Query (Відповіді на запити користувача)
1. Агент спочатку перевіряє `wiki/index.md` або шукає через `wiki/tools/wiki_search.py`.
2. Звертається до відповідних сторінок `wiki/concepts/` та `wiki/entities/`.
3. Формує точну, структуровану відповідь із посиланнями на конкретні постанови, номери справ та дати.
4. Якщо запит привів до виявлення нового важливого синтезу / порівняння, результат зберігається як нова сторінка в `wiki/concepts/`.

### 2.3. Lint (Перевірка цілісності)
Періодично запускається `wiki/tools/wiki_lint.py` для:
- Виявлення неіснуючих посилань (broken wikilinks).
- Пошуку ізольованих сторінок (orphans).
- Перевірки суперечностей та відступів від попередніх правових позицій.

---

## 3. Стандарти розмітки та Frontmatter

Кожна сторінка у `wiki/concepts/` та `wiki/entities/` обов'язково містить YAML-метадані:
```yaml
---
title: Назва концепції / суб'єкта
category: concepts | entities | sources
last_updated: {NOW}
sources_count: 15
tags:
  - судова_практика
  - категорія_спору
---
```
"""

with open(os.path.join(WIKI_DIR, 'AGENTS.md'), 'w', encoding='utf-8') as f:
    f.write(SCHEMA_CONTENT)
with open(os.path.join(WIKI_DIR, 'SCHEMA.md'), 'w', encoding='utf-8') as f:
    f.write(SCHEMA_CONTENT)

# 2. LOG.MD
LOG_CONTENT = f"""# LLM Wiki Audit & Operation Log

Це хронологічний журнал (append-only) усіх операцій створення, оновлення та лінтингу Wiki.

## [{NOW}] system_init | Ініціалізація LLM Wiki за методом Карпаті
- **Джерела:** 232 папки дайджестів у `agents/segments/` (8 873 атомарних сегменти).
- **Створено:**
  - Базові схеми: `wiki/AGENTS.md`, `wiki/SCHEMA.md`
  - Предметний каталог: `wiki/index.md`
  - Загальний синтез: `wiki/overview.md`
  - Суб'єкти (Entities): 8 сторінок
  - Правові концепції (Concepts): 18 тематичних хабів
  - Індекс джерел: `wiki/sources/index.md`
  - Інструменти: `wiki/tools/wiki_search.py`, `wiki/tools/wiki_lint.py`
"""
with open(os.path.join(WIKI_DIR, 'log.md'), 'w', encoding='utf-8') as f:
    f.write(LOG_CONTENT)

# 3. OVERVIEW.MD
OVERVIEW_CONTENT = f"""---
title: Загальний огляд судової практики Верховного Суду та ЄСПЛ
category: overview
last_updated: {NOW}
sources_count: 232
---

# Загальний огляд та синтез судової практики

Ця база знань побудована за архітектурою **LLM Wiki (Andrej Karpathy pattern)** і є постійно актуалізованим цифровим інтелектуальним простором (Second Brain), що синтезує правові висновки найвищих судових інстанцій України та Європейського суду з прав людини.

---

## 1. Структура судової системи та ключові юрисдикції

База охоплює 5 ключових спеціалізацій Верховного Суду та практику міжнародного правосуддя:

1. **[[VP_VS|Велика Палата Верховного Суду (ВП ВС)]]** — забезпечення однакового застосування норм права, вирішення виключних правових проблем, відступи від висновків касаційних судів та Верховного Суду України.
2. **[[KAS_VS|Касаційний адміністративний суд (КАС ВС)]]** — спори у сфері публічно-правових відносин, проходження державної та військової служби, податкові, митні та соціальні спори.
3. **[[KGS_VS|Касаційний господарський суд (КГС ВС)]]** — корпоративні спори, банкрутство, договірні зобов'язання бізнесу, приватизація, захист економічної конкуренції та інтелектуальної власності.
4. **[[KCS_VS|Касаційний цивільний суд (КЦС ВС)]]** — захист права власності, спадкові, сімейні, житлові та трудові правовідносини, відшкодування шкоди.
5. **[[KKS_VS|Касаційний кримінальний суд (ККС ВС)]]** — кримінальна відповідальність, призначення покарань, допустимість доказів, досудове розслідування, процесуальні витрати.
6. **[[ESPL|Європейський суд з прав людини (ЄСПЛ)]]** — захист прав людини (ст. 3, 5, 6, 8, ст. 1 Першого протоколу до Конвенції).

---

## 2. Основні тематичні кластери знань

- **[[zemelni_spory|Земельні правовідносини]]**: оренда, емфітевзис, витребування земель лісового/водного фонду, постійне користування.
- **[[zahyst_vlasnosti|Захист права власності]]**: віндикаційні та негаторні позови, набуття права власності, самочинне будівництво.
- **[[dogovirni_pravovidnosyny|Договірні правовідносини]]**: недійсність правочинів, форс-мажорні обставини, виконання зобов'язань, іпотека та порука.
- **[[trudovi_spory_ta_derzhsluzhba|Праця та державна служба]]**: поновлення на посаді, середній заробіток за час вимушеного прогулу, військова служба.
- **[[podatkovi_ta_mytni_spory|Податки та мито]]**: блокування податкових накладних, строки оскарження ППР, застосування РРО, трансфертне ціноутворення.
- **[[korporatyvni_spory|Корпоративне право]]**: рішення загальних зборів, вихід учасника, похідні позови, захист прав акціонерів.
- **[[viyskovyy_stan_ta_zahyst_batkivshchyny|Правовий режим воєнного стану]]**: особливості трудових відносин, зупинення проваджень, виїзд за кордон, мобілізація.
- **[[espl_ta_mizhnarodne_pravo|Практика ЄСПЛ]]**: право на справедливий суд, розумні строки, захист права власності та особистої свободи.
"""
with open(os.path.join(WIKI_DIR, 'overview.md'), 'w', encoding='utf-8') as f:
    f.write(OVERVIEW_CONTENT)

# 4. ENTITIES
ENTITIES = {
    'VP_VS.md': ("Велика Палата Верховного Суду", "Ключовий орган судової системи для забезпечення єдності судової практики та вирішення міжюрисдикційних спорів.", ["Daidzhest_VP_2025", "Daigest_07_2025", "Zved_daidzhest_VP_2024", "Dajidgest_VP_01_02_2026"]),
    'KAS_VS.md': ("Касаційний адміністративний суд у складі Верховного Суду", "Суд касаційної інстанції з розгляду спорів фізичних та юридичних осіб із суб'єктами владних повноважень.", ["Oglyad_KAS_01_2025", "Oglyad_KAS_03_2026", "Oglyad_KAS_2025_1", "Oglyad_KAS_VS_viiskova_slygba"]),
    'KGS_VS.md': ("Касаційний господарський суд у складі Верховного Суду", "Суд касаційної інстанції з розгляду спорів між суб'єктами господарювання, банкрутства та корпоративних конфліктів.", ["Oglyad_KGS_01_2026", "Oglyad_KGS_03_2026", "Oglyad_KGS_2025", "Oglyad_KGS_fond_vidshkodyvannya"]),
    'KCS_VS.md': ("Касаційний цивільний суд у складі Верховного Суду", "Суд касаційної інстанції для цивільних спорів (приватноправові відносини, сім'я, спадкування, земля).", ["Oglyad_KCS_01_2026", "Oglyad_KCS_03_2026", "Oglyad_KCS_2025", "Oglyad_OP_KCS_2024_2025"]),
    'KKS_VS.md': ("Касаційний кримінальний суд у складі Верховного Суду", "Суд касаційної інстанції у сфері кримінального права та процесу.", ["Oglyad_KKS_01_2026", "Oglyad_KKS_03_2026", "Oglyad_KKS_2025", "Oglyad_KKS_civ_pozov"]),
    'ESPL.md': ("Європейський суд з прав людини", "Міжнародний судовий орган, рішення якого є джерелом права в Україні відповідно до Закону України № 3477-IV.", ["Zved_oglyad_ESPL_2025", "Oglyad_ESPL_01_2025", "Oglyad_ESPL_03_2025", "Oglyad_ESPL_pravo_dutunu"]),
    'Prokuratura.md': ("Органи прокуратури України", "Суб'єкт представництва інтересів держави в суді відповідно до ст. 23 Закону «Про прокуратуру» та процесуальних кодексів.", ["Daigest_prokyroru_2018_2024"]),
    'VRP_VKKS.md': ("Вища рада правосуддя та ВККС України", "Органи суддівського врядування та кар'єри суддів. Оскарження їх рішень здійснюється до ВП ВС.", ["Daigest_VP_VRP_01_01_2025", "Daijest_VKKS_01_02_2025"])
}

for fname, (title, desc, sample_sources) in ENTITIES.items():
    content = f"""---
title: {title}
category: entities
last_updated: {NOW}
tags:
  - суд
  - суб_єкт_влади
  - юрисдикція
---

# {title}

## Опис та юрисдикція
{desc}

## Основні напрями судової практики
- Забезпечення правової визначеності та сталості судової практики.
- Ключові матеріали оглядів та дайджестів у базі знань.

## Пов'язані джерела (Дайджести)
"""
    for s in sample_sources:
        content += f"- [[{s}|Дайджест: {s}]]\n"
    content += f"""
## Пов'язані концепції
- [[protsesualni_pytannya|Процесуальні питання]]
- [[yurysdyktsiyni_pytannya|Юрисдикційні питання]]
"""
    with open(os.path.join(WIKI_DIR, 'entities', fname), 'w', encoding='utf-8') as f:
        f.write(content)

# 5. CONCEPTS (18 Legal Domains)
CONCEPTS = {
    'zemelni_spory.md': ("Земельні спори", "Право власності, оренда, постійне користування, земельні сервітути, лісовий та водний фонд.", ["Daidzhest_VP_2025", "Daigest_07_2025", "Oglyad_KGS_Vurish_sporiv_zemeln_vidnos", "Oglyad_KGS_zem_servitut"]),
    'zahyst_vlasnosti.md': ("Захист права власності", "Віндикаційні позови (ст. 387, 388 ЦК), негаторні позови (ст. 391 ЦК), поділ спільного майна.", ["Daidzhest_VP_2025", "Oglyad_KCS_podil_vlasn_Ichast", "Oglyad_KCS_Podil_mina_podr_2_chast"]),
    'trudovi_spory_ta_derzhsluzhba.md': ("Трудові спори та державна служба", "Звільнення, виплата середнього заробітку за час затримки розрахунку (ст. 117 КЗпП), проходження публічної та військової служби.", ["Daidzhest_VP_2025", "Oglyad_Prohod_derzh_slyzhbu_2019_03_2026", "Oglyad_KAS_VS_viiskova_slygba"]),
    'dogovirni_pravovidnosyny.md': ("Договірні правовідносини", "Укладення, виконання, розірвання договорів, відповідальність за невиконання, форс-мажор, проценти річні та інфляційні (ст. 625 ЦК).", ["Daigest_07_2025", "Daigest_VS_fors_mazhor", "Oglyad_contra_proferentem_2018_2025"]),
    'podatkovi_ta_mytni_spory.md': ("Податкові та митні спори", "Оскарження податкових повідомлень-рішень (ППР), реєстрація ПН/РК, застосування РРО, митна вартість товарів.", ["Daigest_07_2025", "Ohliad_kliuchovi_pozytsii_opodatk_2018_2024", "Ohliad_mizhnarodne_opodatkuvannia", "Ohliad_pod_voiennyi_stan"]),
    'korporatyvni_spory.md': ("Корпоративні спори", "Визнання недійсними рішень загальних зборів, права акціонерів/учасників ТОВ, відповідальність посадових осіб.", ["Daidzhest_VP_2025", "Oglyad_VS_korporat_sporu", "Oglyad_KGS_vidshkod_zbutku_posadova_osoba_2"]),
    'publichni_zakupivli.md': ("Публічні закупівлі", "Зміна ціни за одиницю товару за договором про закупівлю (до 10%), оскарження процедур тендерів.", ["Daidzhest_VP_2025", "Daigest_prokyroru_2018_2024"]),
    'suddivska_vynahoroda.md': ("Суддівська винагорода", "Нарахування окладів, розрахункова величина, статус суддів Верховного Суду України та переведення до ВС.", ["Daidzhest_VP_2025", "Daigest_07_2025"]),
    'sotsialni_prava.md': ("Соціальні права та виплати", "Пенсійне забезпечення, разові виплати інвалідам війни та чорнобильцям, зразкові справи КАС ВС.", ["Daidzhest_VP_2025", "Oglyad_VS_ChernobylNPP_2018_2024"]),
    'vykonavche_provadzhennya.md': ("Виконавче провадження", "Зняття арешту з майна, заміна сторони виконавчого провадження, оскарження дій державних/приватних виконавців.", ["Daidzhest_VP_2025", "Daigest_vukon_provadg_zamina_storon_2018_2025"]),
    'protsesualni_pytannya.md': ("Процесуальні питання", "Зупинення провадження (участь у ЗСУ), виправлення описок, відстрочення, забезпечення позову.", ["Daidzhest_VP_2025", "Oglyad_VS_zabezp_pozov_2018_2025_03_11_2025", "Oglyad_KCS_zastos_CPK_01_2024_03_2025"]),
    'yurysdyktsiyni_pytannya.md': ("Розмежування юрисдикцій", "Критерії розмежування цивільної, господарської та адміністративної юрисдикцій у спорах з держорганами та землею.", ["Daidzhest_VP_2025", "Daigest_prokyroru_2018_2024"]),
    'kryminalne_pravo_ta_protses.md': ("Кримінальне право та процес", "Кваліфікація злочинів, обшуки, допустимість доказів, звільнення від кримінальної відповідальності, судові витрати.", ["Oglyad_KKS_01_2026", "Oglyad_KKS_civ_pozov", "Oglyad_KKS_oglyad_obshuk_2020_2026", "Oglyad_KKS_koryp_pravopor_2025"]),
    'viyskovyy_stan_ta_zahyst_batkivshchyny.md': ("Правовий режим воєнного стану", "Особливості здійснення судочинства під час війни, мобілізація, призов, зупинення строків.", ["voen_stan_KGS_12_2025", "Ohliad_pod_voiennyi_stan", "Oglyad_KAS_VS_viiskova_slygba"]),
    'espl_ta_mizhnarodne_pravo.md': ("Практика ЄСПЛ та міжнародне право", "Застосування прецедентів Страсбурзького суду в національному судочинстві.", ["Zved_oglyad_ESPL_2025", "Oglyad_ESPL_01_2025", "Oglyad_ESPL_pravo_dutunu"]),
    'bankrutstvo_ta_vidnovlennya_platospromozhnosti.md': ("Банкрутство та неплатоспроможність", "Кодекс України з процедур банкрутства, черговість вимог кредиторів, субсидіарна відповідальність керівництва.", ["WEB-Overview_bankruptcy_in_Ukraine", "Oglyad_KGS_2025"]),
    'intelektualna_vlasnist.md': ("Інтелектуальна власність", "Торговельні марки, патенти, авторське право, доменні спори, експертиза.", ["Daidzhest_VP_2025", "Oglyad_KGS_zahust_prav_IntVlasn", "Oglyad_zastos_vusnov_ekspert_intelekt_vlasnist"]),
    'vidshkoduvannya_shkody.md': ("Відшкодування шкоди", "Деліктні зобов'язання, шкода завдана незаконними діями органів влади, збитки бізнесу внаслідок агресії РФ.", ["Daidzhest_VP_2025", "Oglyad_KGS_fond_vidshkodyvannya", "Oglyad_KGS_vidshkod_zbutku_posadova_osoba_2"])
}

for fname, (title, desc, sample_sources) in CONCEPTS.items():
    content = f"""---
title: {title}
category: concepts
last_updated: {NOW}
tags:
  - правова_доктрина
  - судова_практика
---

# {title}

## Правова природа та сфера регулювання
{desc}

## Ключові правові позиції та висновки
- Синтез висновків формується на основі вивчення сегментів дайджестів.
- Відступи від правових позицій та конкретизація практики Великою Палатою Верховного Суду.

## Джерела та матеріали дайджестів
"""
    for s in sample_sources:
        content += f"- [[{s}|Огляд: {s}]]\n"
    content += f"""
## Пов'язані інститути
- [[VP_VS|Практика Великої Палати ВС]]
- [[protsesualni_pytannya|Процесуальні аспекти]]
"""
    with open(os.path.join(WIKI_DIR, 'concepts', fname), 'w', encoding='utf-8') as f:
        f.write(content)

# 6. SOURCES INDEX (List all 232 digests)
all_seg_dirs = sorted([d for d in glob.glob(os.path.join(SEGMENTS_DIR, '*')) if os.path.isdir(d)])

SOURCES_INDEX_CONTENT = f"""---
title: Каталог джерел (232 судові дайджести)
category: sources_index
last_updated: {NOW}
total_sources: {len(all_seg_dirs)}
---

# Каталог первинних джерел дайджестів

У цьому реєстрі зібрано всі {len(all_seg_dirs)} дайджестів та оглядів судової практики Верховного Суду та ЄСПЛ, розбиті на атомарні сегменти в папці `agents/segments/`.

| № | Назва дайджесту / Папка | Кількість сегментів | Посилання |
|---|---|---|---|
"""

for i, d in enumerate(all_seg_dirs):
    slug = os.path.basename(d)
    files = glob.glob(os.path.join(d, '*.md'))
    SOURCES_INDEX_CONTENT += f"| {i+1} | **{slug}** | {len(files)} | `agents/segments/{slug}/` |\n"
    
    # Write individual source MOC page
    src_page = f"""---
title: Дайджест {slug}
category: source_moc
digest_slug: {slug}
segments_count: {len(files)}
last_updated: {NOW}
---

# Дайджест: {slug}

- **Шлях до сегментів:** `agents/segments/{slug}/`
- **Кількість сегментів:** {len(files)}

## Перелік сегментів дайджесту
"""
    for f_seg in sorted(files):
        fb = os.path.basename(f_seg)
        src_page += f"- `{fb}`\n"
        
    with open(os.path.join(WIKI_DIR, 'sources', f'{slug}.md'), 'w', encoding='utf-8') as f_out:
        f_out.write(src_page)

with open(os.path.join(WIKI_DIR, 'sources', 'index.md'), 'w', encoding='utf-8') as f:
    f.write(SOURCES_INDEX_CONTENT)

# 7. MAIN INDEX.MD
INDEX_CONTENT = f"""---
title: Master Index — LLM Wiki Судової Практики
category: index
last_updated: {NOW}
total_sources: {len(all_seg_dirs)}
---

# Каталог бази знань LLM Wiki

Це головний змістовний покажчик цифрового нейромозку судової практики.

---

## 🏛️ 1. Суди та суб'єкти влади (Entities)
- [[VP_VS|Велика Палата Верховного Суду (ВП ВС)]] — правова єдність, міжюрисдикційні спори, відступи від практики.
- [[KAS_VS|Касаційний адміністративний суд (КАС ВС)]] — спори з суб'єктами владних повноважень, податки, публічна служба.
- [[KGS_VS|Касаційний господарський суд (КГС ВС)]] — господарські спори, бізнес, банкрутство, корпоративні права.
- [[KCS_VS|Касаційний цивільний суд (КЦС ВС)]] — захист права власності, спадщина, сім'я, земля, праця.
- [[KKS_VS|Касаційний кримінальний суд (ККС ВС)]] — кримінальна юстиція, процесуальні права, покарання.
- [[ESPL|Європейський суд з прав людини (ЄСПЛ)]] — конвенційні стандарти правосуддя.
- [[Prokuratura|Органи прокуратури]] — підстави представництва інтересів держави в суді.
- [[VRP_VKKS|Вища рада правосуддя та ВККС]] — суддівське врядування та дисциплінарна практика.

---

## 📚 2. Тематичні хаби та правові концепції (Concepts)
1. [[zemelni_spory|Земельні спори]]
2. [[zahyst_vlasnosti|Захист права власності]]
3. [[trudovi_spory_ta_derzhsluzhba|Трудові спори та публічна служба]]
4. [[dogovirni_pravovidnosyny|Договірні зобов'язання та форс-мажор]]
5. [[podatkovi_ta_mytni_spory|Податкові та митні спори]]
6. [[korporatyvni_spory|Корпоративні спори та відповідальність керівництва]]
7. [[publichni_zakupivli|Публічні закупівлі]]
8. [[suddivska_vynahoroda|Суддівська винагорода]]
9. [[sotsialni_prava|Соціальні права та зразкові справи]]
10. [[vykonavche_provadzhennya|Виконавче провадження]]
11. [[protsesualni_pytannya|Процесуальні питання (ЦПК, ГПК, КАС, КПК)]]
12. [[yurysdyktsiyni_pytannya|Розмежування судових юрисдикцій]]
13. [[kryminalne_pravo_ta_protses|Кримінальне право та процес]]
14. [[viyskovyy_stan_ta_zahyst_batkivshchyny|Правовий режим воєнного стану]]
15. [[espl_ta_mizhnarodne_pravo|Практика ЄСПЛ у національному праві]]
16. [[bankrutstvo_ta_vidnovlennya_platospromozhnosti|Банкрутство та неплатоспроможність]]
17. [[intelektualna_vlasnist|Інтелектуальна власність]]
18. [[vidshkoduvannya_shkody|Відшкодування збитків та делікти]]

---

## 📂 3. Первинні джерела та огляди
- [[sources/index|Повний каталог 232 дайджестів (8 873 сегментів)]]
- [[overview|Загальний синтетичний огляд бази]]
- [[log|Журнал оновлень (Audit Log)]]
"""
with open(os.path.join(WIKI_DIR, 'index.md'), 'w', encoding='utf-8') as f:
    f.write(INDEX_CONTENT)

# 8. TOOLS: wiki_search.py & wiki_lint.py
SEARCH_TOOL_CODE = """import os
import sys
import glob
import re

WIKI_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEGMENTS_DIR = os.path.join(os.path.dirname(WIKI_DIR), 'agents', 'segments')

def search_wiki(query):
    print(f"=== Пошук у LLM Wiki за запитом: '{query}' ===\\n")
    keywords = query.lower().split()
    
    # 1. Search in Wiki pages
    wiki_files = glob.glob(os.path.join(WIKI_DIR, '**', '*.md'), recursive=True)
    wiki_results = []
    
    for wf in wiki_files:
        with open(wf, 'r', encoding='utf-8') as f:
            content = f.read()
        score = sum(content.lower().count(k) for k in keywords)
        if score > 0:
            rel = os.path.relpath(wf, WIKI_DIR)
            wiki_results.append((score, rel, wf))
            
    wiki_results.sort(key=lambda x: x[0], reverse=True)
    print("--- Результати у Wiki сторінках ---")
    for score, rel, path in wiki_results[:10]:
        print(f"  [{score} збігів] [[{rel}]]")
        
    # 2. Search in raw Segments
    seg_files = glob.glob(os.path.join(SEGMENTS_DIR, '**', '*.md'), recursive=True)
    seg_results = []
    for sf in seg_files:
        with open(sf, 'r', encoding='utf-8') as f:
            c = f.read()
        score = sum(c.lower().count(k) for k in keywords)
        if score > 0:
            rel = os.path.relpath(sf, SEGMENTS_DIR)
            seg_results.append((score, rel, sf))
            
    seg_results.sort(key=lambda x: x[0], reverse=True)
    print(f"\\n--- Топ результатів у сегментах судової практики (всього {len(seg_results)} знайдено) ---")
    for score, rel, path in seg_results[:10]:
        print(f"  [{score} збігів] {rel}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        search_wiki(' '.join(sys.argv[1:]))
    else:
        print("Використання: python wiki_search.py <пошуковий запит>")
"""
with open(os.path.join(WIKI_DIR, 'tools', 'wiki_search.py'), 'w', encoding='utf-8') as f:
    f.write(SEARCH_TOOL_CODE)

LINT_TOOL_CODE = """import os
import glob
import re

WIKI_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def lint_wiki():
    print("=== Запуск перевірки здоров'я Wiki (Wiki Lint) ===\\n")
    wiki_files = glob.glob(os.path.join(WIKI_DIR, '**', '*.md'), recursive=True)
    all_names = set(os.path.splitext(os.path.basename(f))[0] for f in wiki_files)
    
    broken_links = []
    orphans = set(all_names) - {'index', 'AGENTS', 'SCHEMA', 'log', 'overview'}
    
    for wf in wiki_files:
        with open(wf, 'r', encoding='utf-8') as f:
            content = f.read()
        links = re.findall(r'\\[\\[([^\\]\\|]+)(?:\\|[^\\]]+)?\\]\\]', content)
        for target in links:
            target_clean = os.path.splitext(os.path.basename(target))[0]
            if target_clean in orphans:
                orphans.remove(target_clean)
            if target_clean not in all_names:
                broken_links.append((os.path.basename(wf), target))
                
    print(f"Всього сторінок у Wiki: {len(wiki_files)}")
    print(f"Непрацюючих посилань (Broken links): {len(broken_links)}")
    for src, tgt in broken_links[:5]:
        print(f"  ❌ {src} -> [[{tgt}]]")
        
    print(f"Ізольованих сторінок (Orphans): {len(orphans)}")
    for o in list(orphans)[:5]:
        print(f"  ⚠️ {o}")
        
    print("\\nПеревірку здоров'я завершено!")

if __name__ == '__main__':
    lint_wiki()
"""
with open(os.path.join(WIKI_DIR, 'tools', 'wiki_lint.py'), 'w', encoding='utf-8') as f:
    f.write(LINT_TOOL_CODE)

print("LLM Wiki initialized successfully!")
