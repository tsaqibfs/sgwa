# SGWA Service Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking. User has selected inline execution; do not ask for the execution method again.

**Goal:** Ship profile/password, versioned service forms, persistent notifications, printable result documents and authenticated mock checks in the existing web application.

**Architecture:** Extend the modular FastAPI application with focused profile, forms, notifications, results and mocks modules. Domain writes use the same MySQL transaction as the existing request/workflow events; React consumes these APIs and the existing authenticated SSE stream. Alembic preserves historical requests and agency IDs.

**Tech Stack:** Python/FastAPI, SQLAlchemy/Alembic, MySQL, Argon2/PyJWT, React/TypeScript/Vite, Radix, pytest, Playwright, existing Docker Compose.

**Spec:** `docs/superpowers/specs/2026-10-10-sgwa-service-features-design.md`

## Global Constraints

- Database remains Oracle MySQL; never substitute SQLite for integration tests or reset application schemas.
- Profile name 2–150 characters; optional phone max 30; optional address max 500. Email, role and agency assignment are not profile-editable.
- Password 10–128 characters, current password required, new password must differ. Argon2 remains. Password/hash never enters audit/notification payloads.
- JWT session version must be checked on HTTP, CSRF bootstrap and SSE. Password change ends all existing sessions, including the caller.
- Forms have at most 30 uniquely keyed fields: text, textarea, number, date, select and checkbox. Published versions are immutable. No uploads or executable schema expressions.
- Form/ML agency mismatch enters human review; no-form submissions remain compatible.
- Notification `(user_id,event_key)` unique; result `request_id` and document number unique; mock `(actor_id,idempotency_key)` unique.
- Result text must contain: `Bukti hasil demonstrasi akademik — bukan dokumen resmi`.
- Native/EnvKit and Docker remain separate. Seed must preserve passwords and the 25-agency catalog; no automatic demo-history insertion.
- This plan does not implement phase B/C: 25-class training, feedback retraining, reports/forecast, CI, coverage target, TLS/limiter or load testing. Those remain in the approved roadmap and need their own detailed plans.

## Verification Convention

Use existing `backend/tests/conftest.py` helpers and only a TEST_DATABASE_URL accepted by `backend/tests/safety.py`. Configure it from local `.env` without printing credentials. Run tests with `.venv/Scripts/python.exe -m pytest -p no:cacheprovider --basetemp=.superpowers/test-tmp/<unique-run>`; create the parent first. Each command below assumes this configuration. A skipped MySQL test is not a pass.

Keep a plan-specific progress ledger under `.superpowers/sdd/2026-10-10-sgwa-service-features/`. Record RED/GREEN commands, commits and rulings. Continue through all tasks after plan review without asking to continue between tasks. Do not push, merge or deploy publicly.

## Review Focus

- JWT without version and stale CSRF/SSE after password change: reject the old session everywhere (tasks 1–2).
- Two form publications or a submit racing publication: immutable versions and 409 rather than silently validating against another schema (tasks 3–4).
- Staff reassignment/deactivation after a notification: preserve a generic notification without exposing an out-of-scope request link (tasks 5, 8).
- Legacy final requests with incomplete timeline and later renamed users/agencies: distinguish backfilled documents and preserve snapshots (task 6).
- Same mock idempotency key with different request/payload: reject 409 without overwriting the original result (task 7).

---

### Task 1: Profile API and session revocation

**Files:** Create `backend/app/profile/{__init__,schemas,service,routes}.py`, `backend/alembic/versions/0003_profile_sessions.py`, `backend/tests/test_profile.py`, `backend/tests/test_profile_migration.py`. Modify `backend/app/{models,main}.py`, `backend/app/auth/{service,routes,dependencies}.py`, `backend/app/live/service.py`, existing auth/live tests as needed for the versioned contract.

**Interfaces:** Produce `ProfileOut(id,name,email,role,agency_id,phone,address)`, `ProfileUpdate(name?,phone?,address?)`, `PasswordChange(current_password,new_password)`; GET/PATCH `/api/v1/profile`, POST `/api/v1/profile/password`. `make_session(user_id:int,session_version:int=1)->tuple[str,str]`. Produce a shared `session_actor(db:Session,token:str)->User` that validates JWT version and active user, consumed by HTTP authentication, authenticated CSRF bootstrap and SSE. Profile service `update_profile(db,actor,payload)->User`, `change_password(db,actor,payload)->None`; password mutation owns its locked transaction and audit.

