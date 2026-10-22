# SGWA Laporan Layanan dan CSV Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Membuat laporan layanan terfilter dan ekspor CSV yang konsisten, aman untuk spreadsheet, dan mengikuti hak akses warga/staf/admin.

**Architecture:** Modul reports membaca tabel yang ada melalui scope permohonan dan transaksi laporan REPEATABLE READ tersendiri. Endpoint JSON mengembalikan filter efektif, summary dan satu halaman; endpoint CSV menyiapkan seluruh hasil terbatas sebelum audit/response. UI memakai filter applied yang sama untuk laporan dan unduhan, dengan download client berbagi autentikasi/error handling.

**Tech Stack:** Python>=3.11, FastAPI, SQLAlchemy2, Pydantic2, MySQL, csv standar, React19, TypeScript, Vitest, Playwright Edge, Docker Compose. Versi mengikuti lockfile proyek, tanpa dependensi runtime baru.

**Spec:** `docs/superpowers/specs/2026-10-13-sgwa-reports-design.md` (disetujui pengguna).

**Execution:** Pertahankan metode inline/native dari sesi sebelumnya: executing-plans, satu fresh whole-branch reviewer. Rencana ini perlu review pengguna sebelum eksekusi. Checkout tetap branch feature yang digunakan pengguna; tidak merge/push.

## Global Constraints

- Warga hanya permohonan miliknya; staf hanya permohonan dengan tugas dinasnya; admin seluruh permohonan. Scope sebelum filter/count/summary/page/CSV.
- Dinas filter memakai EXISTS pada workflow, termasuk pendamping; satu baris per permohonan. Dinas lain bagi staf403; staf tanpa dinas kosong; role tidak dikenal403; tanpa sesi401.
- Tanggal pengajuan WIB inklusif, konversi interval UTC; default UI awal bulan sampai hari ini Asia/Jakarta. Status hanya pending/processing/escalated/approved/rejected. Query tidak dikenal422.
- Page>=1 default1, page_size1–100 default20; urutan created_at DESC,id DESC. CSV tidak menerima pagination, maksimal5.000; lebih413 tanpa truncation; kosong tetap header.
- Selesai=approved+rejected, completion_rate0–1/null; durasi final nonnegatif dalam jam; overdue permohonan nonfinal dengan tugas pending/processing melewati due_at, hanya cakupan dinas efektif.
- CSV UTF-8 BOM, koma, CRLF; tepat10 kolom spec; tanggal WIB `YYYY-MM-DD HH:mm:ss+07:00`; confidence0–1; teks rentan formula diprefix apostrof. File server `sgwa-laporan-YYYYMMDD-HHMMSS.csv`.
- Laporan/CSV snapshot per request, bukan janji snapshot identik antar-request. Cache-Control no-store. Audit report.export_prepared hanya filter/jumlah/generated_at, setelah seluruh file siap; gagal audit membatalkan response.
- Tidak mengekspor owner/kontak/deskripsi/jawaban/catatan/feedback; tidak mengubah model/workflow/historis. Tidak ada migrasi, forecast, XLSX/PDF atau job ekspor pada tahap ini.
- Tes DB hanya schema berawalan sgwa_test dengan safety guard; tidak reset EnvKit atau Docker demo. Tidak mencetak environment/secret/backup. Native dan Docker terpisah, fixture smoke dibersihkan berdasarkan ID terverifikasi.

## Review Focus

1. Auth sudah memulai transaksi sebelum laporan; transaksi laporan harus RR sejak awal, konsisten ketika writer lain commit, dan tidak mengubah isolation transaksi endpoint lama (Task1).
2. Cell dengan kombinasi whitespace/control/BOM sebelum formula dan baris yang punya25workflow tidak boleh meloloskan formula atau menggandakan hasil/limit (Task2).
3. Server/proxy mengembalikan JSON/error saat unduhan; file palsu tidak boleh disimpan, dan401 tetap mengakhiri sesi seperti client JSON (Task3).
4. Respons filter lama datang terlambat atau filter applied berganti sebelum fetch selesai; tabel lama tidak boleh dipasangkan dengan unduhan filter baru (Task4).
5. Rebuild/startup native/Docker laporan tidak boleh mengubah pilihan model aktif, kandidat, prediksi lama atau data demo pengguna (Task5).

