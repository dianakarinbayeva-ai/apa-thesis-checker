import io
import json
import tempfile
from pathlib import Path

from django.apps import apps
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase

from platform_app.models import Submission
from platform_app.checker import DEFAULT_PROFILE


def complete_result(state='pass'):
    from platform_app.checker import REGISTRY
    from collections import Counter
    findings=[{'rule_id':rule[0], 'status':state if index==0 else 'pass', 'method':'geometry',
               'message':'observed', 'evidence':'Synthetic evidence', 'page':1,
               'clause':str(rule[1]), 'source_url':'https://www.apa.kz/'} for index,rule in enumerate(REGISTRY)]
    counts=Counter(f['status'] for f in findings)
    return {'findings':findings,'counts':{key:counts[key] for key in ['pass','fail','uncertain','na']},
            'page_count':40,'body_pages':40,'original_sha256':'0'*64}


class CuratorTests(TestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user('curator_admin', password='Strong!Curator2026', is_staff=True)

    def models(self):
        return apps.get_model('platform_app', 'StudyGroup'), apps.get_model('platform_app', 'RosterStudent')

    def group(self, code='test-1'):
        Group, _ = self.models()
        return Group.objects.create(code=code, programme='Test Programme', programme_code='TEST',
                                    group_number=1, intake='winter', year=2025, roster_loaded=True)

    def test_staff_can_open_curator_dashboard(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get('/curator/').status_code, 200)

    def test_student_and_unassigned_curator_cannot_read_rosters(self):
        _, Student = self.models()
        own, other = self.group(), self.group('test-2')
        curator = User.objects.create_user('assigned_curator')
        own.curators.add(curator)
        Student.objects.create(group=other, position=1, full_name='Synthetic Private Student')
        self.client.force_login(curator)
        self.assertEqual(self.client.get(f'/curator/group/{own.pk}/').status_code, 200)
        self.assertEqual(self.client.get(f'/curator/group/{other.pk}/').status_code, 404)
        student = User.objects.create_user('ordinary_student')
        self.client.force_login(student)
        self.assertEqual(self.client.get('/curator/').status_code, 403)
        self.assertEqual(self.client.get(f'/curator/group/{other.pk}/').status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get('/curator/').status_code, 302)
        for path in ['/', '/register/', '/source/']:
            r = self.client.get(path)
            self.assertNotIn(b'Synthetic Private Student', r.content)

    def test_latest_result_and_remaining_counts(self):
        from platform_app.curator import group_overview
        _, Student = self.models()
        group = self.group()
        Student.objects.create(group=group, position=1, full_name='Synthetic Unregistered')
        for pos, state in enumerate(['empty', 'pass', 'fail', 'uncertain', 'queued', 'failed', 'malformed'], 2):
            user = User.objects.create_user(f'count_student_{pos}')
            Student.objects.create(group=group, position=pos, full_name=f'Synthetic Student {pos}', user=user)
            if state == 'empty':
                continue
            result = complete_result(state if state in ['pass','fail','uncertain'] else 'pass')
            job = Submission.objects.create(owner=user, title='Synthetic', file='synthetic.pdf', language='kk',
                    duration='1', profile=DEFAULT_PROFILE, status=state if state in ['queued', 'failed'] else 'done', result=result)
            if state == 'malformed':
                job.result = {};job.save()
            if state == 'uncertain':
                older = Submission.objects.create(owner=user, title='Old pass', file='synthetic.pdf', language='kk',
                    duration='1', profile=DEFAULT_PROFILE, status='done', result=complete_result())
                from django.utils import timezone
                from datetime import timedelta
                Submission.objects.filter(pk=older.pk).update(created_at=timezone.now()-timedelta(days=1))
        overview = group_overview(group)
        self.assertEqual(overview['total'], 8)
        self.assertEqual(overview['registered'], 7)
        self.assertEqual(overview['uploaded'], 6)
        self.assertEqual(overview['remaining'], 2)
        self.assertEqual(overview['passed'], 1)
        self.assertEqual(overview['revision'], 1)
        self.assertEqual(overview['inconclusive'], 2)
        self.assertEqual(overview['processing'], 1)
        self.assertEqual(overview['failed'], 1)
        group.roster_loaded=False;group.save()
        self.assertIsNone(group_overview(group)['total'])

    def test_malformed_and_partial_reports_are_inconclusive_and_safe_to_open(self):
        from platform_app.curator import submission_outcome
        from platform_app.i18n import TEXT
        _, Student=self.models();group=self.group()
        owner=User.objects.create_user('malformed_owner')
        Student.objects.create(group=group,position=1,full_name='Synthetic Malformed Student',user=owner)
        job=Submission.objects.create(owner=owner,title='Malformed report',file='synthetic.pdf',language='kk',duration='1',status='done')
        self.client.force_login(self.staff)
        invalid=[[], {'findings':None}, {'findings':[{'status':'pass'}],
            'counts':{'pass':1,'fail':0,'uncertain':0,'na':0}}]
        for result in invalid:
            job.result=result;job.save()
            self.assertEqual(submission_outcome(job),'inconclusive')
            self.assertContains(self.client.get(f'/curator/work/{job.pk}/'),TEXT['kk']['invalid_report'])
            for kind in ['json','pdf']:
                self.assertEqual(self.client.get(f'/curator/work/{job.pk}/download/{kind}/').status_code,409)
        partial=complete_result();partial['findings']=partial['findings'][:1]
        partial['counts']={'pass':1,'fail':0,'uncertain':0,'na':0}
        job.result=partial
        self.assertEqual(submission_outcome(job),'inconclusive')

    def test_enrolment_code_binds_once_and_does_not_publish_names(self):
        _, Student = self.models()
        group = self.group()
        row = Student.objects.create(group=group, position=1, full_name='Synthetic Enrollee')
        data = {'username':'new_roster_student','password':'Secure!Roster2026','password2':'Secure!Roster2026',
                'full_name':'Synthetic Enrollee', 'study_group':str(group.pk),'enrollment_code':row.enrollment_code}
        self.assertEqual(self.client.post('/register/',data).status_code,302)
        row.refresh_from_db()
        first_user = row.user
        self.client.logout()
        data['username'] = 'second_code_claim'
        self.assertEqual(self.client.post('/register/', data).status_code, 200)
        self.assertFalse(User.objects.filter(username='second_code_claim').exists())
        row.refresh_from_db()
        self.assertEqual(row.user, first_user)
        data.update(username='invalid_claim',enrollment_code='WRONG')
        self.assertEqual(self.client.post('/register/',data).status_code,200)
        self.assertFalse(User.objects.filter(username='invalid_claim').exists())

    def test_scoped_reports_and_no_curator_deletion(self):
        from django.core.files.base import ContentFile
        from django.test import override_settings
        _, Student = self.models()
        group = self.group()
        other_group = self.group('report-other-group')
        curator = User.objects.create_user('report_curator')
        outsider = User.objects.create_user('other_curator')
        group.curators.add(curator);other_group.curators.add(outsider)
        student = User.objects.create_user('report_student')
        Student.objects.create(group=group, position=1, full_name='Synthetic Report Student', user=student)
        finding = {'rule_id':'R_SIZE', 'status':'pass', 'method':'geometry', 'message':'observed',
                   'evidence':'A4', 'page':1, 'clause':'5.1.1', 'source_url':'https://www.apa.kz/'}
        with tempfile.TemporaryDirectory() as folder, override_settings(MEDIA_ROOT=folder):
            job = Submission.objects.create(owner=student, title='Private report', language='kk', duration='1',
                status='done', profile=DEFAULT_PROFILE, result=complete_result())
            job.file.save('private.pdf',ContentFile(b'%PDF-synthetic-privacy-fixture'))
            endings=['', 'status/', 'preview/', 'download/json/', 'download/original/']
            self.client.force_login(curator)
            response=self.client.get(f'/curator/work/{job.pk}/')
            self.assertContains(response,'Private report')
            self.assertNotContains(response,'delete-form')
            for ending in endings:
                response=self.client.get(f'/curator/work/{job.pk}/{ending}')
                self.assertEqual(response.status_code,200)
                self.assertIn('no-store',response['Cache-Control'])
                response.close()
            self.assertEqual(self.client.post(f'/work/{job.pk}/delete/').status_code,404)
            self.client.force_login(outsider)
            for ending in endings:
                self.assertEqual(self.client.get(f'/curator/work/{job.pk}/{ending}').status_code,404)
            self.client.force_login(student)
            self.assertEqual(self.client.get(f'/curator/work/{job.pk}/').status_code,404)
            self.assertTrue(Submission.objects.filter(pk=job.pk).exists())

    def test_existing_account_can_join_only_one_roster(self):
        _, Student=self.models();group=self.group()
        row=Student.objects.create(group=group,position=1,full_name='Synthetic Existing Student')
        second=Student.objects.create(group=group,position=2,full_name='Synthetic Other Student')
        user=User.objects.create_user('existing_account')
        self.client.force_login(user)
        self.assertEqual(self.client.post('/join-group/',{'study_group':group.pk,'enrollment_code':row.enrollment_code}).status_code,302)
        row.refresh_from_db();self.assertEqual(row.user,user)
        self.assertEqual(self.client.post('/join-group/',{'study_group':group.pk,'enrollment_code':second.enrollment_code}).status_code,302)
        second.refresh_from_db();self.assertIsNone(second.user)

    def test_scoped_curator_report_is_read_only(self):
        _, Student = self.models()
        group=self.group();other=self.group('other-report-group')
        curator=User.objects.create_user('report_curator');group.curators.add(curator)
        owner=User.objects.create_user('report_owner')
        Student.objects.create(group=group,position=1,full_name='Synthetic Owner',user=owner)
        job=Submission.objects.create(owner=owner,title='Synthetic report',file='test.pdf',language='kk',duration='1',status='queued')
        self.client.force_login(curator)
        response=self.client.get(f'/curator/work/{job.pk}/')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response['Cache-Control'],'private, no-store')
        self.assertNotContains(response,'delete-form')
        self.assertEqual(self.client.get(f'/work/{job.pk}/').status_code,404)
        self.assertEqual(self.client.post(f'/work/{job.pk}/delete/').status_code,404)
        group.curators.remove(curator);other.curators.add(curator)
        self.assertEqual(self.client.get(f'/curator/work/{job.pk}/').status_code,404)
        self.assertEqual(self.client.get(f'/curator/work/{job.pk}/download/json/').status_code,404)

    def test_private_import_is_idempotent_and_rejects_conflicts(self):
        from django.core.management.base import CommandError
        _, Student=self.models()
        group=self.group()
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'roster.json'
            payload={'groups':[{'code':group.code,'students':['Synthetic One','Synthetic Two']}]}
            path.write_text(json.dumps(payload),encoding='utf-8')
            for _ in range(2):call_command('import_students',str(path),stdout=io.StringIO())
            self.assertEqual(Student.objects.filter(group=group).count(),2)
            row=Student.objects.get(group=group,position=1);code=row.enrollment_code
            linked=User.objects.create_user('already_linked');row.user=linked;row.save()
            call_command('import_students',str(path),stdout=io.StringIO())
            row.refresh_from_db();self.assertEqual(row.user,linked);self.assertEqual(row.enrollment_code,code)
            payload['groups'][0]['students'][0]='Different Synthetic Person'
            path.write_text(json.dumps(payload),encoding='utf-8')
            with self.assertRaises(CommandError):call_command('import_students',str(path),stdout=io.StringIO())
            self.assertEqual(Student.objects.get(pk=row.pk).full_name,'Synthetic One')

    def test_curator_pages_translate_and_filter(self):
        from platform_app.i18n import TEXT
        _, Student=self.models();group=self.group()
        Student.objects.create(group=group,position=1,full_name='Synthetic Filter Student')
        self.client.force_login(self.staff)
        for lang in ['kk','ru','en']:
            self.client.post('/language/',{'language':lang})
            for path in ['/curator/',f'/curator/group/{group.pk}/']:
                response=self.client.get(path)
                self.assertContains(response,TEXT[lang]['curator_dashboard'])
            response=self.client.get(f'/curator/group/{group.pk}/?status=passed')
            self.assertNotContains(response,'Synthetic Filter Student')
        self.assertEqual(self.client.post(f'/curator/group/{group.pk}/',{}).status_code,405)

    def test_real_checker_without_headings_remains_a_valid_violation_report(self):
        import pymupdf
        from types import SimpleNamespace
        from platform_app.checker import check_pdf
        from platform_app.result_validation import valid_result
        from platform_app.curator import submission_outcome
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'without-headings.pdf'
            doc=pymupdf.open()
            for _ in range(2):
                page=doc.new_page()
                for y in range(100,300,20):
                    page.insert_text((85,y),'Academic research discusses government and public institutions.',fontname='tiro',fontsize=14)
            doc.save(path);doc.close()
            result=check_pdf(path,language='en')
        self.assertNotIn('R_HEADING',{f['rule_id'] for f in result['findings']})
        self.assertTrue(valid_result(result,DEFAULT_PROFILE))
        self.assertEqual(submission_outcome(SimpleNamespace(status='done',result=result,profile=DEFAULT_PROFILE)),'revision')

    def test_complete_pdf_export_and_rejected_missing_metadata(self):
        from platform_app.result_validation import valid_result
        result=complete_result()
        for key in ['page_count','body_pages','original_sha256']:
            missing=dict(result);missing.pop(key)
            self.assertFalse(valid_result(missing,DEFAULT_PROFILE),key)
        missing=complete_result();missing['findings'][0].pop('page')
        self.assertFalse(valid_result(missing,DEFAULT_PROFILE))
        _,Student=self.models();group=self.group()
        owner=User.objects.create_user('pdf_export_owner')
        Student.objects.create(group=group,position=1,full_name='Synthetic PDF Owner',user=owner)
        job=Submission.objects.create(owner=owner,title='Complete export',file='synthetic.pdf',language='en',duration='1',
            status='done',profile=DEFAULT_PROFILE,result=result)
        self.client.force_login(self.staff)
        response=self.client.get(f'/curator/work/{job.pk}/download/pdf/')
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.content.startswith(b'%PDF'))