- [x] Write API tests `test_profile_update_rejects_privilege_fields`, `test_password_requires_current_and_different_value`, `test_password_change_revokes_two_sessions`, `test_old_jwt_without_version_rejected`, `test_stale_csrf_and_sse_rejected`, `test_concurrent_password_change_verifies_locked_hash`. Assert 422 for extra/invalid profile keys, 401 for old sessions, hash changes once and audit contains no password/hash. Write migration test: existing user keeps hash/ID, session_version becomes 1, optional profile columns are NULL.
- [x] Run `pytest backend/tests/test_profile.py backend/tests/test_profile_migration.py -q` with convention above. Expected: RED because profile routes/schema/version are absent, not because database is unavailable.
- [x] Add the additive migration, models and strict Pydantic schemas; wire profile routes and shared versioned authentication. Lock and refresh the user before verifying current password; atomically hash/increment version/audit, then clear session/CSRF cookies. CSRF bootstrap clears invalid logged-in sessions and supplies anonymous CSRF; SSE terminates invalid sessions.
- [x] Repeat targeted tests and `pytest backend/tests/test_auth.py backend/tests/test_live_updates.py backend/tests/test_security_recovery.py -q`. Expected: all executed tests PASS, including legacy token rejection and logout/register behavior.
- [x] Commit `feat: add profile API and password session revocation` and ledger evidence.

### Task 2: Profile page and browser password flow

**Files:** Create `frontend/src/pages/Profile.tsx`, `frontend/e2e/profile.spec.ts`. Modify `frontend/src/{App.tsx,components/AppShell.tsx,auth/AuthProvider.tsx,api/types.ts}` and existing stylesheet where needed.

**Interfaces:** Consume task 1 APIs and existing `api<T>()`, `useAuth()`. Produce `/app/profile` for all roles. Auth context adds `refreshUser():Promise<void>` to refresh the displayed name; password change clears local auth state and redirects to login with a success message.

- [x] Write browser test registering a unique citizen, updating profile, and logging into a second browser context. Change password in the first; assert both sessions lose access, old password fails and new password succeeds. Verify required/current/confirm fields and mismatched confirmation prevents submission. No seed account password is changed by tests.
- [x] Run `npm.cmd --prefix frontend run e2e -- profile.spec.ts`. Expected: RED because profile page/fields are absent.
- [x] Implement profile/edit/password forms, error/loading/success states, accessible labels, navigation and auth refresh. Keep phone/address optional; email read-only. Confirm password in UI and do not cache password input.
- [x] Repeat test and `npm.cmd --prefix frontend run build`. Expected: browser PASS and TypeScript/Vite build exit 0.
- [x] Commit `feat: add profile and change password page` and ledger evidence.

### Task 3: Versioned forms API and request contract

**Files:** Create `backend/app/forms/{__init__,schemas,validation,service,routes}.py`, `backend/alembic/versions/0004_service_forms.py`, `backend/tests/test_service_forms.py`, `backend/tests/test_form_submission.py`, `backend/tests/test_form_concurrency.py`. Modify `backend/app/{models,main}.py`, `backend/app/requests/{schemas,service}.py`.

**Interfaces:** Produce `ServiceForm`, `ServiceFormVersion`; request `form_version_id:int|None`, `form_answers:dict|None`. Create schema `FormSchema(fields:list[FieldDefinition])` with exact supported types/limits. `validate_answers(schema:FormSchema,answers:dict)->dict`; `resolve_submission_form(db:Session,version_id:int,answers:dict)->ServiceFormVersion` locks the parent form and validates published/current/active state. Admin POST `/service-forms`, PATCH `/{id}/draft`, POST `/{id}/publish`, PATCH `/{id}` for active state; GET list/detail returns only active published data for non-admin. Optimistic `expected_version` protects draft/publish conflicts. Request detail includes immutable form version schema and answers.

