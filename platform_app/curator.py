"""Private roster access and one latest result per student."""
from collections import Counter

from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Subquery
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils.crypto import constant_time_compare
from django.views.decorators.http import require_GET

from .i18n import strings
from .models import RosterStudent, StudyGroup, Submission
from .result_validation import valid_result


def visible_groups(user):
    if not user.is_authenticated or not user.is_active:
        return StudyGroup.objects.none()
    if user.is_staff or user.is_superuser:
        return StudyGroup.objects.all()
    return StudyGroup.objects.filter(curators=user).distinct()


def can_curate(user):
    return bool(user.is_authenticated and user.is_active and
                (user.is_staff or user.is_superuser or user.curated_study_groups.exists()))


def find_enrollment(group_id, code, *, lock=False):
    if not str(group_id).isdigit() or len(str(group_id)) > 18 or not code or len(code) > 80:
        return None
    rows = RosterStudent.objects.filter(group_id=group_id, group__roster_loaded=True)
    if lock:
        rows = rows.select_for_update()
    code = code.strip().upper()
    for row in rows:
        if constant_time_compare(row.enrollment_code, code) and row.user_id is None:
            return row
    return None


def submission_outcome(job):
    if job.status in ("queued", "processing"):
        return "processing"
    if job.status == "failed":
        return "failed"
    if job.status != "done" or not valid_result(job.result, job.profile):
        return "inconclusive"
    counts = job.result["counts"]
    if counts["fail"]:
        return "revision"
    if counts["uncertain"] or not counts["pass"]:
        return "inconclusive"
    return "passed"


def group_overview(group):
    latest = Submission.objects.filter(owner_id=OuterRef("user_id")).order_by("-created_at", "-id")
    students = list(group.students.select_related("user").annotate(
        latest_id=Subquery(latest.values("id")[:1])))
    jobs = Submission.objects.in_bulk([s.latest_id for s in students if s.latest_id])
    counts = Counter()
    rows = []
    for student in students:
        job = jobs.get(student.latest_id)
        state = "unregistered" if not student.user_id else "not_uploaded" if job is None else submission_outcome(job)
        counts[state] += 1
        rows.append({"student": student, "job": job, "state": state})
    total = len(students)
    remaining = counts["unregistered"] + counts["not_uploaded"]
    overview = dict(group=group, rows=rows, total=total, registered=total-counts["unregistered"],
        uploaded=total-remaining, remaining=remaining, unregistered=counts["unregistered"], not_uploaded=counts["not_uploaded"],
        passed=counts["passed"], revision=counts["revision"], inconclusive=counts["inconclusive"],
        processing=counts["processing"], failed=counts["failed"])
    overview["completion_percent"] = round(100 * overview["uploaded"] / total) if total else 0
    if not group.roster_loaded:
        for key in ("total", "registered", "uploaded", "remaining", "unregistered", "not_uploaded", "passed", "revision",
                    "inconclusive", "processing", "failed", "completion_percent"):
            overview[key] = None
    return overview


def curated_submission(request, pk):
    if not can_curate(request.user):
        raise Http404
    return get_object_or_404(Submission.objects.select_related("owner__student_roster__group"),
        pk=pk, owner__student_roster__group__in=visible_groups(request.user))


@login_required
@require_GET
def dashboard(request):
    t = strings(request.LANGUAGE_CODE)
    if not can_curate(request.user):
        return render(request, "platform_app/error.html", {"error": t["curator_forbidden"]}, status=403)
    groups = [group_overview(group) for group in visible_groups(request.user)]
    keys = ("total", "registered", "unregistered", "not_uploaded", "uploaded", "remaining", "passed", "revision", "inconclusive", "processing", "failed")
    totals = {key: sum(g[key] or 0 for g in groups) for key in keys}
    if any(g["total"] is None for g in groups):
        totals = {key: None for key in keys}
    response = render(request, "platform_app/curator_dashboard.html", {"groups": groups, "totals": totals})
    response["Cache-Control"] = "private, no-store"
    return response


@login_required
@require_GET
def group_detail(request, pk):
    group = get_object_or_404(visible_groups(request.user), pk=pk)
    overview = group_overview(group)
    t = strings(request.LANGUAGE_CODE)
    choices = ("unregistered", "not_uploaded", "processing", "passed", "revision", "inconclusive", "failed")
    state = request.GET.get("status", "all")
    if state not in (*choices, "all"):
        state = "all"
    rows = overview["rows"] if state == "all" else [r for r in overview["rows"] if r["state"] == state]
    query = request.GET.get("q", "").strip()[:180]
    if query:
        rows = [r for r in rows if query.casefold() in r["student"].full_name.casefold()]
    for row in rows:
        row["state_label"] = t["cur_" + row["state"]]
    response = render(request, "platform_app/curator_group.html", {"overview": overview, "group": group,
        "rows": rows, "status_filter": state, "query": query, "state_options": [(s, t["cur_"+s]) for s in choices]})
    response["Cache-Control"] = "private, no-store"
    return response
