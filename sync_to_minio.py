import os
import glob
from minio import Minio
from dotenv import load_dotenv

BASE_DIR = '/Users/kostantinkrivula/Desktop/sqlbase/skill_for_digest'
load_dotenv(dotenv_path=os.path.join(BASE_DIR, '.env.local'))

ENDPOINT = os.getenv('MINIO_ENDPOINT', 'minio.lexis.blog').replace('https://', '').replace('http://', '').rstrip('/')
ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
BUCKET_NAME = os.getenv('MINIO_BUCKET', 'court-documents')

def get_client():
    return Minio(ENDPOINT, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=True)

def sync_folder_to_minio(client, local_folder, minio_prefix):
    print(f"\n==================================================")
    print(f"Syncing local folder: {local_folder} -> MinIO prefix: {minio_prefix}/")
    print(f"==================================================")
    
    # 1. List existing objects on MinIO under this prefix
    print("Fetching existing objects list from MinIO...")
    existing_objects = {}
    try:
        objs = client.list_objects(BUCKET_NAME, prefix=f"{minio_prefix}/", recursive=True)
        for o in objs:
            existing_objects[o.object_name] = o.size
        print(f"Found {len(existing_objects)} existing objects on MinIO under '{minio_prefix}/'.")
    except Exception as e:
        print(f"Warning fetching existing objects: {e}")

    # 2. Walk local folder
    local_files = []
    for root, dirs, files in os.walk(local_folder):
        for f in files:
            if f.startswith('.') or f.endswith('.DS_Store'):
                continue
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, local_folder)
            local_files.append((full_path, rel_path))

    print(f"Found {len(local_files)} local files to sync.")

    uploaded = 0
    skipped = 0
    errors = 0

    for idx, (full_path, rel_path) in enumerate(local_files):
        object_name = f"{minio_prefix}/{rel_path}".replace('\\', '/')
        local_size = os.path.getsize(full_path)

        # Check if identical already exists
        if object_name in existing_objects and existing_objects[object_name] == local_size:
            skipped += 1
            continue

        try:
            client.fput_object(BUCKET_NAME, object_name, full_path)
            uploaded += 1
            if uploaded % 25 == 0 or (idx + 1) == len(local_files):
                print(f"[{idx+1}/{len(local_files)}] Uploaded: {object_name} ({local_size} bytes)")
        except Exception as e:
            errors += 1
            print(f"❌ Error uploading {object_name}: {e}")

    print(f"\nSummary for '{minio_prefix}': Uploaded {uploaded}, Skipped (up-to-date) {skipped}, Errors {errors}")

def main():
    print(f"Connecting to MinIO: {ENDPOINT}, bucket: {BUCKET_NAME}")
    client = get_client()

    # 1. Sync agents/markdown -> markdown/
    local_md = os.path.join(BASE_DIR, 'agents', 'markdown')
    sync_folder_to_minio(client, local_md, 'markdown')

    # 2. Sync agents/pdfs -> pdfs/
    local_pdfs = os.path.join(BASE_DIR, 'agents', 'pdfs')
    sync_folder_to_minio(client, local_pdfs, 'pdfs')

    print("\n==================================================")
    print("ALL SYNC OPERATIONS COMPLETED SUCCESSFULLY!")
    print("==================================================")

if __name__ == '__main__':
    main()