- [x] Write tests covering each field type, required/optional values, unknown keys, duplicate keys, more than 30 fields, dates/options/ranges, inactive agencies/forms and role access. Assert a citizen cannot read drafts. Test old request retains old schema after publish; stale submit/publication race returns 409; conflicting ML class escalates; no-form request is unchanged. Assert unknown/incompatible schema fields are rejected rather than ignored.
- [x] Run `pytest backend/tests/test_service_forms.py backend/tests/test_form_submission.py backend/tests/test_form_concurrency.py -q`. Expected: RED for missing models/APIs/contract.
- [x] Add migration and focused modules, restrict schema/answers with no coercion that turns strings into booleans/numbers. Lock parent form before publication/submission, version uniquely and atomically. Integrate form checks before request insertion; mismatch sets needs_review and records why, while classification probabilities and original predicted label are preserved.
- [x] Repeat targeted tests and `pytest backend/tests/test_request_edges.py backend/tests/test_contract.py -q`. Expected: PASS, including prior no-form behavior.
- [x] Commit `feat: add versioned service forms and submission validation` and ledger evidence.

### Task 4: Form builder and dynamic citizen form

**Files:** Create `frontend/src/pages/ServiceForms.tsx`, `frontend/src/components/ServiceFormFields.tsx`, `frontend/e2e/service-forms.spec.ts`. Modify `frontend/src/{App.tsx,components/AppShell.tsx,pages/Requests.tsx,pages/RequestDetail.tsx,api/types.ts}` and stylesheet.

**Interfaces:** Consume task 3 schemas/APIs. Produce admin `/app/forms`, dynamic `ServiceFormFields({schema,answers,onChange,readOnly})`, optional service selector in NewRequest and historical form answers in RequestDetail. Number/boolean answers stay typed; date values are ISO dates. No-form payload omits both form properties.

- [x] Write browser scenario: admin creates/preview/publishes a form; citizen submits required answers; admin publishes another version; old detail still shows original labels/answers. Test invalid required input, optional form selection, inactive form and 409 publication race preserving citizen answers. Use separate synthetic accounts and record IDs for cleanup.
- [x] Run `npm.cmd --prefix frontend run e2e -- service-forms.spec.ts`. Expected: RED because builder/rendering absent.
- [x] Implement admin field editor and preview, citizen rendering and read-only historical detail. Catch stale-version 409, reload schema and retain entered values by stable key for user review without resubmitting silently.
- [x] Repeat browser test and `npm.cmd --prefix frontend run build`. Expected: PASS and build exit 0; inspect 375/768/1366px layouts for overflow.
- [x] Commit `feat: add service form builder and dynamic request UI` and ledger evidence.

### Task 5: Transactional notifications and SSE revisions

**Files:** Create `backend/app/notifications/{__init__,schemas,service,routes}.py`, `backend/alembic/versions/0005_notifications.py`, `backend/tests/test_notifications.py`, `backend/tests/test_notification_atomicity.py`. Modify `backend/app/{models,main}.py`, `backend/app/requests/service.py`, `backend/app/workflow/tasks.py`, `backend/app/live/service.py`; update SLA integration tests.

**Interfaces:** Produce `notify_request_event(db:Session,item:Request,event_key:str,kind:str,assigned_agency_ids:list[int])->None`, which never commits. Produce GET `/notifications?page=&page_size=`, GET `/notifications/unread-count`, PATCH `/{id}/read`, POST `/read-all`; list `{items,total,page,page_size}` and unread `{count}`. Notification serialization yields `can_open_request` based on current scope. Revision hashing includes only actor-owned notification id/read_at.

