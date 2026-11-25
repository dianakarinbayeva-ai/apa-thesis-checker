import hashlib
import io
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.test import TestCase, SimpleTestCase, override_settings

from platform_app.jobs import process_one, seed_profile
from platform_app.models import Submission
from tests.test_platform import sample_pdf


class MemoryRemoteStorage(Storage):
    def __init__(self):
        self.objects = {}

    def _save(self, name, content):
        self.objects[name] = content.read()
        return name

    def _open(self, name, mode='rb'):
        return ContentFile(self.objects[name], name=name)

    def exists(self, name):
        return name in self.objects

    def delete(self, name):
        self.objects.pop(name, None)


class CloudProcessingTests(TestCase):
    def test_admin_displays_private_filename_without_public_url(self):
        admin = User.objects.create_superuser('cloud_admin', password='Safe!Admin2026')
        storage = MemoryRemoteStorage()
        with patch.object(Submission._meta.get_field('file'), 'storage', storage):
            job = Submission.objects.create(owner=admin,title='Private admin test',language='kk',duration='1',
                profile=seed_profile().snapshot(),file='documents/synthetic.pdf')
            self.client.force_login(admin)
            response = self.client.get(f'/admin/platform_app/submission/{job.pk}/change/')
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'documents/synthetic.pdf')

    def test_database_failure_removes_uploaded_object(self):
        from django.db import DatabaseError
        self.client.force_login(User.objects.create_user('failure_student'))
        storage = MemoryRemoteStorage()
        with patch.object(Submission._meta.get_field('file'), 'storage', storage), \
                patch.object(Submission, 'save', side_effect=DatabaseError('synthetic failure')):
            response=self.client.post('/upload/',{'title':'Synthetic','language':'en','duration':'1',
                'file':ContentFile(b'%PDF-synthetic',name='synthetic.pdf')})
        self.assertEqual(response.status_code,200)
        self.assertEqual(storage.objects,{})
        self.assertEqual(Submission.objects.count(),0)

    def test_worker_processes_private_storage_without_local_path(self):
        storage = MemoryRemoteStorage()
        with patch.object(Submission._meta.get_field('file'), 'storage', storage):
            user = User.objects.create_user('cloud_student', password='Safe!Test2026')
            data = sample_pdf(pages=40, language='kk')
            job = Submission(owner=user, title='Synthetic', language='kk', duration='1', profile=seed_profile().snapshot())
            job.file.save('synthetic.pdf', ContentFile(data), save=False)
            job.save()
            self.assertTrue(process_one())
            job.refresh_from_db()
            self.assertEqual(job.status, 'done')
            self.assertEqual(job.result['original_sha256'], hashlib.sha256(data).hexdigest())
            with job.file.open('rb') as original:
                self.assertEqual(original.read(), data)

    def test_storage_upload_failure_is_localized_and_creates_no_job(self):
        self.client.force_login(User.objects.create_user('storage_student'))
        with patch('django.core.files.storage.filesystem.FileSystemStorage._save', side_effect=OSError('offline')):
            response = self.client.post('/upload/', {'title':'Synthetic', 'language':'en', 'duration':'1',
                'file':ContentFile(b'%PDF-synthetic', name='synthetic.pdf')})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Submission.objects.count(), 0)
        from platform_app.i18n import TEXT
        self.assertContains(response, TEXT['kk']['storage_unavailable'])


class CloudConfigurationTests(SimpleTestCase):
    def test_database_url_uses_private_schema_and_tls(self):
        try:
            from platform_config.cloud import database_from_url
        except ImportError:
            self.fail('Cloud database configuration is not implemented')
        db = database_from_url('postgresql://apa.ref:pass%21@aws-1-eu-central-1.pooler.supabase.com:5432/postgres')
        self.assertEqual(db['PASSWORD'], 'pass!')
        self.assertEqual(db['USER'], 'apa.ref')
        self.assertEqual(db['OPTIONS']['sslmode'], 'require')
        self.assertIn('search_path=apa_private', db['OPTIONS']['options'])
        with self.assertRaises(ValueError):
            database_from_url('sqlite:///tmp/public.sqlite')

    def test_cloud_configuration_rejects_missing_durable_storage(self):
        try:
            from platform_config.cloud import validate_cloud_environment
        except ImportError:
            self.fail('Fail-closed cloud configuration is not implemented')
        with self.assertRaises(ValueError):
            validate_cloud_environment({'APA_CLOUD':'1'})
        with self.assertRaises(ValueError):
            validate_cloud_environment({'DATABASE_URL':'postgresql://a:b@host/db',
                'DJANGO_SECRET_KEY':'secret', 'APA_STORAGE_ENDPOINT':'http://public.example',
                'APA_STORAGE_TOKEN':'token', 'APA_HTTPS':'1'})

    def test_cloud_storage_rejects_traversal(self):
        from platform_app.private_storage import PrivateCloudStorage
        for name in ('../secret.pdf','a/../secret.pdf','/secret.pdf','a\\secret.pdf','secret.txt'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                PrivateCloudStorage.safe_name(name)
