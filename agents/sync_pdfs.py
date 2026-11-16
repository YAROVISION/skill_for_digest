"""Bidirectional synchronization between MinIO `pdfs/` and local `agents/pdfs/`."""

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from tools.storage_tools import MinioStorage

LOCAL_PDFS_DIR = os.path.join(ROOT_DIR, "agents", "pdfs")


def sync_pdfs():
    os.makedirs(LOCAL_PDFS_DIR, exist_ok=True)
    storage = MinioStorage()
    client = storage.client
    bucket = storage.bucket_name

    print(f"=== Bidirectional PDF Sync (MinIO: {bucket}/pdfs/ <-> {LOCAL_PDFS_DIR}) ===")

    # 1. Fetch MinIO PDF objects
    minio_objects = {}
    for obj in client.list_objects(bucket, prefix="pdfs/", recursive=True):
        if obj.object_name.lower().endswith(".pdf"):
            name = os.path.basename(obj.object_name)
            minio_objects[name] = obj

    # 2. Fetch local PDFs
    local_files = {}
    for entry in os.listdir(LOCAL_PDFS_DIR):
        full_path = os.path.join(LOCAL_PDFS_DIR, entry)
        if os.path.isfile(full_path) and entry.lower().endswith(".pdf"):
            local_files[entry] = os.path.getsize(full_path)

    print(f"[Discovery] MinIO: {len(minio_objects)} PDFs | Local: {len(local_files)} PDFs")

    uploaded = 0
    downloaded = 0
    errors = 0

    # 3. Upload local -> MinIO
    for name, local_size in sorted(local_files.items()):
        if name not in minio_objects or minio_objects[name].size != local_size:
            local_path = os.path.join(LOCAL_PDFS_DIR, name)
            target_obj = f"pdfs/{name}"
            try:
                client.fput_object(
                    bucket, target_obj, local_path, content_type="application/pdf"
                )
                uploaded += 1
                print(f"[Upload -> MinIO] {name} ({local_size} bytes)")
            except Exception as e:
                errors += 1
                print(f"❌ Upload error ({name}): {e}")

    # 4. Download MinIO -> local
    for name, obj in sorted(minio_objects.items()):
        if name not in local_files:
            local_path = os.path.join(LOCAL_PDFS_DIR, name)
            try:
                client.fget_object(bucket, obj.object_name, local_path)
                downloaded += 1
                print(f"[Download -> Local] {name} ({obj.size} bytes)")
            except Exception as e:
                errors += 1
                print(f"❌ Download error ({name}): {e}")

    print(f"\n--- Sync Completed: Uploaded={uploaded}, Downloaded={downloaded}, Errors={errors} ---")


if __name__ == "__main__":
    sync_pdfs()
