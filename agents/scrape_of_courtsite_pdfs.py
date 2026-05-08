"""
scrape_of_courtsite_pdfs.py

Парсить сайт Верховного Суду, знаходить посилання на PDF-файли,
перевіряє чи файл вже існує у list_of_pdfs.md,
і якщо ні — завантажує до MinIO та додає запис у список.
"""

import os
import re
import time
import random
import requests
import urllib.parse
from bs4 import BeautifulSoup
from minio import Minio
from minio.error import S3Error
from io import BytesIO
from dotenv import load_dotenv

# ── Configuration ──────────────────────────────────────────────────────────────

load_dotenv(dotenv_path='.env.local', override=True)

SOURCE_PAGE      = 'https://supreme.court.gov.ua/supreme/pokazniki-diyalnosti/analiz/'
TARGET_PATH_PART = 'https://court.gov.ua/storage/portal/supreme/'
DELAY_OPTIONS    = [3, 5, 6, 7]  # seconds
DRY_RUN          = os.getenv('DRY_RUN', 'false').lower() == 'true'

MINIO_ENDPOINT   = os.getenv('MINIO_ENDPOINT', '').replace('https://', '').replace('http://', '')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
MINIO_BUCKET     = os.getenv('MINIO_BUCKET', 'court-documents')
MINIO_PREFIX     = 'pdfs/'

LIST_FILE        = os.path.join(
    os.path.dirname(__file__),
    'lists', 'list_of_pdfs.md'
)

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def wait_random():
    ms = random.choice(DELAY_OPTIONS)
    print(f'[Pacing] Waiting {ms} seconds before next request...')
    time.sleep(ms)


_TS_PREFIX = re.compile(r'^\d+_')  # наприклад: 1775151020585_


def strip_timestamp(filename: str) -> str:
    """Remove leading timestamp prefix (e.g. '1775151020585_') from filename."""
    return _TS_PREFIX.sub('', filename)


def transliterate(text: str) -> str:
    """Transliterate Ukrainian Cyrillic to Latin."""
    mapping = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'ґ': 'g', 'д': 'd', 'е': 'e', 'є': 'ie',
        'ж': 'zh', 'з': 'z', 'и': 'y', 'і': 'i', 'ї': 'i', 'й': 'i', 'к': 'k', 'л': 'l',
        'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ь': '',
        'ю': 'iu', 'я': 'ia',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'H', 'Ґ': 'G', 'Д': 'D', 'Е': 'E', 'Є': 'Ie',
        'Ж': 'Zh', 'З': 'Z', 'И': 'Y', 'І': 'I', 'Ї': 'I', 'Й': 'I', 'К': 'K', 'Л': 'L',
        'М': 'M', 'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch', 'Ь': '',
        'Ю': 'Iu', 'Я': 'Ia'
    }
    return "".join(mapping.get(c, c) for c in text)


def normalize_filename(url_part: str) -> str:
    """Decode URL, transliterate Cyrillic, and replace spaces with underscores."""
    # 1. Decode URL encoding (%D0%94...)
    name = urllib.parse.unquote(url_part)
    # 2. Transliterate Cyrillic to Latin
    name = transliterate(name)
    # 3. Replace spaces with underscores
    name = name.replace(' ', '_')
    # 4. Cleanup multiple underscores
    name = re.sub(r'_{2,}', '_', name)
    return name


