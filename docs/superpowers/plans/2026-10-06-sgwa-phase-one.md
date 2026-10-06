# SGWA Phase One Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement workflow paralel lintas dinas, SLA, status langsung, dan audit admin tanpa kehilangan data atau alur demo yang ada.

**Architecture:** Extend modular monolith FastAPI dengan tugas per dinas dan status agregat pada permohonan. Semua keputusan, SLA, timeline dan audit memakai transaksi MySQL yang sama; worker Python menjalankan pemeriksaan tenggat, sementara SSE memberi sinyal agar React mengambil ulang data. Tidak memakai model multi-label atau broker tambahan.

**Tech Stack:** Existing Python/FastAPI, SQLAlchemy 2, Alembic, PyMySQL, React/TypeScript/Vite, Radix Themes, Phosphor, pytest, Playwright Edge. SSE memakai StreamingResponse dan EventSource bawaan; tidak perlu dependency produk baru.

**Spec:** `docs/superpowers/specs/2026-10-06-sgwa-expansion-design.md` — tahap 1 saja. Tahap 2/3 tidak dianggap selesai oleh rencana ini.

## Global Constraints

- Database tetap MySQL sesuai ketentuan pengguna.
- Tidak menimpa database lama atau menghapus layanan EnvKit.
- Credentials tetap berada di .env dan tidak dicetak.
- Agency.sla_days integer 1–90, default 3 hari kalender.
- Semua waktu UTC di database, Asia/Jakarta di UI.
- Worker mengecek setiap 60 detik; pemeriksaan sekali tersedia untuk pengujian.
- Confidence rendah atau teks tidak dikenal tetap escalated tanpa routing otomatis.
- Approved hanya setelah seluruh dinas menyetujui; penolakan/SLA lewat menghasilkan escalated.
- Keputusan final tetap meminta konfirmasi; mutasi tidak diulang otomatis.
- Oracle MySQL harus diverifikasi sebelum persyaratan engine dinyatakan terpenuhi. Koneksi yang terakhir diperiksa adalah MariaDB 11.8.2.

## Review Focus

1. Pengajuan lama aktif saat migrasi: tidak kehilangan status/riwayat dan tidak langsung overdue (Task 1).
2. Putaran review baru setelah penolakan: catatan putaran lama tetap terlacak; keputusan lama tidak menyetujui putaran baru (Task 3).
3. Penonaktifan/penugasan ulang staf saat SSE tersambung: scope lama tidak diteruskan, pengguna wajib mengambil ulang otorisasi (Task 5).
4. Worker dan keputusan staf berjalan bersamaan: keputusan terminal tidak ditimpa dan satu eskalasi tidak dicatat dua kali (Task 4).
5. Sinyal live saat mengetik atau setelah reconnect: draft tetap utuh, detail dan antrean tidak memakai data stale atau menampilkan kasus di luar scope (Task 7).

## File Map and Interfaces

Models/migration: extend `backend/app/models.py`, add `backend/alembic/versions/0002_parallel_workflow.py`.

Workflow: keep `backend/app/workflow/service.py` as public compatibility adapter; add `workflow/tasks.py` for decisions, `workflow/routing.py` for route configuration. Add `workflow/routes.py` and `workflow/schemas.py` for explicit task and admin route APIs. Scope/serialization stay in `requests/service.py`.

SLA: add `backend/app/sla/service.py`, `backend/app/sla/worker.py`, `backend/app/sla/__init__.py`. Audit: add `audit/routes.py`, `audit/schemas.py` beside existing transactional recorder. Live: add `live/service.py`, `live/routes.py`, `live/__init__.py`. Frontend: add `api/useLiveUpdates.ts`, `components/WorkflowTasks.tsx`, `pages/AuditLogs.tsx`, `pages/WorkflowRoutes.tsx`.

Public compatibility: existing status/reroute endpoints stay available. For staff, legacy status mutation applies to their single task; for admin it performs final review. New clients use explicit task endpoint. Legacy reroute accepts one agency; new review routing accepts a unique list.

Task representation: `{id, agency_id, agency_name, status, version, due_at, completed_at, decision_note, overdue}`. Detailed requests add `workflows`; existing summary fields stay. Staff scope is an EXISTS query on request_workflows, never a duplicate JOIN that breaks counts/pagination. Audit list: `{items,total,page,page_size}`.

## Task 1: Safe migration and task model

**Files:** Modify models.py, agencies/schemas.py, agencies/service.py, requests/service.py; create migration 0002 and `backend/tests/test_parallel_migration.py`.
**Produces:** `RequestWorkflow` model, `WorkflowRoute` model (unique source_code/agency_id), Agency.sla_days; `serialize(session,item,detail=True)` includes workflows. Route rows reference source agency code through FK; destination references agency id. Rule order is deterministic by agency id, with primary class agency first.