- [x] Write tests for submit/task/reroute/escalation/final recipients, owner-only mark-read, pagination/unread, staff reassignment, inactive recipients, retry deduplication and two concurrent task decisions. Inject notification insert failure; assert request/task versions, timeline and audit remain unchanged. Repeat SLA worker and assert one escalation notification per recipient.
- [x] Run `pytest backend/tests/test_notifications.py backend/tests/test_notification_atomicity.py -q`. Expected: RED because notification storage/events absent.
- [x] Add migration/API and no-commit notification service. Insert notifications before existing transaction commit in submit and workflow `finish`; use request id plus persisted version/event type as stable event_key. Keep SLA per-request transaction boundary through `finish`; no extra commit after notifications. Use nested savepoint handling only for expected unique-key duplicate, not to swallow real insert errors.
- [x] Repeat tests plus `pytest backend/tests/test_parallel_decisions.py backend/tests/test_sla.py backend/tests/test_live_updates.py -q`. Expected: PASS and actor-scoped SSE revision changes on read/new notification.
- [x] Commit `feat: persist transactional workflow notifications` and ledger evidence.

### Task 6: Immutable printable results and legacy backfill

**Files:** Create `backend/app/results/{__init__,schemas,service,routes}.py`, `backend/alembic/versions/0006_result_documents.py`, `scripts/backfill_results.py`, `backend/tests/test_result_documents.py`. Modify `backend/app/{models,main}.py`, `backend/app/workflow/tasks.py`, `scripts/container_init.py` and native setup docs.

**Interfaces:** Produce `ensure_result_document(db:Session,item:Request,converted:bool=False)->ResultDocument|None`, never commits; locks/reads final request and returns existing snapshot idempotently. Produce GET `/requests/{id}/result` authorized with existing request scope. Snapshot has document number, request reference, owner display name, status, finalized_at, notes, agency decisions/names and converted flag. Backfill uses this function on historical final requests in bounded transactions.

- [x] Write tests: approved/rejected generates one document, non-final is unavailable, rollback covers insert failure, second call is idempotent, name/profile edits do not change snapshot, wrong citizen/staff gets 404. Backfill incomplete historical timeline sets converted flag and preserves unavailable fields explicitly without invented timestamps/decisions.
- [x] Run `pytest backend/tests/test_result_documents.py -q`. Expected: RED because documents absent.
- [x] Add migration/API/service and invoke snapshot creation before final transaction commit in `finish`, after task state has flushed. Number format `SGWA-DEMO-<uuid>` with unique constraint. Use actual final event time when available; historical missing event time remains unavailable. Add idempotent backfill command after migration/seed to native and Docker init; no network calls or destructive reset.
- [x] Repeat tests plus notification/workflow tests. Expected: PASS; migration/backfill on historical approved/rejected records preserves source data and repeats safely.
- [x] Commit `feat: add immutable result documents and backfill` and ledger evidence.

### Task 7: Deterministic mock checks API

**Files:** Create `backend/app/mocks/{__init__,schemas,service,routes}.py`, `backend/alembic/versions/0007_mock_checks.py`, `backend/tests/test_mock_checks.py`. Modify `backend/app/{models,main}.py`.

**Interfaces:** GET/POST `/requests/{id}/mock-checks` restricted to scoped staff/admin; body `{check_type,scenario,idempotency_key}`. Types `identity`, `permit_completeness`, `general_service`; scenarios `success`, `mismatch`, `unavailable`. Service `run_mock_check(db,actor,item,payload)->MockCheck` returns stored deterministic synthetic payload, never grants workflow approval. Unavailable is a persisted simulated outcome, not an external HTTP failure.

- [x] Write tests for all outcomes/types, citizen rejection, out-of-scope staff, repeated key returning original ID, changed payload/request with same actor/key returning 409. Assert status/version of request unchanged and no external HTTP request occurs.
- [x] Run `pytest backend/tests/test_mock_checks.py -q`. Expected: RED because endpoint/table absent.
- [x] Add migration, strict schemas, fixture-based responses and audit without full private request text. Lock request scope, deduplicate atomically and reject payload conflicts. Label every response `simulation:true`.
- [x] Repeat targeted tests and workflow tests. Expected: PASS including concurrent identical key creating one row.
- [x] Commit `feat: add scoped deterministic mock service checks` and ledger evidence.

### Task 8: Notification inbox, mock UI and printable result page

**Files:** Create `frontend/src/pages/{Notifications,ResultDocument}.tsx`, `frontend/src/components/MockChecks.tsx`, `frontend/e2e/service-flow.spec.ts`. Modify `frontend/src/{App.tsx,components/AppShell.tsx,pages/RequestDetail.tsx,api/types.ts}` and stylesheet.