## File responsibilities dan setup eksekusi

- `backend/app/reports/schemas.py`: query strict dan response types; `service.py`: filter/scope, pagination/projection/summary; `session.py`: lifecycle snapshot RR; `csv_export.py`: cell safety/encoding/preparation/audit; `routes.py`: auth/validation/header/response.
- `frontend/src/api/client.ts`: shared fetch/error plus apiFile; `api/reports.ts`: report types/query/date/download helpers; `pages/Reports.tsx`: filter applied, report and download UI. Perubahan App/AppShell/CSS terfokus; `useData.ts` menambah fetching tanpa mengubah arti loading lama.
- Tes baru: `backend/tests/test_reports.py`, `test_report_csv.py`, `frontend/src/api/client.test.tsx`, `api/reports.test.tsx`, `api/useData.test.tsx`, `pages/Reports.test.tsx`, `frontend/e2e/reports.spec.ts`.
- Bukti: `docs/reports-verification.md`; update README/setup/demo/roadmap. Scratch hanya `.superpowers/sdd/2026-10-13-sgwa-reports/`.

Saat eksekusi: baca skills TDD/verification/worktree; periksa status/log, pertahankan perubahan pengguna. Buat ledger/brief di namespace ini. Runner scratch `run_tests.py` menerima argumen pytest, membaca TEST_DATABASE_URL eksplisit dari environment atau file test privat yang dipilih, memvalidasi lewat `backend.tests.safety.validated_test_url`, memakai tmp unik di namespace dan tidak fallback ke DATABASE_URL aplikasi. Jalankan baseline backend/ML dan frontend; catat hasil aktual, tidak menyalin angka fase ML.

Referensi transaksi yang telah diperiksa via Context7: [SQLAlchemy Session transaction isolation](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html). Isolation ditetapkan sebelum operasi DB pada Session baru; tidak diubah pada Session auth yang sudah berjalan.

### Task 1: Query, snapshot dan ringkasan laporan

**Files:** Create reports `__init__.py`, `schemas.py`, `session.py`, `service.py`; test `backend/tests/test_reports.py`. Tidak mengubah scoped_query atau get_session lama.

**Interfaces:**
- `ReportFilters`: date_from/date_to date|null, status Literal lima status|null, agency_id int>0|null; extra forbid, validator rentang. `ReportQuery` extends filters dengan page/page_size bounds di atas.
- `AgencyRef`: id:int, name:str. `ReportRow`: id/reference/title/status/created_at/updated_at, primary_agency:AgencyRef|null, agencies:list[AgencyRef], classification:{predicted_agency_code,confidence,model_version}|null. Waktu response string UTC ISO dengan Z.
- `ReportSummary`: total:int, by_status:dict[str,int], completed_count:int, completion_rate:float|null, overdue_count:int, average_completed_hours:float|null. `ReportResponse`: filters:ReportFilters, generated_at:str, page/page_size/total, summary, items:list[ReportRow].
- `get_report_session() -> Iterator[Session]`: Session baru bind `get_engine().execution_options(isolation_level='REPEATABLE READ')`, expire_on_commit=False, close/rollback saat exception. Route auth tetap menggunakan dependency lama.
- `effective_filters(actor:User,filters:ReportFilters)->ReportFilters`; `utc_bounds(filters)->tuple[datetime|null,datetime|null]`; `report_query(actor,filters)->Select`; `report_rows(db,statement,*,offset:int,limit:int)->list[ReportRow]`; `read_report(db,actor,query:ReportQuery,generated_at:datetime)->ReportResponse`.

