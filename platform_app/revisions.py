"""A comparison baseline must always belong to the same student."""
from .comparison import compare_results
from .models import Submission
from .result_validation import valid_result


def previous_for(job):
    if job.previous_id:
        return Submission.objects.filter(pk=job.previous_id, owner_id=job.owner_id, status='done').first()
    return None


def comparison_for(job):
    previous = previous_for(job)
    if previous and valid_result(previous.result, previous.profile) and valid_result(job.result,job.profile):
        return compare_results(previous.result, job.result)
    return None