**Interfaces:** Consume tasks 5–7, existing live refresh event and task 4 request detail. Produce `/app/notifications` and `/app/requests/:id/result`; bell/unread indicator and read controls; request mock panel visible to staff/admin; print button uses `window.print()` and print-only layout.

- [x] Write browser tests for notification persistence across relogin, unread change via SSE, own-only request navigation, mock success/mismatch/unavailable, and final evidence via normal staff/admin decision flows. Assert demo label and source data; emulate print media and assert navigation/buttons hidden while result content remains visible. Non-final request has no result link; route guessing rejects access.
- [x] Run `npm.cmd --prefix frontend run e2e -- service-flow.spec.ts`. Expected: RED because inbox/results/mock UI absent.
- [x] Implement these UI routes/components, state/error handling and printable stylesheet. Refresh inbox/unread on scoped SSE without opening duplicate EventSource instances. Retain an idempotency key during mock retry, reset on changed request/type/scenario. Do not expose citizen controls for mock execution.
- [x] Repeat browser tests and frontend build. Expected: PASS; inspect screen and print layouts, including long agency names and notes.
- [x] Commit `feat: add persistent inbox mock checks and result printing UI` and ledger evidence.

### Task 9: Integration, migration and Docker verification

**Files:** Create `backend/tests/test_service_features_migration.py`, `docs/service-features-verification.md`. Update `README.md`, `docs/{setup,demo,docker}.md`, historical schema tests and E2E fixtures affected by new tables/session contracts. Add a safe test runner under `scripts/` only if needed to reproducibly set TEST_DATABASE_URL without printing secrets.

**Interfaces:** Consume all task contracts. Produce verifiable status documentation; five original demo accounts and 25 agencies remain, no form/request fixtures seeded implicitly. The final model is still the existing model: stage A completion must not claim 25-class/feedback features are already available.

- [x] Write upgrade test from migration 0002 populated synthetic historical requests to 0007, as well as fresh-schema migration, repeated backfill and seed. Assert all original IDs, password hashes, audit and workflow data survive; only documented new tables/columns/snapshots appear. Run RED before adjusting migration integration/setup behavior.
- [x] Run `pytest backend/tests/test_service_features_migration.py -q`. Expected: PASS after required integration fixes; genuine migration defect is investigated rather than masking test failure.
- [x] Run whole backend/ML suite with validated MySQL test schema and frontend production build. Run browser suite including new features. Expected: zero failures, no unconfigured-database skips counted as verified.
- [x] Rebuild full Docker using `docker compose --env-file .env.docker -f compose.docker.yaml up --build -d --wait --wait-timeout 240`. Expected: init exit 0, API/frontend/MySQL healthy, worker running. Verify actual migration 0007, 25 active agencies, login/CSRF, form submit, notifications, SSE, final result and mock outcomes through Nginx. Use only identifiable synthetic fixtures and clean their dependent rows from the tested container afterwards; never delete unrelated user data.
- [x] Update setup/demo/status docs from actual outputs. Record commands, executed test counts, environment, browser/migration proof and any limitations; do not claim phase B/C complete. Commit `docs: verify and document SGWA service features`.
- [x] Dispatch one fresh whole-change reviewer under executing-plans/requesting-code-review after all tasks; review from this plan's BASE, not only last commit. Fix critical/important findings with reproducing RED→GREEN tests and a green regression suite. Ledger rulings/minors and report them before branch integration; no merge/push without user request.

## Self-review and handoff

Coverage mapping: spec profile/session→1–2; form/version/mismatch→3–4; notifications/atomicity/SSE→5,8; result snapshot/backfill/print→6,8; mocks/scope/idempotency→7–8; upgrade/native/Docker/docs→9. Shared interfaces: user version/auth actor, form schema/answers, workflow `finish` transaction, live revision, result snapshot and mock payload. The five Review Focus cases have explicit tests above.

Plan status: complete: whole-change review and one verified fix pass finished; deferred minor documented. Native/inline execution already selected by the user; preserve it. After written-plan review, use executing-plans continuously through tasks 1–9. Later ML feedback training work remains phase B with its own spec/plan.