- [x] Tulis failing tests `test_report_scope_filters_and_parallel_no_duplicates`, `test_wib_boundaries_and_strict_query_validation`, `test_summary_completion_duration_overdue_and_empty`, `test_page_order_and_batch_projection`, `test_report_rr_snapshot_without_changing_auth_isolation`. Fixtures owner A/B, staff dinas A/B/no agency, admin/unknown, main+companion workflows, final rejected/approved dan overdue. Assertion: B tidak ada pada scope A; companion matches sekali; by_status semua lima key; total/page_size independen; completed_count=approved+rejected; empty rate/duration null; tugas final bukan overdue; staf hanya deadline dinasnya. Dua connection dengan writer commit di antara pembacaan memberi snapshot lama yang konsisten; transaksi baru melihat update. Engine default tetap sebelumnya.
- [x] Run `.\.venv\Scripts\python.exe .superpowers/sdd/2026-10-13-sgwa-reports/run_tests.py backend/tests/test_reports.py -q`. Expected: FAIL reports belum tersedia.

Assertion unit batas WIB yang wajib dipakai:

```python
def test_wib_day_bounds():
    assert utc_bounds(ReportFilters(date_from=date(2026,10,13),date_to=date(2026,10,13))) == (
        datetime(2026,10,12,17), datetime(2026,10,13,17)
    )
```
- [x] Implement schema/service/session minimal sesuai interfaces. Salin filter saat membuat filter efektif, jangan mutate actor/filter asal. Bangun SELECT scope dari scoped_query dengan tambahan EXISTS. Konversi WIB memakai timezone UTC+7, tanpa dependency tzdata; tanggal yang tak bisa menjadi UTC valid menghasilkan validation422, bukan OverflowError500. Batch-load agencies/workflow/classification dengan id halaman. Count/summary/page dalam satu transaksi; generated_at diambil sekali, UTC naive untuk perbandingan DB. SQL aggregate hanya scoped requests, overdue EXISTS agar tak duplicate.
- [x] Ulangi focused command. Expected: semua PASS/zero skips pada MySQL; query projection tidak bertambah per row saat page_size naik. Tidak ada perubahan tabel/pointer model.
- [x] Commit `feat: read scoped reports with consistent MySQL summaries` hanya files Task1 dan hasil ledger.

### Task 2: Endpoint laporan, CSV lengkap dan audit

**Files:** Create `backend/app/reports/routes.py`, `csv_export.py`, `backend/tests/test_report_csv.py`; modify `backend/app/main.py`; extend `test_reports.py` untuk kontrak HTTP.

**Interfaces:** Consume Task1 types/service/session. `read_export_rows(db,actor,filters:ReportFilters,*,limit:int=5000)->list[ReportRow]` mengambil maksimal limit+1 request sebelum enrichment, raises HTTP413 bila lebih. `safe_csv_cell(value:str)->str`; `encode_csv(rows:list[ReportRow])->bytes`; `CsvArtifact` fields content:bytes,filename:str,generated_at:str; `prepare_export(db,actor,filters,generated_at:datetime)->CsvArtifact` membentuk bytes lalu audit/commit, tidak streaming DB.

- [x] Tulis failing HTTP tests `test_report_endpoint_auth_filters_and_cache`, `test_csv_scope_companion_all_pages_and_empty`, `test_csv_exact_limit_and_overflow_no_truncation`, `test_csv_unicode_controls_bom_and_escaping`, `test_export_audit_atomicity_and_history_unchanged`. Assertion: GET reports401/unknown403; invalid/extra422 termasuk CSV page/page_size; staff agency lain403; JSON summary/items hanya scope; semua header no-store. CSV21rows lebih dari page20 tetap lengkap; exactly5000 berhasil,5001 memberi413 JSON tanpa Content-Disposition attachment; workflow25 per request tidak menambah row count. Header tepat10kolom spec dan tidak memuat PII. Decoded utf-8-sig via csv.reader mengembalikan quote/koma/newline/Unicode semula selain sanitasi.
- [x] Parametrize cell tests untuk `=1+1`, ` +cmd`, `\t=1`, `\rtext`, `\ntext`, `\ufeff \t@x`, `\x00 \ufeff-1`, Unicode whitespace sebelum formula; semuanya diprefix apostrof. `Normal, "Indonesia"` tidak diprefix, numeric server tidak berubah. Assert timestamp boundary WIB dan historical pajak/model4 dibaca apa adanya. Audit berisi tepat filters/count/generated_at, tidak judul/identitas. Simulasi SQLAlchemyError saat query/audit memberi503 JSON dan tidak audit/file parsial; request/classification/result/pointer snapshots tetap.
- [x] Run runner Task1 dengan `backend/tests/test_reports.py backend/tests/test_report_csv.py -q`. Expected: FAIL endpoint/encoder belum tersedia.

