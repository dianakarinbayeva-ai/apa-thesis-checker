import hashlib
import io
import json
import tempfile
import zipfile
from pathlib import Path

import pymupdf as fitz
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, SimpleTestCase, override_settings
from django.utils import timezone
from datetime import timedelta

from platform_app.checker import check_pdf, parse_pdf_pages, PDFError
from platform_app.i18n import TEXT, finding_text
from platform_app.jobs import process_one, seed_profile
from platform_app.models import Submission
from platform_app.source_bundle import source_archive

FONT = Path(__file__).resolve().parent.parent / 'platform_app/assets/NotoSans-Regular.ttf'


def sample_pdf(pages=40, language='en', bad_size=False, font_size=14, appendix=False, bad_numbers=False):
    labels = {
        'en': ('Contents','Introduction','Conclusion','References','Appendix 1'),
        'ru': ('Содержание','Введение','Заключение','Список использованных источников','Приложение 1'),
        'kk': ('Мазмұны','Кіріспе','Қорытынды','Пайдаланылған әдебиеттер тізімі','Қосымша 1'),
    }[language]
    doc = fitz.open()
    for index in range(pages):
        page=doc.new_page(width=620 if bad_size else 595.28,height=841.89)
        page.insert_font(fontname='noto',fontfile=str(FONT))
        heading = {1:labels[0],2:labels[1],pages-3:labels[2],pages-2:labels[3]}.get(index)
        if index == pages-1 and appendix:
            heading=labels[4]
        if heading:
            page.insert_text((85,75),heading,fontname='noto',fontsize=14)
        for row in range(8):
            page.insert_text((85,110+row*16),'Academic research examines public administration [1].',fontname='tiro',fontsize=font_size)
        if index:
            number=str(index+1+(3 if bad_numbers else 0))
            page.insert_text((294,815),number,fontname='noto',fontsize=10)
    result=doc.tobytes(garbage=4,deflate=True)
    doc.close()
    return result


class EngineTests(SimpleTestCase):
    def check(self, data, **kwargs):
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/'input.pdf';file.write_bytes(data)
            return check_pdf(file,**kwargs)

    def test_three_languages_and_hash(self):
        for language in ('kk','ru','en'):
            with self.subTest(language=language):
                data=sample_pdf(language=language)
                result=self.check(data,language=language)
                self.assertEqual(result['original_sha256'],hashlib.sha256(data).hexdigest())
                sections=[f for f in result['findings'] if f['rule_id']=='R_STRUCTURE']
                self.assertTrue(all(f['status']=='pass' for f in sections))
                self.assertNotIn('manual',result['counts'])
                self.assertEqual(sum(result['counts'].values()),len(result['findings']))
                for rule in ('R_SIZE','R_LENGTH','R_FONT','R_COLOR','R_NUMBER','R_SPACING'):
                    self.assertTrue(any(f['rule_id']==rule and f['status']=='pass' for f in result['findings']),rule)

    def test_length_boundaries_and_appendices(self):
        for pages,duration,expected in [(39,'1','fail'),(40,'1','pass'),(59,'1.5','fail'),(60,'1.5','pass'),(60,'2','pass')]:
            with self.subTest(pages=pages,duration=duration):
                result=self.check(sample_pdf(pages),duration=duration)
                self.assertEqual(next(f for f in result['findings'] if f['rule_id']=='R_LENGTH')['status'],expected)
        result=self.check(sample_pdf(40,appendix=True))
        self.assertEqual(result['body_pages'],39)
        self.assertEqual(result['appendix_start'],40)

    def test_size_font_and_page_number_violations(self):
        result=self.check(sample_pdf(5,bad_size=True,font_size=18,bad_numbers=True))
        for rid in ['R_SIZE','R_FONT','R_NUMBER']:
            self.assertTrue(any(f['rule_id']==rid and f['status']=='fail' for f in result['findings']),rid)

    def test_corrupt_scan_encryption_and_limits(self):
        with self.assertRaisesRegex(PDFError,'bad_pdf'):
            self.check(b'%PDF-broken')
        doc=fitz.open();doc.new_page()
        with self.assertRaisesRegex(PDFError,'scan'):
            self.check(doc.tobytes())
        with self.assertRaisesRegex(PDFError,'encrypted'):
            self.check(doc.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256,owner_pw='owner',user_pw='private'))
        doc.close()
        doc=fitz.open()
        for _ in range(301):doc.new_page()
        with self.assertRaisesRegex(PDFError,'too_many_pages'):
            self.check(doc.tobytes())
        doc.close()

    def test_translation_keys_complete(self):
        for language, values in TEXT.items():
            self.assertEqual(set(values),set(TEXT['en']))
            self.assertTrue(all(values.values()))
            self.assertNotIn('Ручная',str(values))