- [ ] Write migration test at revision 0001 inserting pending/processing/approved/rejected/escalated requests and historical events; run 0002; assert original rows unchanged, mapped terminal tasks have matching status, active tasks due_at approximately migration UTC + 3 days, and escalated rows do not get runnable tasks. Assert unique request/agency and SLA schema default 3.
- [ ] Run `.venv\Scripts\python.exe scripts/test_backend.py`; expected new migration test fails because 0002 is absent. All destructive setup uses `validated_test_url` before connecting.
- [ ] Implement migration backfill: terminal completed_at from request.updated_at; no assigned agency means no task. Maintain assigned_agency_id. ORM defaults and API default sla_days = 3 agree. On downgrade, refuse if multi-agency tasks exist rather than silently discard them; application backup and staging migration must precede applying to sgwa_demo.
- [ ] Run migration tests and schema suite; assert upgrade/downgrade on empty database, refusal of lossy downgrade, and FK invariants. Update existing schema test for new tables without weakening prior assertions.
- [ ] Commit `feat: add versioned agency tasks and SLA migration`.

## Task 2: Configurable multi-agency submit

**Files:** Create workflow/routing.py, routes.py, schemas.py; modify requests/service.py, main.py; create `backend/tests/test_workflow_routing.py`.
**Consumes:** RequestWorkflow, WorkflowRoute, Classifier.predict, transactional audit recorder.
**Produces:** `resolve_route(db:Session, code:str)->list[Agency]`; `set_route(db:Session,actor:User,code:str,agency_ids:list[int])->list[Agency]`. GET `/workflow/routes`; PUT `/workflow/routes/{code}` body `{agency_ids:[...]}` admin only. Include primary class agency implicitly and reject source/destination inactive, duplicate ids, empty destinations, missing agencies; maximum 20 destinations including primary.

- [ ] Write tests for Perizinan -> Perizinan + Pajak yielding two pending tasks/due snapshots and one historical classification; unknown text stays escalated with zero tasks; invalid destination makes submit escalated atomically; citizen/staff cannot edit rules. `assert len(detail['workflows']) == 2` and ML predicted code unchanged.
- [ ] Run backend suite; expected routing tests fail for absent APIs/tasks.
- [ ] Implement locked route resolution, validate all agencies before creating tasks, preserve classification version/probabilities, create all tasks/event/audit in one transaction. No rules means primary-only route. Reject invalid route changes with 422 and audit successful changes. Lock source agency before destinations in sorted id order; document consistent lock order with Task 3.
- [ ] Run suite including low-confidence boundaries, audit rollback and agency deactivation regressions. Extend pause-based concurrency tests to pause before task insert without retaining deadlock-inducing assumptions about earlier code.
- [ ] Commit `feat: route classified requests to configured agencies`.

## Task 3: Parallel decisions, aggregate state and human review

**Files:** Create workflow/tasks.py, `backend/tests/test_parallel_decisions.py`; modify workflow/service.py, routes.py, schemas.py, requests/service.py, requests/routes.py.
**Produces:** `decide_task(db:Session,actor:User,request_id:int,task_id:int,request_version:int,task_version:int,status:str,note:str)->Request`; `review_route(db:Session,actor:User,request_id:int,version:int,agency_ids:list[int],note:str)->Request`. PATCH `/requests/{id}/tasks/{task_id}` body `{request_version,task_version,status,note}`; POST `/requests/{id}/review-route` body `{version,agency_ids,note}`. Admin final review remains PATCH status.

- [ ] Write tests: first agency approved leaves processing, final approval makes approved; one rejection makes escalated; tasks frozen on escalated; admin final review preserves actual rejected task; reroute archives previous task outcomes in event changes then resets a fresh round with new due/version. Staff outside task agency gets 404; citizen mutation 403; stale versions 409; two decisions never lose one committed outcome.
- [ ] Run suite; expected new parallel assertions fail under single-agency service.
- [ ] Implement locking request first, then task rows, then agency rows for review; require note for approved/rejected/escalated and processing only from pending. Escalated is request-level action with note; task status enum remains four values. Parent version increases for every task action; preserve original from_status, record task agency and status in audit/event note. Derived status: all pending => pending, any started/approved => processing, all approved => approved, any rejected => escalated. Terminal parent disallows further task changes.
- [ ] Adapt legacy status/reroute and staff scope. No changed semantics for single-agency happy path; intentional change: staff rejection now escalates for admin rather than immediately final rejecting. Tests must pin the new rule, not discard rejection coverage.
- [ ] Run full suite including rollback, optimistic conflict, request isolation, pagination with one citizen request shared by two agencies, and historical manual-review decisions.
- [ ] Commit `feat: coordinate agency decisions with final human review`.

