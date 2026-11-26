import hashlib
import io
import tempfile
from pathlib import Path

import pymupdf
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from platform_app.checker import check_pdf
from platform_app.models import Submission
from platform_app.jobs import seed_profile
from tests.test_platform import sample_pdf


class ReviewViewerTests(TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.settings_override=override_settings(MEDIA_ROOT=self.temp.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.addCleanup(self.temp.cleanup)
        self.owner=User.objects.create_user('viewer_owner')
        self.other=User.objects.create_user('viewer_other')
        data=sample_pdf(40,'en')
        with pymupdf.open(stream=data,filetype='pdf') as doc:
            doc[32].insert_text((85,360),'This unique paragraph on page thirty three has a colour error.',
                fontname='tiro',fontsize=14,color=(1,0,0))
            self.original=doc.tobytes()
        self.job=Submission(owner=self.owner,title='Synthetic page33',language='en',duration='1',profile=seed_profile().snapshot())
        self.job.file.save('synthetic33.pdf',ContentFile(self.original),save=False)
        self.job.save()
        self.job.result=check_pdf(self.job.file.path,language='en',profile=self.job.profile)
        self.job.status='done';self.job.save()
        self.client.force_login(self.owner)

    def test_viewer_page33_and_highlighted_pixels_keep_original_unchanged(self):
        response=self.client.get(f'/work/{self.job.pk}/viewer/?page=33')
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'page=33')
        image=self.client.get(f'/work/{self.job.pk}/page-image/?page=33')
        self.assertEqual(image.status_code,200)
        self.assertEqual(image['Content-Type'],'image/png')
        pix=pymupdf.Pixmap(image.content)
        self.assertLessEqual(pix.width*pix.height,3_000_000)
        samples=pix.samples
        self.assertTrue(any(samples[i]>220 and samples[i+1]>190 and samples[i+2]<180
            for i in range(0,len(samples),pix.n)))
        self.assertEqual(hashlib.sha256(Path(self.job.file.path).read_bytes()).digest(),hashlib.sha256(self.original).digest())
        self.assertIn('no-store',image['Cache-Control'])

    def test_private_routes_and_invalid_page_selection(self):
        for suffix in ('viewer/?page=33','page-image/?page=33'):
            self.client.force_login(self.other)
            self.assertEqual(self.client.get(f'/work/{self.job.pk}/'+suffix).status_code,404)
            self.client.force_login(self.owner)
        for query in ('page=0','page=41','page=oops','page=33&finding=oops','page=33&finding=99999'):
            self.assertEqual(self.client.get(f'/work/{self.job.pk}/page-image/?'+query).status_code,400)

    def test_revision_owner_link_and_foreign_parent_denial(self):
        response=self.client.get(f'/upload/?previous={self.job.pk}')
        self.assertEqual(response.status_code,200)
        self.assertContains(response,str(self.job.pk))
        response=self.client.post('/upload/',{'previous':str(self.job.pk),'title':'Corrected synthetic',
            'language':'en','duration':'1','file':ContentFile(sample_pdf(40,'en'),name='corrected.pdf')})
        self.assertEqual(response.status_code,302)
        revision=Submission.objects.exclude(pk=self.job.pk).get()
        self.assertEqual(revision.previous_id,self.job.pk)
        self.client.force_login(self.other)
        response=self.client.post('/upload/',{'previous':str(self.job.pk),'title':'Foreign',
            'language':'en','duration':'1','file':ContentFile(sample_pdf(40,'en'),name='foreign.pdf')})
        self.assertEqual(response.status_code,404)
        self.assertEqual(Submission.objects.count(),2)
