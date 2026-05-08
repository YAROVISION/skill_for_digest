import os
from minio import Minio
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env.local')

ENDPOINT = os.getenv('MINIO_ENDPOINT', '').replace('https://', '').replace('http://', '')
ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
BUCKET_NAME = os.getenv('MINIO_BUCKET', 'court-documents')

print(f"Connecting to: {ENDPOINT}")
print(f"Bucket: {BUCKET_NAME}")

try:
    client = Minio(ENDPOINT, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=True)
    objects = client.list_objects(BUCKET_NAME, prefix='markdown/', recursive=True)
    count = 0
    for obj in objects:
        print(f"Found: {obj.object_name}")
        count += 1
        if count >= 3: break
    print(f"Connection successful! Found {count} files (limit 3 for test).")
except Exception as e:
    print(f"Connection failed: {str(e)}")