Assertion pure cell yang wajib dipakai:

```python
def test_formula_after_mixed_prefix():
    assert safe_csv_cell('\ufeff \t@SUM(1)') == "'\ufeff \t@SUM(1)"
    assert safe_csv_cell('Normal, "Indonesia"') == 'Normal, "Indonesia"'
```
- [x] Implement GET `/api/v1/reports` dengan ReportQuery query-model strict dan GET `/api/v1/reports/requests.csv` dengan ReportFilters strict, require_role citizen/staff/admin, dependency report_session. Kasus staff agency None tetap empty tanpa melebar scope. CSV memakai csv.writer, UTF-8-sig dan CRLF. Deteksi awalan formula setelah semua whitespace/control/BOM awal; awalan tab/CR/LF langsung juga diprefix. Filename hanya timestamp server UTC; CSV timestamp WIB seconds. Response bytes dengan attachment/X-Report-Generated-At/no-store setelah prepare_export commit. JSON listing tidak audit. Registrasi router prefix `/api/v1`.
- [x] Ulangi focused suite lalu seluruh `backend/tests ml/tests -q` dengan runner. Expected: PASS/zero skips. Periksa audit rollback, limit dan 5.000 rows aktual, bukan stub threshold lebih rendah.
- [x] Commit `feat: export complete scoped CSV reports with safe cells and audit`.

### Task 3: Download client yang mengikuti auth/error

**Files:** Modify `frontend/src/api/client.ts`; create `frontend/src/api/client.test.tsx`, `api/reports.ts`, `api/reports.test.tsx`.

**Interfaces:** Consume ReportResponse/ReportRow shape Task1 dan CSV headers Task2. Pertahankan `api<T>(path,options):Promise<T>` dan bootstrapCsrf public API. Internal `request(path:string,options:RequestInit):Promise<Response>` membagi credentials/header/network+HTTPerror handling; `apiFile(path:string):Promise<{blob:Blob;filename:string;generatedAt:string|null}>`. `ReportFilterDraft` strings date_from/date_to/status/agency_id; `defaultReportFilters(now:Date):ReportFilterDraft` berdasarkan WIB; `reportSearch(filters,page?:number):string` omit kosong, page hanya jika supplied; `saveReportFile(file):void` anchor/objectURL lifecycle.

- [x] Tulis failing tests: JSON API existing success/error tetap; file success nonempty/kosong berheader;401 dispatch sgwa:unauthorized dan ApiError;413/503 JSON tidak menjadi Blob download; network error ApiError0;200 application/json bukanCSV ditolak ApiError502 dengan pesan format unduhan. Valid filename server diterima; path/quote filename tak aman fallback `sgwa-laporan.csv`. Assert credentials include, revokeObjectURL/anchor cleanup. Query CSV tidak page, query listing page20size tetap; date WIB pada `2026-10-31T18:00:00Z` menghasilkan awal/today `2026-11-01`.
- [x] Run dari frontend `npm run test -- --run src/api/client.test.tsx src/api/reports.test.tsxx`. Expected: FAIL apiFile/helper missing.

Assertion timezone helper:

```typescript
it('sets default month from WIB rather than host date',()=>{
 expect(defaultReportFilters(new Date('2026-10-31T18:00:00Z'))).toEqual({
  date_from:'2026-11-01',date_to:'2026-11-01',status:'',agency_id:''
 });
});
```
- [x] Implement shared request tanpa mengubah penanganan detail validation/network/status lama. Baca error JSON hanya untuk non-success; file sukses harus content-type text/csv, filename ASCII safe `[A-Za-z0-9._-]+.csv`, fallback di atas. apiFile hanya mengambil Blob, saveReportFile baru melakukan save. Types laporan di reports.ts mengikuti Task1 persis; query tidak berisi user/role/owner.
- [x] Ulangi focused lalu `npm run test -- --run` dan `npm run build`. Expected: PASS; client JSON regresi tidak berubah.
- [x] Commit `feat: download report files with consistent session and error handling`.

