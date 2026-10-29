import io
import json
import re
import secrets
import time
import zipfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.cache import cache
from django.db import transaction, IntegrityError
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST, require_GET

from .checker import MAX_SIZE
from .i18n import strings, finding_text
from .jobs import seed_profile
from .models import RuleProfile, Submission
from .reports import pdf_report


def limited(request, action, maximum=20):
    address = request.META.get("REMOTE_ADDR", "local")
    key = f"limit:{action}:{address}:{int(time.time()//300)}"
    try:
        cache.add(key, 0, 310)
        return cache.incr(key) > maximum
    except ValueError:
        return False


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    error = ""
    if request.method == "POST":
        if limited(request, "login"):
            error = "rate_limit"
        else:
            user = authenticate(request, username=request.POST.get("username", ""), password=request.POST.get("password", ""))
            if user is not None:
                login(request, user)
                return redirect("dashboard")
            error = "auth_error"
    return render(request, "platform_app/auth.html", {"mode": "login", "error": strings(request.LANGUAGE_CODE).get(error)})


def register(request):
    error = ""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        if limited(request, "register", 8):
            error = "rate_limit"
        elif not re.fullmatch(r"[A-Za-z0-9_]{3,50}", username) or User.objects.filter(username__iexact=username).exists():
            error = "register_error"
        else:
            try:
                validate_password(password, User(username=username))
                if password != request.POST.get("password2"):
                    raise ValidationError("mismatch")
                with transaction.atomic():
                    bootstrap = settings.ALLOWED_HOSTS == ["localhost", "127.0.0.1", "[::1]"] and not User.objects.exists()
                    user = User.objects.create_user(username=username, password=password, is_staff=bootstrap, is_superuser=bootstrap)
                login(request, user)
                return redirect("dashboard")
            except ValidationError:
                error = "password_error"
            except IntegrityError:
                error = "register_error"
    return render(request, "platform_app/auth.html", {"mode": "register", "error": strings(request.LANGUAGE_CODE).get(error)})


@require_POST
def logout_view(request):
    language = request.LANGUAGE_CODE
    logout(request)
    request.session["language"] = language
    return redirect("login")


@require_POST
def language(request):
    lang = request.POST.get("language")
    if lang in ("kk", "ru", "en"):
        request.session["language"] = lang
    target = request.POST.get("next", "/")
    if not url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        target = "/"
    return redirect(target)


def dashboard(request):
    if not request.user.is_authenticated:
        return render(request, "platform_app/landing.html")
    works = Submission.objects.filter(owner=request.user)
    return render(request, "platform_app/dashboard.html", dict(works=works[:5], total=works.count(),
                 completed=works.filter(status="done").count(), pending=works.filter(status__in=["queued", "processing"]).count()))


@login_required
def history(request):
    from django.core.paginator import Paginator
    page = Paginator(Submission.objects.filter(owner=request.user), 20).get_page(request.GET.get("page"))
    return render(request, "platform_app/history.html", {"works": page, "pagination": page})


@login_required
def upload(request):
    seed_profile()
    error = ""
    if request.method == "POST":
        file = request.FILES.get("file")
        lang = request.POST.get("language")
        duration = request.POST.get("duration")
        title = request.POST.get("title", "").strip()
        if limited(request, "upload", 20):
            error = "rate_limit"
        elif not file or not title or len(title) > 180 or lang not in ("kk", "ru", "en") or duration not in ("1", "1.5", "2"):
            error = "invalid_form"
        elif file.size > MAX_SIZE:
            error = "too_large"
        elif not file.name.lower().endswith(".pdf") or not file.read(5) == b"%PDF-":
            error = "bad_pdf"
        else:
            file.seek(0)
            profile = RuleProfile.objects.filter(active=True).first()
            if profile is None:
                error = "worker_error"
            else:
                work = Submission(owner=request.user, title=title, language=lang, duration=duration, profile=profile.snapshot())
                work.file.save(f"{work.id}.pdf", file, save=False)
                work.save()
                return redirect("detail", pk=work.pk)
    profile = RuleProfile.objects.filter(active=True).first()
    return render(request, "platform_app/upload.html", {"error": strings(request.LANGUAGE_CODE).get(error), "profile": profile})


@login_required
def detail(request, pk):
    job = get_object_or_404(Submission, pk=pk, owner=request.user)
    findings = [finding_text(f, request.LANGUAGE_CODE) for f in job.result.get("findings", [])]
    t = strings(request.LANGUAGE_CODE)
    counts = [(s, t[s], job.result.get("counts", {}).get(s, 0)) for s in ("pass", "fail", "uncertain", "na")]
    return render(request, "platform_app/detail.html", dict(job=job, findings=findings, counts=counts,
                  status_label=t[job.status], error=t.get(job.error_code, t["worker_error"])))


@login_required
@require_GET
def job_status(request, pk):
    job = get_object_or_404(Submission, pk=pk, owner=request.user)
    response = JsonResponse({"status": job.status})
    response["Cache-Control"] = "no-store"
    return response


@login_required
def preview(request, pk):
    job = get_object_or_404(Submission, pk=pk, owner=request.user)
    response = FileResponse(job.file.open("rb"), content_type="application/pdf", filename="document.pdf")
    response["Content-Disposition"] = 'inline; filename="document.pdf"'
    response["Cache-Control"] = "private, no-store"
    return response


@login_required
def download(request, pk, kind):
    job = get_object_or_404(Submission, pk=pk, owner=request.user)
    if kind == "original":
        response = FileResponse(job.file.open("rb"), content_type="application/pdf", as_attachment=True, filename="original.pdf")
    elif job.status != "done":
        return not_found(request)
    elif kind == "json":
        result = dict(job.result)
        result["report_language"] = request.LANGUAGE_CODE
        result["findings"] = [finding_text(f, request.LANGUAGE_CODE) for f in result["findings"]]
        response = HttpResponse(json.dumps(result, ensure_ascii=False, indent=2), content_type="application/json; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="report.json"'
    elif kind == "pdf":
        response = HttpResponse(pdf_report(job, request.LANGUAGE_CODE), content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="report.pdf"'
    else:
        return not_found(request)
    response["Cache-Control"] = "private, no-store"
    return response


@login_required
@require_POST
def delete_work(request, pk):
    job = get_object_or_404(Submission, pk=pk, owner=request.user)
    if job.status != "processing":
        job.file.delete(save=False)
        job.delete()
    return redirect("history")


def guide(request):
    from .checker import DEFAULT_PROFILE, REGISTRY
    return render(request, "platform_app/guide.html", {"profile": DEFAULT_PROFILE,
        "rules": [(strings(request.LANGUAGE_CODE)[rid], clause) for rid, clause, _ in REGISTRY]})


def source(request):
    """Source archive is constructed only from an explicit distributable manifest."""
    from .source_bundle import source_archive
    response = HttpResponse(source_archive(), content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="apa-thesis-checker-source.zip"'
    return response


def health(request):
    from .version import VERSION
    return JsonResponse({"status": "ok", "version": VERSION})


def not_found(request, exception=None):
    return render(request, "platform_app/error.html", {"error": strings(request.LANGUAGE_CODE)["not_found"]}, status=404)


def server_error(request):
    return render(request, "platform_app/error.html", {"error": strings(request.LANGUAGE_CODE)["worker_error"]}, status=500)
