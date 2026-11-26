# Yellow evidence and revised project implementation plan

**Goal:** Clicking “Page 33” opens physical PDF page33 with yellow marks on verified error lines; reports show exact requirements and examples; uploading a corrected revision compares outcomes with its selected predecessor.

**Authorization:** User explicitly requested these behaviors and delegated design decisions. Keep the existing full trilingual platform, Academy branding, free hosting, owner/curator scopes and unchanged original files. No new paid service, API key or system component.

**Architecture:** Store real PDF text coordinates in findings. Render one bounded PDF page on demand with temporary yellow annotations, through protected Django routes, and display it in a controlled HTML viewer. Original PDFs remain byte-for-byte intact. Use an explicit “Upload corrected version” action linking submissions, retaining history. Compare unchanged anchors and conclusive rule results; changed/deleted text or uncertain measurements never become a false success. Older reports use conservative on-demand evidence localization.

**Decisions:** A browser-native PDF iframe cannot reliably control line highlights/page scrolling across browsers; the built-in page viewer removes that dependency. Page images use PyMuPDF already installed, no CDN/PDF.js dependency. Global requirements without a text location are described as such instead of coloring an arbitrary paragraph. All three interface/report languages remain complete.

## Tasks

- [ ] Coordinate evidence: failing page33 tests, real locations/anchors, bounded and validated metadata, current evidence coverage, unchanged input hashes.
- [ ] Rule-specific guidance and revision comparison: font/size/colour/margins/numbering/captions/structure/length/spacing examples using the stored profile; page-shift, repeated-anchor, uncertainty and incompatible-profile tests.
- [ ] Protected viewer: HTML viewer, bounded PNG renderer, exact page/selected finding, reliable parent iframe navigation, pending/error UI, accessibility and privacy tests; visually inspect synthetic highlighted page33.
- [ ] Revision workflow: nullable self-FK migration, owner-only predecessor selection, inherited form defaults, queue comparison integration, history/report/PDF/JSON comparison presentation, legacy-result compatibility.
- [ ] Integration: full suite, independent review, synthetic HTTP end-to-end, source/private-data scan, GitHub publication, existing free-service deployment, real URL checks and temporary synthetic cleanup.

## Verification focus

Reject foreign-user and out-of-scope curator access at every viewer/image/revision route. Bound page dimensions and concurrent rendering; do not follow file-supplied URLs or expose public storage. Respect crop/rotation coordinates. Preserve stale-job and invalid-result behavior. Never declare a correction just because its text disappeared, coordinates moved, or a measurement became uncertain. Keep current students/rosters and original reports private.