def load_known_files(list_path: str) -> set:
    """Return a set of ORIGINAL (no-timestamp) file names already recorded.

    Files stored as '1775151020585_Oglyad_KAS_12_2025.pdf' are normalised
    to 'Oglyad_KAS_12_2025.pdf' so comparison with scraped names works.
    """
    known = set()
    if not os.path.exists(list_path):
        return known
    with open(list_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('- '):
                name = line[2:].strip()
                if name:
                    known.add(strip_timestamp(name))  # ← нормалізація
    return known


def append_to_list(list_path: str, filename: str):
    """Append a new file name to the markdown list."""
    with open(list_path, 'a', encoding='utf-8') as f:
        f.write(f'- {filename}\n')


def scrape_pdf_links(url: str) -> list:
    """Fetch the page and extract all matching PDF hrefs."""
    print(f'[Fetch] {url}')
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    links = []
    for tag in soup.find_all('a', href=True):
        href = tag['href']
        if TARGET_PATH_PART in href and href.lower().endswith('.pdf'):
            links.append(href)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for lnk in links:
        if lnk not in seen:
            seen.add(lnk)
            unique.append(lnk)
    return unique


def upload_to_minio(client: Minio, pdf_url: str, filename: str) -> bool:
    """Download PDF from url and upload to MinIO. Returns True on success."""
    print(f'[Download] {pdf_url}')
    resp = requests.get(pdf_url, headers=HEADERS, timeout=60)
    resp.raise_for_status()

    data   = BytesIO(resp.content)
    length = len(resp.content)
    object_name = MINIO_PREFIX + filename

    print(f'[Upload] → {MINIO_BUCKET}/{object_name}  ({length} bytes)')
    client.put_object(
        MINIO_BUCKET,
        object_name,
        data,
        length,
        content_type='application/pdf',
        metadata={
            'scraped-from': SOURCE_PAGE,
            'source-url':   pdf_url,
        }
    )
    return True

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print('─── Supreme Court PDF Scraper (Python) Started ───')
    print(f'Source : {SOURCE_PAGE}')
    print(f'Dry run: {DRY_RUN}')
    print(f'List   : {LIST_FILE}')
    print()

    # 1. Load already-known file names
    known_files = load_known_files(LIST_FILE)
    print(f'[List] {len(known_files)} files already recorded in list_of_pdfs.md')

    # 2. Scrape PDF links
    try:
        pdf_links = scrape_pdf_links(SOURCE_PAGE)
    except Exception as e:
        print(f'❌ Failed to fetch source page: {e}')
        return

    print(f'[Discovery] Found {len(pdf_links)} unique PDF links on page')

    if DRY_RUN:
        print('\n[Dry Run] Links that would be processed:')
        for lnk in pdf_links:
            fname = lnk.split('/')[-1]
            status = '✅ already known' if fname in known_files else '🆕 new'
            print(f'  {status}  {fname}')
        print('\n[Dry Run] Exiting without uploading.')
        return

    # 3. Connect to MinIO
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=True
    )

    # 4. Process each link
    new_count = 0
    skip_count = 0

    for i, url in enumerate(pdf_links):
        raw_name = url.split('/')[-1]
        filename = normalize_filename(raw_name)

        if filename in known_files:
            print(f'[{i+1}/{len(pdf_links)}] ⏭  Skip (already exists): {filename}')
            skip_count += 1
            continue

        print(f'\n[{i+1}/{len(pdf_links)}] 🆕 New file: {filename}')

        try:
            upload_to_minio(client, url, filename)
            append_to_list(LIST_FILE, filename)
            known_files.add(filename)
            new_count += 1
            print(f'✅ Uploaded and recorded: {filename}')
        except Exception as e:
            print(f'❌ Error processing {filename}: {e}')

        # Polite delay between requests (skip after last item)
        if i < len(pdf_links) - 1:
            wait_random()

    print(f'\n─── Scraper Finished ───')
    print(f'  Skipped (already known) : {skip_count}')
    print(f'  Downloaded & uploaded   : {new_count}')


if __name__ == '__main__':
    main()

# ── Команди запуску ────────────────────────────────────────────────────────────
#
# Пробний запуск (без завантаження — лише показує що є нове):
#   DRY_RUN=true python3 agents/scrape_of_courtsite_pdfs.py
#
# Реальний запуск (завантажує нові PDF у MinIO):
#   python3 agents/scrape_of_courtsite_pdfs.py