### Task 4: UI laporan, filter applied dan browser

**Files:** Create `frontend/src/pages/Reports.tsx`, `pages/Reports.test.tsx`, `api/useData.test.tsx`, `frontend/e2e/reports.spec.ts`; modify `App.tsx`, `components/AppShell.tsx`, `styles/redesign.css`, `api/useData.ts`.

**Interfaces:** Consume api/reports helpers Task3, ReportResponse/GET/CSV Task1–2. `useData<T>` menambah `fetching:boolean` yang true untuk setiap fetch termasuk background reload, false pada completion active; arti loading lama tetap. Reports menyimpan draft dan applied terpisah, page, downloadBusy/ref, downloadError. Fingerprint filters/page yang ditampilkan harus cocok applied/page sebelum download aktif; agency staff dinormalisasi ke user.agency_id agar echo cocok.

- [x] Tulis failing unit tests `test_filters_apply_reset_and_csv_use_applied_values`, `test_stale_response_cannot_pair_old_table_with_new_export`, `test_report_loading_empty_error_and_download_duplicate_guard`, `test_staff_scope_and_session_expiry_download`; useData test background fetching/stale response terabaikan dan loading lama tetap. Assert mengedit draft tidak fetch/export filter baru; apply/reset page1; saat filterB fetch tertahan, tableA tidak digunakan dan download disabled walaupun render effect belum selesai; responsA terlambat tidak menimpa B. Network/auth download error tidak menyimpan file;401 event/session behavior dipertahankan; busy mencegah2request. Defaultdate WIB, null rate/duration ditampilkan `—`.
- [x] Run focused `npm run test -- --run src/pages/Reports.test.tsx src/api/useData.test.tsx`. Expected: FAIL Reports/mekanisme fetching belum tersedia.

Assertion pada test stale-filter yang telah memasang mock GET filterB tertahan dan merender Reports:

```typescript
await user.click(screen.getByRole('button',{name:'Terapkan filter'}));
expect(screen.getByRole('button',{name:'Unduh CSV'})).toBeDisabled();
expect(fileRequestMock).not.toHaveBeenCalled();
```

Tetapkan copy tombol unduh persis **Unduh CSV**; `fileRequestMock` adalah vi.fn mock apiFile dalam test tersebut, tidak dipakai pada production.
- [x] Implement `/app/reports` Guard roles citizen/staff/admin dan menu Laporan layanan; layout panel/filter, ringkasan, tabel, pagination, waktu penyusunan, catatan rate/final/SLA dan confidence bukan akurasi. Agency dropdown via `/agencies` termasuk nonaktif bertanda `(nonaktif)`; staf cakupan tetap. Download disabled saat fetching/error/no matching result/busy, memakai applied values tanpa pagination. Busy download menahan apply/reset agar data/filter tidak berpindah saat save. Perubahan CSS hanya reports; tabel horizontal scroll dalam panel. Daftar request links id, tanpa PII.
- [x] Ulangi focused, seluruh frontend unit/build. Expected: PASS, tidak mengubah loading halaman existing.
- [x] Tulis/run Edge `reports.spec.ts`: citizenA punya permohonan unik, admin manual-route main+companion, staff dapat filtercompanion/lihat satu row; citizenB tak melihat A; admin CSV memuat semua hasilfilter bukan cuma page. Playwright download dibaca dari file dengan UTF8BOM/parser CSV, fileerror request503 tidak mengeluarkan event download dan filter tetap. Screenshots375/768/1366, body no overflow, keyboardlabels; semua data hanya schema E2E disiapkan via scripts.prepare_e2e/run_e2e_server, bukan native/demo.
- [x] Run dari frontend `npm run e2e -- e2e/reports.spec.ts`, lalu seluruh e2e. Expected: PASS termasuk existing ML/workflow tests; simpan screenshot/log di namespace plan ini. Task3/4 TypeScript lint/build harus tetap lolos.
- [x] Commit `feat: add role-scoped service reports and CSV download UI`.

