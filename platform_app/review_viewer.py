"""Protected, bounded page rendering. All annotations exist only in memory."""
import hashlib
import math
from threading import BoundedSemaphore
from urllib.parse import urlencode

import pymupdf as fitz
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from .checker import MAX_SIZE
from .curator import curated_submission
from .i18n import strings
from .models import Submission
from .result_validation import valid_result

_render_slot = BoundedSemaphore(1)


def _job(request, pk, curator_view):
    return curated_submission(request, pk) if curator_view else get_object_or_404(Submission, pk=pk, owner=request.user)


def _selection(request, job):
    page = int(request.GET.get('page', '1'))
    if not 1 <= page <= job.result['page_count']:
        raise ValueError('page')
    selected = request.GET.get('finding')
    if selected is not None:
        selected = int(selected)
        if not 0 <= selected < len(job.result['findings']):
            raise ValueError('finding')
        finding = job.result['findings'][selected]
        if finding.get('page') not in (None, page):
            raise ValueError('finding page')
    return page, selected


def _error(request, key, status):
    response = render(request, 'platform_app/error.html', {'error':strings(request.LANGUAGE_CODE)[key]}, status=status)
    response['Cache-Control'] = 'private, no-store'
    return response


def _page_dict(page, number):
    lines, spans = [], []
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines', []):
            text = ''.join(s['text'] for s in line['spans']).strip()
            if text:
                lines.append({'text':text, 'bbox':list(line['bbox'])})
            spans.extend({key:s[key] for key in ('text','font','size','color','flags','bbox')}
                         for s in line['spans'] if s['text'].strip())
    return {'page_no':number, 'width_pt':page.cropbox.width, 'height_pt':page.cropbox.height,
            'text':page.get_text(), 'lines':lines, 'spans':spans}


def _boxes(job, page, number, selected):
    from .evidence import locations_on_page, validated_locations
    page_data = None
    boxes = []
    for index, finding in enumerate(job.result['findings']):
        if finding['status'] != 'fail' or finding.get('page') not in (None, number):
            continue
        safe, _ = validated_locations(finding.get('locations', []))
        locations = [loc for loc in safe if loc['page'] == number]
        if not locations:
            page_data = page_data or _page_dict(page, number)
            locations = locations_on_page(finding, page_data, job.profile)
        for location in locations[:60]:
            raw = location['bbox']
            rect = fitz.Rect(raw) & fitz.Rect(0, 0, page.cropbox.width, page.cropbox.height)
            if rect.is_empty or rect.is_infinite or rect.width <= 0 or rect.height <= 0:
                continue
            boxes.append((rect, selected == index))
        if len(boxes) >= 1000:
            break
    return boxes[:1000]


@login_required
@require_GET
def viewer(request, pk, curator_view=False):
    job = _job(request, pk, curator_view)
    if job.status != 'done' or not valid_result(job.result, job.profile):
        return _error(request, 'invalid_report', 409)
    try:
        number, selected = _selection(request, job)
    except (ValueError, TypeError, KeyError):
        return _error(request, 'invalid_page', 400)
    prefix = 'curator_' if curator_view else ''
    parameters = {'page':number}
    if selected is not None:
        parameters['finding'] = selected
    image_url = reverse(prefix+'page_image', args=[pk]) + '?' + urlencode(parameters)
    query = '?page='
    base = reverse(prefix+'viewer', args=[pk])
    chosen = job.result['findings'][selected] if selected is not None else None
    response = render(request, 'platform_app/page_viewer.html', {
        'job':job, 'page_number':number, 'page_count':job.result['page_count'], 'image_url':image_url,
        'previous_url':base+query+str(number-1) if number>1 else None,
        'next_url':base+query+str(number+1) if number<job.result['page_count'] else None,
        'viewer_url':base, 'selected':selected, 'chosen_rule':strings(request.LANGUAGE_CODE).get(chosen['rule_id']) if chosen else '',
    })
    response['Cache-Control'] = 'private, no-store'
    return response


@login_required
@require_GET
def page_image(request, pk, curator_view=False):
    job = _job(request, pk, curator_view)
    if job.status != 'done' or not valid_result(job.result, job.profile):
        return _error(request, 'invalid_report', 409)
    try:
        number, selected = _selection(request, job)
    except (ValueError, TypeError, KeyError):
        return _error(request, 'invalid_page', 400)
    if not _render_slot.acquire(timeout=5):
        return _error(request, 'viewer_busy', 503)
    try:
        with job.file.open('rb') as original:
            data = original.read(MAX_SIZE+1)
        if len(data)>MAX_SIZE or hashlib.sha256(data).hexdigest() != job.result['original_sha256']:
            return _error(request, 'original_changed', 409)
        with fitz.open(stream=data, filetype='pdf') as document:
            if document.is_encrypted or not 1 <= number <= len(document):
                return _error(request, 'invalid_page', 400)
            page = document[number-1]
            boxes = _boxes(job, page, number, selected)
            # Overlapping errors share a single yellow mark; this avoids an opaque stack.
            seen = set()
            for rect, focused in boxes:
                key = tuple(round(n,1) for n in rect)
                if key not in seen:
                    annotation = page.add_highlight_annot(rect)
                    annotation.set_colors(stroke=(1, 0.88, 0))
                    annotation.set_opacity(0.45)
                    annotation.update()
                    seen.add(key)
                if focused:
                    page.draw_rect(rect, color=(0.85,0.48,0), width=0.8, overlay=True)
            focus = next((rect for rect, active in boxes if active), None)
            focus_top = None
            if focus is not None:
                rotated = focus * page.rotation_matrix
                focus_top = max(0, min(1, rotated.y0/max(page.rect.height,1)))
            page = document.reload_page(page)
            scale = min(1.8, 1400/max(page.rect.width,1), 2000/max(page.rect.height,1))
            image = page.get_pixmap(matrix=fitz.Matrix(scale,scale), colorspace=fitz.csRGB, alpha=False)
            payload = image.tobytes('png')
        response = HttpResponse(payload, content_type='image/png')
        response['Cache-Control'] = 'private, no-store'
        response['X-Highlight-Count'] = str(len(seen))
        if focus_top is not None:
            response['X-Focus-Top'] = f'{focus_top:.6f}'
        return response
    except (OSError, ValueError, RuntimeError):
        return _error(request, 'viewer_unavailable', 503)
    finally:
        _render_slot.release()
