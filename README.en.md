# Academic Format Review · English

A trilingual platform for automatically reviewing thesis PDFs against the
requirements of the Academy of Public Administration under the President of Kazakhstan.

1. Extract the Windows ZIP into a writable folder.
2. Run `APA Thesis Checker.exe`. Your browser opens at `127.0.0.1:8765`.
3. Register an account. The first local account becomes the administrator.
4. Start a new review, upload a PDF, select document language and programme duration.
5. Download the PDF/JSON report. Previous submissions remain in your private history.

Kazakh, Russian and English interfaces, messages and reports are supported.
Interface language and document language are independent. Originals are not modified.
The Windows build is local only, without public internet access. Stop with Ctrl+C
or close the application console. Accounts and files live in `data/` beside the EXE.

All implemented checks are automatic. “Insufficient evidence” is an automatic
result, not a pass. PDF layout measurements cannot establish every source Word
setting. No plagiarism, research-quality, spelling or OCR checks are included.
Limits: text-based PDFs up to 30 MB and 300 pages.

Rules use Appendix 1 to Order No. 586 dated 13 September 2024. Minimum length:
40 pages for one-year programmes; 60 pages for 1.5/2-year programmes, excluding
appendices. Administrators manage the profile at `/admin/`. Changes apply only
to future reviews; reports preserve their original rule snapshot.
Reports are preliminary feedback, not official approval.

Development: [README.md](README.md). Cloud: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).
Corresponding application source is available from every page footer.
AGPL-3.0-or-later; original upstream MIT notices are preserved.
