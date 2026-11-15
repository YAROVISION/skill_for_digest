import os
from minio import Minio
from dotenv import load_dotenv

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(dotenv_path=os.path.join(base_dir, '.env.local'))

    endpoint_raw = os.getenv('MINIO_ENDPOINT', 'minio.lexis.blog')
    endpoint = endpoint_raw.replace('https://', '').replace('http://', '').rstrip('/')
    access_key = os.getenv('MINIO_ACCESS_KEY')
    secret_key = os.getenv('MINIO_SECRET_KEY')
    bucket_name = os.getenv('MINIO_BUCKET', 'court-documents')

    target_dir = os.path.join(base_dir, 'agents', 'markdown')
    os.makedirs(target_dir, exist_ok=True)

    print(f"Connecting to MinIO endpoint: {endpoint}")
    print(f"Bucket: {bucket_name}")
    print(f"Destination folder: {target_dir}")

    client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=True)

    prefix = 'markdown/'
    print(f"Listing objects with prefix: {prefix}")
    
    objects = list(client.list_objects(bucket_name, prefix=prefix, recursive=True))
    total_objects = len(objects)
    print(f"Found {total_objects} objects in MinIO.")

    downloaded = 0
    skipped = 0

    for obj in objects:
        object_name = obj.object_name
        # Get path relative to prefix
        rel_path = object_name[len(prefix):] if object_name.startswith(prefix) else object_name
        if not rel_path or rel_path.endswith('/'):
            continue  # Directory marker object

        local_file_path = os.path.join(target_dir, rel_path)
        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

        print(f"[{downloaded + 1}/{total_objects}] Downloading {object_name} -> {local_file_path} ({obj.size} bytes)")
        client.fget_object(bucket_name, object_name, local_file_path)
        downloaded += 1

    print(f"\nSuccessfully downloaded {downloaded} files into {target_dir}")

if __name__ == '__main__':
    main()