class WebTests(TestCase):
    def setUp(self):
        cache.clear()
        self.temp=tempfile.TemporaryDirectory()
        self.setting=override_settings(MEDIA_ROOT=self.temp.name)
        self.setting.enable()
        self.user=User.objects.create_user(username='student_one',password='Secure!Academic2026')
        self.other=User.objects.create_user(username='student_two',password='Secure!Academic2027')
        self.client.force_login(self.user)
        seed_profile()

    def tearDown(self):
        self.setting.disable();self.temp.cleanup()

    def submit(self):
        response=self.client.post('/upload/',{'title':'Test thesis','language':'kk','duration':'1',
            'file':SimpleUploadedFile('thesis.pdf',sample_pdf(4,'kk'),content_type='application/pdf')})
        self.assertEqual(response.status_code,302)
        return Submission.objects.get(owner=self.user)

    def test_full_upload_process_report_history_and_ownership(self):
        job=self.submit()
        self.assertEqual(job.status,'queued')
        self.assertTrue(process_one())
        self.assertFalse(process_one())
        job.refresh_from_db();self.assertEqual(job.status,'done')
        for url in ['/', '/history/',f'/work/{job.pk}/','/guide/']:
            self.assertEqual(self.client.get(url).status_code,200)
        response=self.client.get(f'/work/{job.pk}/download/json/')
        self.assertEqual(response.status_code,200)
        self.assertEqual(json.loads(response.content)['original_sha256'],job.result['original_sha256'])
        for language in ['kk','ru','en']:
            self.client.post('/language/',{'language':language})
            report=self.client.get(f'/work/{job.pk}/download/pdf/')
            self.assertEqual(report.status_code,200)
            doc=fitz.open(stream=report.content,filetype='pdf')
            self.assertTrue(len(doc)>0)
            self.assertIn(TEXT[language]['report'],doc[0].get_text())
            doc.close()
        self.client.force_login(self.other)
        for ending in ['', 'status/','download/pdf/','download/json/','download/original/']:
            self.assertEqual(self.client.get(f'/work/{job.pk}/{ending}').status_code,404)
        self.assertEqual(self.client.post(f'/work/{job.pk}/delete/').status_code,404)
        self.client.force_login(self.user)
        path=Path(job.file.path)
        self.client.post(f'/work/{job.pk}/delete/')
        self.assertFalse(path.exists())
        self.assertFalse(Submission.objects.filter(pk=job.pk).exists())

    def test_invalid_file_has_localised_error(self):
        self.client.post('/language/',{'language':'ru'})
        response=self.client.post('/upload/',{'title':'bad','language':'ru','duration':'1',
            'file':SimpleUploadedFile('bad.pdf',b'not-pdf')})
        self.assertContains(response,TEXT['ru']['bad_pdf'])
        self.assertEqual(Submission.objects.count(),0)

    def test_failed_job_and_stale_recovery(self):
        job=self.submit()
        Path(job.file.path).write_bytes(b'%PDF-broken')
        process_one();job.refresh_from_db()
        self.assertEqual((job.status,job.error_code),('failed','bad_pdf'))
        job.status='processing';job.started_at=timezone.now()-timedelta(minutes=15);job.save()
        process_one();job.refresh_from_db()
        self.assertEqual((job.status,job.error_code),('failed','timeout'))

    def test_auth_csrf_and_language_persistence(self):
        from django.test import Client
        csrf=Client(enforce_csrf_checks=True)
        self.assertEqual(csrf.post('/register/',{}).status_code,403)
        self.client.post('/language/',{'language':'en','next':'https://evil.invalid'})
        self.assertEqual(self.client.get('/guide/')['Content-Language'],'en')
        self.assertEqual(self.client.post('/logout/').status_code,302)
        self.assertEqual(self.client.get('/login/')['Content-Language'],'en')
        self.assertEqual(self.client.get('/history/').status_code,302)
        result=self.client.post('/register/',{'username':'new_student','password':'Unique!Study2026','password2':'Unique!Study2026'})
        self.assertEqual(result.status_code,302)
        self.assertTrue(User.objects.filter(username='new_student').exists())

    def test_source_archive_excludes_data_and_credentials(self):
        archive=zipfile.ZipFile(io.BytesIO(source_archive()))
        names=archive.namelist()
        self.assertIn('LICENSE',names)
        self.assertIn('vendor/tsinghua/LICENSE',names)
        self.assertIn('platform_app/checker.py',names)
        self.assertTrue(all(not any(p in name.split('/') for p in ['data','.env','.git','__pycache__']) for name in names))
        self.assertEqual(self.client.get('/source/').status_code,200)