## Task 4: SLA worker and real metrics

**Files:** Create sla/service.py, worker.py, __init__.py, `backend/tests/test_sla.py`; modify agencies schemas/service/routes and dashboard/routes.py.
**Produces:** `escalate_overdue(db:Session,now:datetime,limit:int=100)->int`; CLI `python -m backend.app.sla.worker --once`, default loop 60 seconds. Dashboard adds `overdue_count`, `average_completed_hours:float|null`; by_agency counts scoped tasks and clearly represents participations rather than unique requests.

- [ ] Test due_at == now not overdue, due_at < now escalated, approved tasks excluded, changing sla_days does not change task deadlines, two scans/two workers record one event, concurrent terminal approval is not overwritten. Use injected fixed UTC time, no sleep-based assertions.
- [ ] Run suite; expected absent SLA worker/function fails.
- [ ] Implement indexed deadline scan (pending/processing), then lock/recheck parent before escalation; process each request in its own transaction for failure isolation; restartable loop handles transient DB error without secrets. Record system actor null, affected agencies and deadline. Enforce SLA 1–90 on create/edit; add average metric only when completed requests exist, otherwise null.
- [ ] Run SLA/concurrency/agency/dashboard tests; verify task counts are not mislabeled unique requests and active unrelated requests unaffected.
- [ ] Commit `feat: enforce agency deadlines with idempotent escalation`.

## Task 5: Scoped SSE signals

**Files:** Create live/service.py, routes.py, __init__.py, `backend/tests/test_live_updates.py`; modify main.py.
**Produces:** `scoped_revision(db:Session,actor:User)->str`, `iter_events(engine,session_token:str,poll_seconds:float=3)->AsyncIterator[str]`; GET `/live` StreamingResponse text/event-stream, no-store. Initial event `event: changed`, `data: {"revision":"opaque-digest"}`; every 15 seconds heartbeat; invalid/reassigned account emits session-invalid then closes.

- [ ] Test revisions change only for authorized requests or visible agency settings, two users have isolated results, already-connected staff reassignment/disable ends scope, JWT expiry closes stream, reconnect always emits initial refresh, no IDs/titles/passwords in event payload. Exercise finite iterator steps with injected clock/poll interval, not endless TestClient requests.
- [ ] Run suite; expected missing stream/service fails.
- [ ] Revision is SHA-256 of sorted scoped request id/version pairs and visible agency id/name/active/SLA values; admin also includes audit row ids. This snapshot design covers commits arriving in different event-id order. No in-memory broadcast state, no max-event-id-only cursor. Use a fresh short-lived session per poll, re-read user auth and assignment, perform sync DB work in a thread, support disconnect/cancellation, release dependency session before streaming. Set X-Accel-Buffering no; do not cache authenticated responses.
- [ ] Run isolation/lifetime tests; verify one initial frame and heartbeat with no long-running DB transaction.
- [ ] Commit `feat: stream scoped change signals for live status`.

## Task 6: Audit query and authentication events

**Files:** Create audit/routes.py, schemas.py, `backend/tests/test_audit_api.py`; modify auth/routes.py, audit/service.py, main.py.
**Produces:** GET `/audit?page=1&page_size=20&actor_id=&action=&entity_type=&from_date=&to_date=` admin only; ISO UTC datetime bounds, start inclusive/end exclusive; page_size 1–100. Rows include actor display name or system, action/entity/id/changes/time.

- [ ] Test citizen/staff 403, pagination/filter boundaries, successful login/logout records, failed login records generic action without submitted email/password/token/cookie, staff creation never writes password. Assert sensitive keys/values absent from changes.
- [ ] Run suite; expected missing audit API fails.
- [ ] Implement transactional records before returning auth cookies; logout identifies valid actor if available, logs generic anonymous logout otherwise. Add explicit auth audit action allowlist and parameterized queries; never serialize password_hash. Failed login may return 401 after committing its generic audit event.
- [ ] Run audit/auth regression suite and failure rollback tests; adjust SLA/live tests if added audit changes legitimately trigger admin refresh.
- [ ] Commit `feat: expose admin audit history and auth events`.

## Task 7: Live detail and parallel staff UI

