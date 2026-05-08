import os
from minio import Minio
from dotenv import load_dotenv

class MinioStorage:
    def __init__(self):
        load_dotenv()
        load_dotenv(dotenv_path='.env.local', override=True)
        
        self.endpoint = os.getenv('MINIO_ENDPOINT', '').replace('https://', '').replace('http://', '')
        self.access_key = os.getenv('MINIO_ACCESS_KEY')
        self.secret_key = os.getenv('MINIO_SECRET_KEY')
        self.bucket_name = os.getenv('MINIO_BUCKET', 'court-documents')
        
        if not all([self.endpoint, self.access_key, self.secret_key]):
            raise ValueError("MinIO credentials are not fully set in .env or .env.local")
            
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=True
        )

    def list_markdown_files(self, prefix='markdown/'):
        objects = self.client.list_objects(self.bucket_name, prefix=prefix, recursive=True)
        md_files = [obj for obj in objects if obj.object_name.endswith('.md')]
        md_files.sort(key=lambda x: x.object_name, reverse=True)
        return md_files

    def get_processed_slugs(self, prefix='structured/'):
        processed_slugs = set()
        try:
            st_objs = self.client.list_objects(self.bucket_name, prefix=prefix, recursive=True)
            for o in st_objs:
                parts = o.object_name.split('/')
                if len(parts) >= 2:
                    processed_slugs.add(parts[1])
        except Exception as e:
            print(f"⚠️ Could not fetch existing docs: {e}")
        return processed_slugs

    def get_existing_ids(self, doc_slug):
        existing_ids = set()
        try:
            existing_jsons = self.client.list_objects(self.bucket_name, prefix=f"structured/{doc_slug}/", recursive=True)
            for o in existing_jsons:
                existing_ids.add(os.path.basename(o.object_name))
        except:
            pass
        return existing_ids

    def get_object_content(self, object_name):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp_md:
            self.client.fget_object(self.bucket_name, object_name, tmp_md.name)
            with open(tmp_md.name, 'r', encoding='utf-8') as f:
                content = f.read()
        os.remove(tmp_md.name)
        return content

    def save_structured_json(self, doc_slug, article_id, structured_data):
        import json
        import tempfile
        target_minio_path = f"structured/{doc_slug}/{article_id}.json"
        local_dir = f"documents/structured/{doc_slug}"
        local_path = f"{local_dir}/{article_id}.json"
        
        os.makedirs(local_dir, exist_ok=True)
        with open(local_path, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, ensure_ascii=False, indent=2)
            
        self.client.fput_object(self.bucket_name, target_minio_path, local_path, content_type='application/json')
        return target_minio_path
