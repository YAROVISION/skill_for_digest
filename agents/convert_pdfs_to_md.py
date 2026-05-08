import os
import re
import tempfile
import urllib.parse
import sys
from minio import Minio
from dotenv import load_dotenv
import pymupdf4llm

# Load environment from .env.local
load_dotenv(dotenv_path='.env.local', override=True)

# MinIO Configuration
ENDPOINT = os.getenv('MINIO_ENDPOINT', '').replace('https://', '').replace('http://', '')
ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
BUCKET_NAME = os.getenv('MINIO_BUCKET', 'court-documents')

def get_minio_client():
    if not ENDPOINT or not ACCESS_KEY or not SECRET_KEY:
        print("❌ Error: MinIO credentials missing in .env.local")
        return None
    return Minio(
        ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=True
    )

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

def normalize_name(name: str) -> str:
    """Decode, transliterate and replace spaces with underscores."""
    name = urllib.parse.unquote(name)
    name = transliterate(name)
    name = name.replace(' ', '_')
    name = re.sub(r'_{2,}', '_', name)
    return name

def get_existing_markdown_folders(client):
    """Fetch all folder names under markdown/ prefix."""
    print("[Discovery] Fetching existing markdown folders from MinIO...")
    folders = set()
    objects = client.list_objects(BUCKET_NAME, prefix='markdown/', recursive=False)
    for obj in objects:
        if obj.is_dir:
            # obj.object_name is 'markdown/folder_name/'
            folder_name = obj.object_name.strip('/').split('/')[-1]
            folders.add(folder_name)
    return folders

def convert_pdfs_to_md(filename_filter=None):
    client = get_minio_client()
    if not client: return

    print(f"--- MinIO PDF to Markdown Conversion Agent ---")
    print(f"Bucket: {BUCKET_NAME}")
    
    # 1. Get existing markdown folders for comparison
    existing_folders = get_existing_markdown_folders(client)
    print(f"[Discovery] Found {len(existing_folders)} existing markdown folders.")

    # 2. List all PDF objects in the 'pdfs/' prefix
    objects = client.list_objects(BUCKET_NAME, prefix='pdfs/', recursive=True)
    pdf_objects = [obj for obj in objects if obj.object_name.lower().endswith('.pdf')]
    
    if filename_filter:
        pdf_objects = [obj for obj in pdf_objects if filename_filter in obj.object_name]
        
    print(f"[Discovery] Found {len(pdf_objects)} PDF files in storage.")

    # 3. Filter PDFs that are missing from markdown/
    missing_pdfs = []
    for obj in pdf_objects:
        base_name = os.path.basename(obj.object_name)
        name_no_ext = os.path.splitext(base_name)[0]
        normalized_name = normalize_name(name_no_ext)
        
        if normalized_name not in existing_folders:
            missing_pdfs.append((obj, normalized_name))

    print(f"[Discovery] {len(missing_pdfs)} PDFs need conversion.")

    # 4. Process missing PDFs
    for i, (obj, normalized_name) in enumerate(missing_pdfs):
        full_pdf_path = obj.object_name
        base_name = os.path.basename(full_pdf_path)
        
        target_md_path = f"markdown/{normalized_name}/{normalized_name}.md"

        print(f"\n[Process {i+1}/{len(missing_pdfs)}] {base_name} -> {target_md_path}")

        # Download to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
            tmp_pdf_path = tmp_pdf.name
            try:
                print(f"[Download] Fetching PDF...")
                client.fget_object(BUCKET_NAME, full_pdf_path, tmp_pdf_path)

                # Convert to Markdown
                print(f"[Convert] Converting to Markdown...")
                md_content = pymupdf4llm.to_markdown(tmp_pdf_path)

                # Upload resulting Markdown
                with tempfile.NamedTemporaryFile(mode='w', suffix=".md", delete=False, encoding='utf-8') as tmp_md:
                    tmp_md_path = tmp_md.name
                    tmp_md.write(md_content)
                
                print(f"[Upload] Saving...")
                client.fput_object(BUCKET_NAME, target_md_path, tmp_md_path, content_type='text/markdown')
                
                print(f"✅ Success.")
                os.remove(tmp_md_path)

            except Exception as e:
                print(f"❌ Error processing {base_name}: {str(e)}")
            finally:
                if os.path.exists(tmp_pdf_path):
                    os.remove(tmp_pdf_path)

if __name__ == "__main__":
    f_filter = sys.argv[1] if len(sys.argv) > 1 else None
    convert_pdfs_to_md(f_filter)
    print("\n--- Conversion Agent Completed ---")

# ── Команди запуску ────────────────────────────────────────────────────────────
#
# Обробити всі нові PDF-файли (яких немає у папці markdown):
#   python3 agents/convert_pdfs_to_md.py
#
# Обробити конкретний файл за назвою (або частиною назви):
#   python3 agents/convert_pdfs_to_md.py Daigest_VP_03_2026
