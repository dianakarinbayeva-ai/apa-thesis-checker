import logging
import time
from datetime import timedelta
from threading import Event

from django.db import close_old_connections
from django.utils import timezone

from .checker import DEFAULT_PROFILE, PDFError, check_pdf
from .models import RuleProfile, Submission
from .private_storage import pdf_local_path
from .revisions import previous_for
from .comparison import compare_results
from .result_validation import valid_result

logger = logging.getLogger(__name__)


def seed_profile():
    profile, _ = RuleProfile.objects.get_or_create(code=DEFAULT_PROFILE["code"], defaults={k: v for k, v in DEFAULT_PROFILE.items() if k != "code"})
    return profile


def process_one():
    close_old_connections()
    now = timezone.now()
    # Recover jobs whose process was interrupted. No automatic duplicate processing.
    Submission.objects.filter(status="processing", started_at__lt=now - timedelta(minutes=10)).update(
        status="failed", error_code="timeout", finished_at=now)
    job = Submission.objects.filter(status="queued").order_by("created_at").first()
    if job is None:
        return False
    claimed = Submission.objects.filter(pk=job.pk, status="queued").update(status="processing", started_at=now)
    if not claimed:
        return False
    try:
        previous = previous_for(job)
        if previous and not valid_result(previous.result, previous.profile):
            previous = None
        prior_findings = previous.result.get('findings', []) if previous else None
        with pdf_local_path(job.file) as path:
            result = check_pdf(path, duration=job.duration, language=job.language, profile=job.profile,
                previous_findings=prior_findings)
        if previous:
            result['comparison'] = compare_results(previous.result, result)
        Submission.objects.filter(pk=job.pk, status="processing").update(result=result, status="done", finished_at=timezone.now())
    except PDFError as exc:
        Submission.objects.filter(pk=job.pk).update(status="failed", error_code=str(exc), finished_at=timezone.now())
    except Exception:
        logger.exception("Submission processing failed: %s", job.pk)
        Submission.objects.filter(pk=job.pk).update(status="failed", error_code="worker_error", finished_at=timezone.now())
    finally:
        close_old_connections()
    return True


def worker(stop=None):
    stop = stop or Event()
    while not stop.is_set():
        try:
            if not process_one():
                stop.wait(1)
        except Exception:
            logger.exception("Worker unavailable")
            close_old_connections()
            stop.wait(3)
