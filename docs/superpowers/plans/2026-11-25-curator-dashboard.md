# Curator Dashboard Implementation Plan

> **For agentic workers:** Execute inline with superpowers:executing-plans and test-driven-development. No per-task agents.

**Goal:** Give an authorized curator accurate private progress for two Executive MPA winter groups and import the supplied 37 students.

**Architecture:** StudyGroup and RosterStudent models with scoped curator access, stable per-student enrolment codes, and latest-submission aggregation. Reuse existing report rendering through explicitly scoped curator routes.

**Tech Stack:** Existing Django 5.2, SQLite/PostgreSQL, Python 3.12, PyInstaller.

**Spec:** docs/superpowers/specs/2026-11-25-curator-dashboard.md

## Global Constraints

- Kazakh/Russian/English UI; retain Academy logo and colours.
- No real names or codes in Git or distributable archives.
- Preserve existing accounts, reports and private data.
- No new paid services or system components.

## Review Focus

- Ordinary students and curators assigned to another group cannot view a roster or report.
- Repeated uploads never increase student counts; latest uncertain result replaces an earlier pass.
- Missing/malformed reports and missing rosters never count as passed or complete.
- Duplicate imports do not duplicate students or reset account bindings/codes.
- Used enrolment codes cannot claim a second account; concurrent claims are atomic.

## Tasks

- [x] Write a failing staff curator-page test, then implement roster models, group seeds, access helpers and latest-result aggregation; add tests for every review focus.
- [x] Implement registration/join binding and scoped curator report routes; preserve owner-only deletion and legacy registration tests.
- [x] Add group dashboard, roster table, filters, invitation-code display and translations; verify all three languages and private source exclusions.
- [ ] Add validated idempotent private JSON import command, test with synthetic names, import the actual user-supplied rosters into private data only.
- [ ] Run the suite, review the diff, build a new Windows version, preserve local data, verify HTTP access and publish clean source/artifacts to the authorized GitHub repository.