**Files:** Create frontend/src/api/useLiveUpdates.ts, components/WorkflowTasks.tsx; modify api/types.ts, api/useData.ts, auth/AuthProvider.tsx, components/AppShell.tsx, pages/RequestDetail.tsx, pages/Dashboard.tsx, styles/redesign.css; create tests/live-updates.test.tsx.
**Consumes:** Task representation and stream/task APIs above. `useLiveUpdates(user:User|null):void` mounts once in provider; dispatches `sgwa:data-changed`. useData refetches on this event with latest-response ordering protection and retains existing data during background refresh.

- [ ] Test background update leaves draft/decision note intact, old in-flight response cannot replace newer result, EventSource cleaned up on logout, reconnect refreshes once, session-invalid dispatches existing unauthorized event. Add browser test with two page contexts: citizen watches while staff updates, no citizen refresh click needed.
- [ ] Run unit/browser new cases; expected missing live behavior fails.
- [ ] Implement one stream per authenticated provider. Task cards show agency/status/deadline/note; staff controls only their task, admin final review and multi-agency reroute shown separately. Task/request versions read at action time; conflicts require refresh and fresh confirmation. Route live changes never reset controlled form state. Show offline reconnect status without creating multiple retry loops.
- [ ] Dashboard shows real overdue count and completed-hours metric with empty value explanation; agency distribution label specifies task participation. CSS follows existing civic theme and supports 375/768/1366, reduced motion and keyboard controls.
- [ ] Run unit suite and browser regressions including expired citizen/staff draft tests.
- [ ] Commit `feat: show live multi-agency progress and deadlines`.

## Task 8: Admin route, SLA and audit screens

**Files:** Create pages/WorkflowRoutes.tsx, pages/AuditLogs.tsx; modify pages/Agencies.tsx, api/types.ts, components/AppShell.tsx, App.tsx, frontend/e2e/demo.spec.ts.

- [ ] Add browser tests: admin sets Perizinan + Pajak rule, adjusts SLA, submits citizen request, each agency sees own task, first approval not final, second final, citizen sees result automatically; audit filters find related actions. Unauthorized direct admin screen navigation remains guarded.
- [ ] Run new browser tests; expected missing screen fails.
- [ ] Implement /app/workflow and /app/audit with labelled native/Radix controls, immutable class code, list of active destinations, note that ML chooses primary class. Audit pagination resets on filter change and has loading/error/empty states. SLA input 1–90 and snapshot explanation in agency editor. Add workflow/audit navigation with mobile horizontal overflow restricted to nav.
- [ ] Run full browser suite, inspect screenshots for citizen/staff/admin detail and admin screens at 375/768/1366; verify no page overflow and keyboard selection/confirmation.
- [ ] Commit `feat: manage routing SLA and audit from admin workspace`.

## Task 9: Deployment-safe migration, verification and handover

**Files:** Modify docs/setup.md, docs/demo.md, docs/verification.md, README.md, scripts/test_backend.py if parameter selection is needed; add `docs/phase-one-verification.md`.

- [ ] Read engine version without credentials; inspect available EnvKit services read-only. Prefer an existing Oracle MySQL service. Otherwise document prerequisite/approved setup route; do not silently rename MariaDB as MySQL or switch user's existing databases.
- [ ] Back up sgwa_demo using DB tooling with local credentials, no secrets in logs; test migration on a separate validated test schema first. Never run drop_all or downgrade on application DB. Apply tested forward migration and restart own backend/worker only; smoke-test old demo records remain readable.
- [ ] Run `.venv\Scripts\python.exe scripts/test_backend.py`, frontend unit tests, TypeScript/Vite build, and all Edge e2e. Run migration suite on Oracle MySQL when available; otherwise record explicit outstanding engine verification and do not claim database requirement complete.
- [ ] Update demo guide for multi-dinas approval, SLA --once fixture, SSE refresh, audit filters and old data. Document worker command/startup, route semantics, calendar-day SLA and manual review behavior.
- [ ] Use one independent final reviewer through executing-plans; fix important findings with red/green regression checks, then rerun affected checks. Record measured counts, engine and limitations. Do not fabricate load-test or production-readiness claims.
- [ ] Commit verified changes and leave them in local project branch; no push/PR/deployment without user request.

## Self-review and Handoff

Spec tahap 1 dipetakan ke Tasks 1–9. Profile/form builder/notifikasi persisten/laporan/sertifikat demo/mock API/cross-validation/CI/load/security berada di tahap 2/3, bukan hilang dari backlog. Task 5 SSE ditujukan untuk perubahan tahap 1, bukan pusat notifikasi warga.

Interface source-code route, request/task version, SLA snapshot, human-review reset, and SSE signal schemas have been checked against the design. Existing execution preference is native in this chat: implementer works here, with one final independent reviewer. Written plan review remains required before product code or migration starts.