### Task 5: Native/Docker, dokumentasi dan review akhir

**Files:** Create `docs/reports-verification.md`; modify README, docs/setup.md, docs/demo.md, docs/docker.md dan `docs/superpowers/specs/2026-10-10-sgwa-completion-roadmap.md`. Scratch smoke/backup/snapshots di namespace, backup privat di lokasi backup normal; tidak di Git.

**Interfaces:** API/CSV Task2, UI Task4. Tidak ada migrasi/model bootstrap baru; container_init tetap mempertahankan pointer. Endpoint lama dan scope belum berubah. Schema report RR tersendiri tidak mengubah default engine.

- [x] Run seluruh backend/ML via runner dan frontend unit/build; Edge penuh menggunakan schema E2E. Expected: PASS/zero skips, catat angka/durasi aktual. Jika perbaikan menambah tes atau mengubah production code, ulangi cek yang relevan dan seluruh regression sebelum completion.
- [x] Sebelum restart/rebuild: capture native/Docker active pointer/revision, ready candidate IDs, hash row classification/request/result/workflow dan schema0008; jangan cetak secret/isi row. Backup native privat sebagai perlindungan, tanpa reset. Snapshot sebelum worker berjalan dibuat saat API/worker berhenti sehingga tidak berkompetisi dengan perubahan SLA.
- [x] Jalankan native API terbarui, smoke tiga role JSON/filter/CSV/status401 dan fixture sintetis spesifik; bersihkan hanya fixture yang dibuat dan audit/notifications terkait berdasarkan ID/pemilik/name marker terverifikasi, tanpa melatih model atau mengubah data lain. Bandingkan baris lama/pointer sebelum worker diaktifkan lagi. Expected: HTTP contract PASS, old rows/pointer/candidates unchanged; audit ekspor baru boleh bertambah.
- [x] Rebuild `docker compose --env-file .env.docker -f compose.docker.yaml up --build -d --wait --wait-timeout 240`; verifikasi init0, frontend/backend/mysqlhealthy, worker berjalan, ML25/pointer/candidates unchanged dan report/CSV melalui Nginx8080. Ulangi startup dan smoke; tidak down-v atau mengganti EnvKit. Expected: PASS dan state model/data lama tetap. Fixture smoke container teridentifikasi dibersihkan.
- [x] Tulis panduan penggunaan filter/CSV, completion_rate mencakup rejected, limit5.000, waktu WIB/snapshot, audit prepared bukan saved, data excluded dan langkah E2E laptopbaru. Laporan verifikasi menyebut tes aktual, deployment, preservation dan batas; analytics prediktif/coverage/CI/TLS/load test tetap backlog. Periksa tidak ada klaim persentase otomatis atau peningkatan ML.
- [x] Commit `docs: verify native Docker reports and document scoped CSV usage`. Jalankan satu fresh whole-branch reviewer sesuai executing-plans dengan Base fase ini, spec/plan/ledger dan lima Review Focus. Regrade; Important/Critical satu pass RED→GREEN+full suite, Minor ledger/final defer. Review tidak mengubah branch atau data. Simpan decisions/bukti sebelum menghapus hanya scratch plan ini; pertahankan branch lokal, tidak merge/push, native/Docker user kembali aktif.

## Self-review rencana

Scope/filter/summary/transaksi Task1; API/CSV/audit/limit/error Task2; download/date/query/encoding client Task3; appliedUI/auth/races/responsiveness Task4; preservasi/deployment/docs/regression/review Task5. Review Focus1→test RR Task1;2→cell+workflow/limit Task2;3→invalid file/401 Task3;4→stale applied response Task4;5→snapshot deployment Task5. Interfaces types/field names dikonsumsi konsisten. Tidak ada tabel, migration, dependency atau fitur prediktif yang ditambahkan diam-diam. Perubahan status spec hanya merekam persetujuan pengguna.
