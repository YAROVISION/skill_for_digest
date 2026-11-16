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

LIST_FILE = os.path.join(os.path.dirname(__file__), 'lists', 'list_of_markdown.md')
MISSING_LIST_FILE = os.path.join(os.path.dirname(__file__), 'lists', 'list_of_missing_markdownfiles.md')

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
            folder_name = obj.object_name.strip('/').split('/')[-1]
            folders.add(folder_name)
    return folders

def append_to_list(filename):
    """Append a new file name to the markdown list."""
    with open(LIST_FILE, 'a', encoding='utf-8') as f:
        f.write(f'- {filename}\n')

def update_missing_list(missing_pdfs):
    """Rewrite the missing markdown list file."""
    with open(MISSING_LIST_FILE, 'w', encoding='utf-8') as f:
        f.write("# List of PDFs missing corresponding Markdown folders\n\n")
        for obj, norm_name in missing_pdfs:
            f.write(f"- {os.path.basename(obj.object_name)}\n")

def convert_pdfs_to_md(filename_filter=None):
    client = get_minio_client()
    if not client: return

    print(f"--- MinIO PDF to Markdown Conversion Agent ---")
    
    existing_folders = get_existing_markdown_folders(client)
    
    objects = client.list_objects(BUCKET_NAME, prefix='pdfs/', recursive=True)
    pdf_objects = [obj for obj in objects if obj.object_name.lower().endswith('.pdf')]
    
    if filename_filter:
        pdf_objects = [obj for obj in pdf_objects if filename_filter in obj.object_name]
        
    missing_pdfs = []
    for obj in pdf_objects:
        base_name = os.path.basename(obj.object_name)
        if base_name.lower().startswith('zved_oglyad'):
            continue
            
        name_no_ext = os.path.splitext(base_name)[0]
        normalized_name = normalize_name(name_no_ext)
        
        if normalized_name not in existing_folders:
            missing_pdfs.append((obj, normalized_name))

    print(f"[Discovery] {len(missing_pdfs)} PDFs need conversion.")
    update_missing_list(missing_pdfs)
    
    try:
        client.fput_object(BUCKET_NAME, "lists/list_of_missing_markdownfiles.md", MISSING_LIST_FILE, content_type='text/markdown')
    except Exception as e:
        print(f"⚠️ Failed to upload missing list: {e}")

    converted_count = 0
    for i, (obj, normalized_name) in enumerate(missing_pdfs):
        full_pdf_path = obj.object_name
        base_name = os.path.basename(full_pdf_path)
        target_md_path = f"markdown/{normalized_name}/{normalized_name}.md"

        print(f"\n[Process {i+1}/{len(missing_pdfs)}] {base_name} -> {target_md_path}")

        tmp_pdf_path = None
        tmp_md_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
                tmp_pdf_path = tmp_pdf.name
                client.fget_object(BUCKET_NAME, full_pdf_path, tmp_pdf_path)
            
            md_content = pymupdf4llm.to_markdown(tmp_pdf_path)

            # Save locally to agents/markdown/{normalized_name}/{normalized_name}.md
            local_md_dir = os.path.join(os.path.dirname(__file__), 'markdown', normalized_name)
            os.makedirs(local_md_dir, exist_ok=True)
            local_md_path = os.path.join(local_md_dir, f"{normalized_name}.md")
            with open(local_md_path, 'w', encoding='utf-8') as local_f:
                local_f.write(md_content)

            with tempfile.NamedTemporaryFile(mode='w', suffix=".md", delete=False, encoding='utf-8') as tmp_md:
                tmp_md_path = tmp_md.name
                tmp_md.write(md_content)
            
            client.fput_object(BUCKET_NAME, target_md_path, tmp_md_path, content_type='text/markdown')
            print(f"✅ Success.")
            append_to_list(normalized_name)
            converted_count += 1
        except Exception as e:
            print(f"❌ Error processing {base_name}: {str(e)}")
        finally:
            if tmp_pdf_path and os.path.exists(tmp_pdf_path):
                os.remove(tmp_pdf_path)
            if tmp_md_path and os.path.exists(tmp_md_path):
                os.remove(tmp_md_path)

    if converted_count > 0:
        try:
            client.fput_object(BUCKET_NAME, "lists/list_of_markdown.md", LIST_FILE, content_type='text/markdown')
            print("✅ Remote success list updated.")
        except Exception as e:
            print(f"⚠️ Failed to update remote list: {e}")

if __name__ == "__main__":
    f_filter = sys.argv[1] if len(sys.argv) > 1 else None
    convert_pdfs_to_md(f_filter)
    print("\n--- Conversion Agent Completed ---")
