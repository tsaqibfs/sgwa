# SGWA ML 25 Kelas dan Feedback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Menghasilkan model 25 kelas dengan normalisasi, evaluasi kelompok, feedback admin terverifikasi, serta aktivasi dan rollback yang dapat didemonstrasikan.

**Architecture:** Dataset dasar dan feedback verified membentuk snapshot training; CLI menghasilkan artefak kandidat immutable. MySQL menyimpan feedback, registry, dan satu pointer aktif; backend memilih satu classifier snapshot per submit. Web admin menyediakan koreksi/verifikasi dan pengelolaan model tanpa mengubah workflow atau prediksi historis.

**Tech Stack:** Python >=3.11, FastAPI, SQLAlchemy 2, Alembic, Oracle MySQL, scikit-learn >=1.6,<2, joblib, React 19, TypeScript, Vitest, Playwright Edge, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-10-10-sgwa-ml-feedback-design.md`

**Execution:** Inline melalui executing-plans sesuai pilihan sesi sebelumnya, satu fresh whole-branch reviewer. Status: menunggu review rencana; belum ada implementasi produk.

## Global Constraints

- Kode label persis 25 kode `backend/app/agencies/catalog.py::AGENCIES`; label `pajak` tidak digunakan dalam dataset baru.
- Minimal 100 contoh per kelas, 10 keluarga per kelas, total minimal 2.500 contoh; holdout tetap 20% kelompok per kelas.
- Seed 42, 5-fold stratified group CV, TF-IDF unigram/bigram, Logistic Regression C=4 dan max_iter=1000.
- Threshold grid 0,70 sampai 0,95 langkah 0,05; accepted precision minimal 0,90 dan minimal 25 contoh diterima; gagal berarti auto-routing nonaktif.
- Feedback current verified saja menjadi training; provenance wajib explicit `synthetic_demo` atau `real`; evaluasi holdout selalu diberi label sintetis.
- Aktivasi kandidat berikutnya memerlukan manifest holdout sama dan macro-F1 tidak turun lebih dari 0,02; rollback hanya versi 25 kelas yang pernah aktif dan valid.
- Tidak menulis ulang prediksi/hasil historis, tidak reset database, tidak menyuntikkan permohonan dataset, tidak online learning atau otomatis aktivasi hasil retraining.
- Native dan Docker terpisah; backup sebelum migrasi; pengujian destruktif hanya schema khusus dengan safety guard yang ada.
- Pertahankan checkout feature yang telah dipakai pengguna; periksa status sebelum menulis. Tidak merge/push. Skill using-git-worktrees tetap dibaca untuk memastikan keputusan checkout dicatat.
- Normalizer versioned dan deterministik; no fuzzy correction; single-label primary + workflow multi-dinas. Tampilan SGWA dipertahankan.

## Review Focus

1. Feedback dengan teks sama setelah normalisasi tetapi label berbeda tidak boleh dipakai diam-diam; Task 5 menguji conflict dan overlap.
2. Fold kehilangan satu kelas dapat menghasilkan probabilitas dengan urutan berbeda; Task 2 memvalidasi cakupan 25 label setiap fold sebelum menghitung OOF.
3. File aktif diganti/rusak setelah cache dibuat tidak boleh disamarkan oleh cache; Task 6 menguji pemeriksaan integritas dan kegagalan 503.
4. Aktivasi dua admin bersamaan dan submit yang sedang berjalan tidak boleh mencampur versi dengan threshold; Task 6 menguji concurrency dan snapshot.
5. Docker init kedua tidak boleh menimpa pilihan admin atau mengaktifkan kandidat yang belum direview; Task 8 menguji startup dua kali.

## File responsibilities dan antarmuka bersama

- `ml/text.py`: normalizer versioned dan hash; `ml/scenarios.py`: 25 x 10 keluarga; `ml/build_dataset.py`: generator/CSV/holdout manifest.
- `ml/evaluation.py`: fold, OOF, threshold, holdout metrics; `ml/train.py`: pipeline, validation dan packaging versi. `ml/tests/`: dataset/evaluation/artifact tests.
- `backend/app/ml/feedback.py`: transaksi revision/verification; `feedback_export.py`: snapshot dan grouping; `registry.py`: registrasi/activation/rollback/pointer; `runtime.py`: pemilihan classifier immutable.
- `backend/app/ml/routes.py`, `schemas.py`, `classifier.py`: API, payloads dan loader. `backend/app/models.py` plus migration `0008_ml_feedback.py`: tabel baru.
- `scripts/train_candidate.py`, `scripts/bootstrap_ml.py`: operator CLI; `scripts/container_init.py`: bootstrap aman. Backend Dockerfile menyertakan scripts tersebut.
- Frontend `components/ClassificationFeedback.tsx`, `pages/ModelFeedback.tsx`, `components/ModelVersions.tsx`: flow admin; halaman evaluasi menampilkan laporan aktual.

### Task 1: Normalisasi dan dataset 25 kelas

**Files:** Create `ml/text.py`, `ml/scenarios.py`, `ml/tests/test_dataset.py`; modify `ml/build_dataset.py`, `ml/data/requests.csv`; create `ml/data/holdout.json`.

**Interfaces:** `normalize_text(text: str, version: str = 'id-v1') -> str`; `text_hash(text: str, version: str = 'id-v1') -> str`; `build_dataset(path: Path, manifest_path: Path) -> dict`. CSV keys `text,label,group_id,provenance,dataset_version,text_hash`. Manifest keys `dataset_version,normalizer_version,seed,groups,rows_hash,manifest_hash`, `groups` sorted holdout group IDs. Dataset version `sgwa-25-synthetic-v1`.

- [ ] Write tests named `test_normalizer_is_conservative_and_idempotent`, `test_dataset_has_25_labels_and_stable_holdout`, `test_duplicate_normalized_text_is_rejected`. Assertions: `normalize_text('JLN  bnyk lampmer') == 'jalan banyak lampu merah'`, negation/names preserved, exact catalog labels, 2.500 rows, 250 groups, 50 holdout groups, repeated byte-identical exports, no normalized collisions/conflicting labels.
- [ ] Run `.\.venv\Scripts\python.exe -m pytest ml/tests/test_dataset.py -q`. Expected: FAIL missing module/API or 25-class assertions against old generator.
- [ ] Implement interfaces and 10 independent service families per class, 10 deterministic variants each, including informal language. Make CSV writing callable rather than only `__main__`; validate all groups/duplicates before publishing files. Manifest canonical JSON hash excludes its own hash field.
- [ ] Repeat the test command. Expected: PASS. Run `.\.venv\Scripts\python.exe -m ml.build_dataset`. Expected: exit 0, 25-label CSV and stable holdout manifest.
- [ ] Commit dataset/normalizer plus tests: `feat: add versioned Indonesian normalization and 25-class dataset`.

### Task 2: Group CV, threshold dan artefak

**Files:** Create `ml/evaluation.py`, `ml/tests/test_evaluation.py`; modify `ml/train.py`, `ml/tests/test_training.py`.

**Interfaces:** `train(dataset_path: Path, output_dir: Path, *, holdout_path: Path | None = None, feedback_manifest: dict | None = None) -> dict` continues returning report. `validate_artifacts(directory: Path) -> dict` verifies metadata/report/checksums/classes/normalizer and returns validated metadata before trusted deserialization. `choose_threshold(actual: list[str], predicted: list[str], confidence: list[float]) -> dict` returns `threshold,auto_routing_enabled,accepted_count,accepted_precision,coverage,grid`. `evaluate_groups(rows: list[dict], holdout: dict) -> dict` yields OOF plus fold manifest internally. Reports retain existing fields and add `cross_validation` with `folds,mean_macro_f1,std_macro_f1`, `routing_policy`, `holdout_manifest_hash`, `normalizer_version`, `provenance_counts`. metadata includes same identity/policy values.

- [ ] Write tests: `test_threshold_never_below_70_and_disables_when_no_candidate`, `test_cv_has_no_holdout_or_group_leakage`, `test_each_fold_has_all_classes`, `test_artifact_identity_includes_training_config`, `test_repeated_training_matches_report`. Check 25x25 matrix, 2.000 base train/500 holdout rows, 5 folds, fresh vectorizer excludes fold-only tokens, OOF threshold independent of holdout labels, no-class fold rejected, tampered manifest/duplicate rejected.
- [ ] Run `.\.venv\Scripts\python.exe -m pytest ml/tests -q`. Expected: FAIL old 4-class assumptions/missing CV policy.
- [ ] Implement explicit StratifiedGroupKFold loop `n_splits=5,shuffle=True,random_state=42`, validate fold classes, map probabilities by model.classes_, and fit final pipeline only after OOF. Use shared normalizer before features. Validate numeric fields finite, full report/metadata and checksums. Record actual library versions. Model ID `ml25-` + first 24 hex SHA256 canonical dataset/config/normalizer/manifest identity. Do not use holdout scores in threshold choice.
- [ ] Repeat test command. Expected: PASS, measured scores within [0,1], reproducible; no required perfect-score assertion. Commit `feat: evaluate 25-class model with grouped CV and validated routing policy`.

### Task 3: MySQL feedback et registry schema

**Files:** Modify `backend/app/models.py`; create `backend/alembic/versions/0008_ml_feedback.py`, `backend/tests/test_ml_migration.py`.

**Interfaces:** `MLFeedbackHead(request_id PK/FK,revision int,current_feedback_id nullable FK)`; `MLFeedback(id,request_id,revision,original_text,original_prediction JSON,training_text,text_hash,corrected_code FK agencies.code,provenance,family_key nullable,reason,status,created_by,created_at,reviewed_by nullable,reviewed_at nullable,review_note,idempotency_key,payload_hash)` with unique request/revision and actor/key. Status pending/verified/rejected/superseded. `MLModelVersion(id generated String(80),state ready/failed,relative_path,model_hash,metadata_json,evaluation_json,feedback_manifest JSON,created_at,registered_by nullable FK users.id,failure_reason nullable)`; `MLActiveModel(id=1,model_version_id nullable FK,revision int)`; `MLActivation(id,model_version_id,previous_version_id nullable,actor_id nullable,reason,kind bootstrap/activate/rollback,created_at)`. Singleton seeded by migration; no active model implicitly assigned.

- [ ] Write `test_ml_migration_empty_and_populated_0007` using existing migration test safety guards; assert old columns/rows unchanged, revision/current uniqueness, foreign keys, nullable empty pointer, upgrade repeat idempotent, downgrade to 0007 removes only new tables. No live EnvKit connection.
- [ ] Run `.\.venv\Scripts\python.exe .superpowers/run_tests.py backend/tests/test_ml_migration.py -q`. Expected: FAIL tables/revision missing.
- [ ] Add models and additive revision `down_revision='0007'` (verify actual revision identifier in file before implementing); create head FK after feedback table to avoid cycle during migration. Tables are created/dropped in deterministic dependency order for fixture `Base.metadata` compatibility.
- [ ] Repeat test command. Expected: PASS on isolated MySQL, zero skips. Commit `feat: persist ML feedback revisions and model registry`.

### Task 4: API koreksi/verifikasi

**Files:** Create `backend/app/ml/feedback.py`, `backend/tests/test_ml_feedback.py`; modify `backend/app/ml/routes.py`, `schemas.py`.

**Interfaces:** All below `/api/v1/ml`, admin role only. `GET /feedback?status=&provenance=&request_id=&page=1&page_size=20` returns `{items,total,page,page_size}`, max page_size100; `GET /feedback/{id}` returns snapshot/history. `POST /requests/{request_id}/feedback` payload `expected_revision` (0 initial), `training_text` 10..5000 trimmed chars, `corrected_code`, `provenance`, optional `family_key` 1..80 `[a-z0-9_-]+`, `reason` 3..1000 trimmed, `idempotency_key` 1..100; unknown keys forbidden. `POST /feedback/{id}/review` payload `expected_revision,decision` verified/rejected, `note` 3..1000. Service `create_feedback(db,actor,request_id,payload) -> MLFeedback`, `review_feedback(db,actor,feedback_id,payload) -> MLFeedback` owns commit/rollback.

- [ ] Write tests for admin-only/CSRF, invalid labels/provenance, server-owned original snapshot, exact idempotent retry/conflict, stale revision, revision supersedes old record, review cannot change a stale/nonpending revision, concurrent writes one winner, audit rolls back on failure. Preserve original request/workflow/result/classification before and after create/review; reroute alone creates no feedback. Reject whitespace-only training/reason.
- [ ] Run `.\.venv\Scripts\python.exe .superpowers/run_tests.py backend/tests/test_ml_feedback.py -q`. Expected: FAIL endpoint 404.
- [ ] Implement strict Pydantic payloads and server-side snapshot from title+' '+description/classification. Lock request then head consistently, create head safely, lock current revision with fresh reads under MySQL repeatable read. Idempotency compare before expected revision for successful lost-response retries, verify integrity-error cause explicitly; all writes and audit same transaction.
- [ ] Repeat test command. Expected: PASS. Commit `feat: capture and verify admin classification corrections`.

### Task 5: Feedback export et CLI kandidat

**Files:** Create `backend/app/ml/feedback_export.py`, `backend/app/ml/registry.py`, `scripts/train_candidate.py`, `ml/tests/test_feedback_export.py`, `backend/tests/test_ml_candidates.py`.

**Interfaces:** `snapshot_feedback(db: Session) -> dict` returns immutable manifest `{entries,snapshot_hash}`, entries only current verified ordered by request/revision; provenance/family included. `merge_feedback(base_rows: list[dict], holdout: dict, snapshot: dict) -> tuple[list[dict],dict]` yields merged rows plus manifest `{included,excluded,groups,snapshot_hash}`. `register_candidate(db: Session, directory: Path, actor_id: int | None) -> MLModelVersion`. CLI `.\.venv\Scripts\python.exe -m scripts.train_candidate --actor-email <admin email>` uses environment DB, server catalog, model_dir; refuses nonadmin, never activates.

- [ ] Write tests for snapshot current-only verified, repeat stable hash, normalized duplicate dedup/grouping, different-label conflict with IDs, family/request/hash transitive grouping, holdout overlap exclusion and counts, overlap base train same group, provenance mixed counts, insufficient fold groups, failed/incomplete staging not ready, repeat content ID doesn't duplicate registry. Family with mixed labels errors. A source collision linking multiple base groups errors instead of merging holdout/training silently.
- [ ] Run `.\.venv\Scripts\python.exe .superpowers/run_tests.py ml/tests/test_feedback_export.py backend/tests/test_ml_candidates.py -q`. Expected: FAIL missing modules.
- [ ] Export snapshot within consistent transaction, then release it before training. Union connected request/family/hash groups (and base group links), validate labels. Exclude any component touching holdout; report exclusions/reasons. Deduplicate final texts. Train in `MODEL_DIR/.staging/<uuid>`, validate using Task2 `validate_artifacts`, atomically publish immutable directory and register ready. Repeat existing ID requires identical manifest; errors record failed registry status with no activation and nonzero CLI exit. No externally supplied path accepted.
- [ ] Repeat test command. Expected: PASS. Commit `feat: train immutable candidates from verified feedback snapshots`.

### Task 6: Aktivasi, rollback dan runtime

**Files:** Create `backend/app/ml/runtime.py`, `backend/tests/test_ml_registry.py`; modify `classifier.py`, `routes.py`, `schemas.py`, `backend/app/main.py`, `backend/app/requests/routes.py`, `service.py`; adapt existing test fixtures using classifier stub.

**Interfaces:** `active_classifier(db: Session, app: FastAPI) -> Classifier`, `activate_model(db,actor,model_id,expected_revision,reason,kind='activate') -> dict`. API `GET /versions` returns `{active_model_id,revision,items}`; `GET /versions/{id}/evaluation`; `POST /versions/{id}/activate` and `/rollback` payload `expected_revision,reason` 3..1000. `Prediction` adds `threshold: float = .70`, `auto_routing_enabled: bool = True`; classifier derives them from validated metadata in same instance. Existing metadata/evaluation endpoints resolve active registry classifier.

- [ ] Write tests for 25-class validation/path traversal/unsupported normalizer/checksum/nonfinite threshold, first activation, >0.02 degradation rejected, different holdout rejected, rollback only previously activated valid version, stale/concurrent pointer one winner, registry audit atomicity, cache after file tamper yields503, no pointer gives503, exactly .70 accepted while .699 rejected, auto-routing disabled escalates, in-flight prediction carries original policy on activation. Historical classification/result unchanged and all role/form-routing guards retained.
- [ ] Run `.\.venv\Scripts\python.exe .superpowers/run_tests.py backend/tests/test_ml_registry.py backend/tests/test_request_edges.py backend/tests/test_contract.py backend/tests/test_workflow.py -q`. Expected: FAIL missing registry APIs/hardcoded0.60 policy.
- [ ] Reuse Task2 `validate_artifacts` before deserializing local joblib, resolved path confined to versions root, exact catalog/metadata/report classes, normalizer support and hash checks. Lock pointer for activation with expected revision; preserve audit/log. Candidate activation uses degradation gate; explicit rollback uses previously-active/same-holdout/integrity gates without the degradation gate so it remains possible to return to a known version. Cache immutable classifier with integrity signature/check before reuse, invalidate/fail on mismatch. Registry read binds classifier and threshold once per submit; do not use lifespan fixed classifier in production inference. Update stub tests deliberately to registry/runtime contracts rather than silently keeping production fallback. Legacy 4-class files remain archive only.
- [ ] Repeat test command. Expected: PASS; then `.\.venv\Scripts\python.exe .superpowers/run_tests.py backend/tests ml/tests -q`, Expected: all PASS zero skips. Commit `feat: activate and rollback validated models with consistent inference snapshots`.

### Task 7: Admin UI feedback et evaluasi

**Files:** Create `frontend/src/components/ClassificationFeedback.tsx`, `ModelVersions.tsx`, `frontend/src/pages/ModelFeedback.tsx`, `frontend/src/api/ml.ts`, `frontend/e2e/ml-feedback.spec.ts`; modify `RequestDetail.tsx`, `ModelEvaluation.tsx`, `api/types.ts`, `App.tsx`, `components/AppShell.tsx`, existing stylesheet for focused layout only; add `frontend/src/components/ClassificationFeedback.test.tsx`.

**Interfaces:** Use Task4/6 endpoint names and response fields; route `/app/model-feedback` admin-only. Evaluation keeps existing fields and adds Task2 fields. API types include feedback revision/status, provenance and model pointer revision. Training instructions display actual native/Docker CLI, no training web button or success fiction.

- [ ] Write component test for required explicit provenance, no submit with whitespace, duplicate action prevention and 409 retained edits; Edge E2E for admin create/review/revise, role denial, completed request unchanged, 25-class evaluation/grid, candidate activation/rollback, stale revision, persisted reload. Candidate fixtures via trusted CLI on isolated E2E DB only, no uploaded model or test-only production endpoint. Screenshot375/768/1366 and assert no body overflow.
- [ ] Run from frontend `npm run test -- --run src/components/ClassificationFeedback.test.tsx`; `npm run e2e -- e2e/ml-feedback.spec.ts`. Expected: FAIL missing component/UI.
- [ ] Implement UI using existing components. Show label “Evaluasi pada holdout sintetis”, CV mean/std, threshold/coverage, provenance counts, official agency names, horizontally scrollable matrix; activation reason and revision explicit. Detail correction panel separated from reroute; list paging; reviewed history immutable; 409 refresh with user edits retained for review.
- [ ] Repeat focused commands. Expected: PASS. Run `npm run test -- --run` and `npm run build`. Expected: PASS/exit0. Commit `feat: review classification feedback and manage model versions in admin UI`.

### Task 8: Native/Docker bootstrap, operasi dan verifikasi

**Files:** Create `scripts/bootstrap_ml.py`, `backend/tests/test_ml_bootstrap.py`, `docs/ml-feedback-verification.md`; modify `scripts/container_init.py`, `backend/Dockerfile`, `.superpowers/prepare_e2e.py`, test fixture server, README, docs/ml.md, docs/setup.md, docs/docker.md, docs/demo.md and completion roadmap actual status.

**Interfaces:** `bootstrap_ml() -> dict` native CLI `python -m scripts.bootstrap_ml`; first installs version25 and activation kind bootstrap, subsequent validates existing active unchanged. Container order migrations → seed → bootstrap → backfill. Operator Docker command `docker compose --env-file .env.docker -f compose.docker.yaml run --rm init python -m scripts.train_candidate --actor-email admin@demo.sgwa.id`, candidate-only. Training script included in image; same model_data write mount, backend read-only. Native uses corresponding Python venv command.

- [ ] Write `test_bootstrap_first_then_preserves_admin_active_and_candidate`, `test_missing_active_artifacts_fails_instead_of_retraining`, and populated0007upgrade+bootstrap test with row comparison. No reset/readback secrets. E2E fixture bootstrap active25; old historical fixture versions remain intact.
- [ ] Run `.\.venv\Scripts\python.exe .superpowers/run_tests.py backend/tests/test_ml_bootstrap.py -q`. Expected: FAIL old init always trains/direct artifacts.
- [ ] Implement bootstrap archive existing4class files under generated archive path before first install; valid pointer startup never retrains or chooses newest candidate. Document CLI training, evaluation, activation, rollback, data provenance, failure recovery and normalizer version semantics. Keep secrets/backup outside Git. No fake score promises.
- [ ] Repeat focused command then whole backend/ML, frontend unit/build, and full Edge E2E on isolatedDB. Expected: all PASS zero skips; record actual counts, durations, metrics and limitations. Do not claim old phaseA test counts as new results.
- [ ] Backup native EnvKit, verify Oracle MySQL, migrate/bootstrap while native API/worker stopped, compare old data, restart, login/metadata/submit feedback flow smoke. Rebuild Docker with `docker compose --env-file .env.docker -f compose.docker.yaml up --build -d --wait --wait-timeout 240`; inspect init exit0 and services healthy. Run second startup and verify active pointer unchanged, 25classes and Nginx API flow. Cleanup only identified smoke fixtures/relations; no broad delete. Expected: native/Docker successful separately with preserved old snapshots. Commands affecting Docker/Git/database require normal sandbox permissions as needed.
- [ ] Commit `feat: bootstrap 25-class ML safely in native and Docker deployments` with verified docs. Final whole-branch review via executing-plans required; Important/Critical findings one TDD fix pass, minors deferred. Keep local branch, no merge/push.

## Plan self-review

Spec coverage: dataset/normalizer Task1; CV/threshold/identity Task2; persistence/migrations Task3; correction/review Task4; feedback snapshot/grouping/candidate CLI Task5; activation/runtime/history Task6; UI Task7; bootstrap/docs/native/Docker Task8. Interfaces match payload and artifact fields. Review focus tests included explicitly. Main operational uncertainty is CV precision/coverage at 70% on synthetic data: report actual results and disable automatic routing if necessary, without lowering approved minimum or inventing scores.

Before execution, verify named existing test paths and actual migration IDs; record any required smallest correction in the ledger. TDD tests should use trusted generated small valid artifacts for cheap transaction cases, and full2500training only for ML integration tests.
