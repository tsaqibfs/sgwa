import {test,expect,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {manualRoute} from './manual-routing';
const password=readFileSync('../.env','utf8').split(/\r?\n/).find(line=>line.startsWith('DEMO_PASSWORD='))!.slice(14);
async function login(page:Page,email:string){await page.goto('/login');await page.getByLabel('Email',{exact:true}).fill(email);await page.getByLabel('Password',{exact:true}).fill(password);await page.getByRole('button',{name:'Masuk',exact:true}).click();await expect(page).toHaveURL(/\/app/)}
async function allDates(page:Page){await page.getByLabel('Tanggal awal (WIB)').fill('');await page.getByLabel('Tanggal akhir (WIB)').fill('');await page.getByRole('button',{name:'Terapkan filter'}).click();await expect(page.getByRole('button',{name:'Unduh CSV'})).toBeEnabled()}
async function csv(page:Page){
 const pending=page.waitForEvent('download');await page.getByRole('button',{name:'Unduh CSV'}).click();const file=await pending;
 expect(file.suggestedFilename()).toMatch(/^sgwa-laporan-\d{8}-\d{6}\.csv$/);const path=await file.path();expect(readFileSync(path!)[0]).toBe(0xef);
 const script='import csv,json,sys; data=list(csv.reader(open(sys.argv[1],encoding="utf-8-sig",newline=""))); print(json.dumps(data))';
 return JSON.parse(execFileSync(resolve('../.venv/Scripts/python.exe'),['-c',script,path!],{encoding:'utf8'})) as string[][];
}

test('laporan warga dan staf hanya mencakup permohonan sah termasuk dinas pendamping',async({page,browser})=>{
 test.setTimeout(120000);const stamp=Date.now(),email='report-'+stamp+'@test.sgwa.id';
 await page.goto('/register');await page.getByLabel('Nama lengkap').fill('Pemohon laporan sintetis');await page.getByLabel('Email',{exact:true}).fill(email);await page.getByLabel('Password',{exact:true}).fill(password);await page.getByRole('button',{name:'Buat akun & masuk',exact:true}).click();await expect(page).toHaveURL(/\/app$/);
 await page.goto('/app/requests/new');await page.getByLabel('Judul permohonan').fill('Laporan izin '+stamp);await page.getByLabel('Ceritakan kebutuhan Anda').fill('Saya mengurus izin usaha pada demonstrasi layanan yang memerlukan dua dinas.');await page.getByRole('button',{name:'Kirim permohonan'}).click();await expect(page).toHaveURL(/requests\/\d+$/);const detail=page.url(),request=await (await page.request.get('/api/v1/requests/'+detail.split('/').pop())).json();
 await manualRoute(browser,detail,'DINAS PENANAMAN MODAL DAN PELAYANAN TERPADU SATU PINTU','DINAS KESEHATAN');await page.goto('/app/reports');await allDates(page);
 await page.getByLabel('Dinas dalam laporan').selectOption({label:'DINAS KESEHATAN'});await page.getByRole('button',{name:'Terapkan filter'}).click();await expect(page.locator('.report-table tbody tr')).toHaveCount(1);
 const data=await csv(page);expect(data).toHaveLength(2);expect(data[1][0]).toBe(request.reference);expect(data[1][4]).toContain('DINAS KESEHATAN');expect(data[1][4]).toContain('DINAS PENANAMAN MODAL');expect(data[0]).not.toContain('email');
 const ctx=await browser.newContext({baseURL:'http://127.0.0.1:5173'}),other=await ctx.newPage();
 try{
  await login(other,'warga@demo.sgwa.id');const foreign=await (await other.request.get('/api/v1/reports')).json();expect(foreign.items.some((r:{id:number})=>r.id===request.id)).toBe(false);expect((await other.request.get('/api/v1/requests/'+request.id)).status()).toBe(404);
  await other.getByRole('button',{name:'Keluar',exact:true}).click();await login(other,'kesehatan@demo.sgwa.id');await other.goto('/app/reports');await allDates(other);await expect(other.getByLabel('Dinas dalam laporan')).toBeDisabled();await expect(other.getByRole('link',{name:request.reference})).toBeVisible();
  const agencies=await (await other.request.get('/api/v1/agencies')).json(),otherAgency=agencies.find((a:{code:string})=>a.code==='dukcapil').id;expect((await other.request.get('/api/v1/reports?agency_id='+otherAgency)).status()).toBe(403);
  expect((await csv(other)).slice(1).filter(r=>r[0]===request.reference)).toHaveLength(1);
 }finally{await ctx.close()}
});

test('CSV admin lengkap melewati satu halaman dan aman untuk formula, layar kecil dan keyboard',async({page,context})=>{
 test.setTimeout(120000);await login(page,'warga@demo.sgwa.id');const csrf=(await context.cookies()).find(c=>c.name==='sgwa_csrf')!.value,mark='CSV-'+Date.now(),references:string[]=[];
 for(let i=0;i<23;i++){
  const response=await page.request.post('/api/v1/requests',{headers:{Origin:'http://127.0.0.1:5173','X-CSRF-Token':csrf},data:{title:'=SUM(1) '+mark+'-'+i,description:'Permohonan sintetis pengurusan jalan lingkungan dan perbaikan ruas aspal.'}});expect(response.status()).toBe(201);references.push((await response.json()).reference);
 }
 await page.getByRole('button',{name:'Keluar',exact:true}).click();await login(page,'admin@demo.sgwa.id');await page.goto('/app/reports');await allDates(page);
 const summary=await (await page.request.get('/api/v1/reports')).json();expect(summary.total).toBeGreaterThan(20);await expect(page.locator('.report-table tbody tr')).toHaveCount(20);
 const data=await csv(page);expect(data.length-1).toBe(summary.total);for(const ref of references){const row=data.find(r=>r[0]===ref)!;expect(row).toBeTruthy();expect(row[1]).toMatch(/^'=SUM\(1\)/)}
 await page.getByLabel('Tanggal awal (WIB)').focus();const endDate=page.getByLabel('Tanggal akhir (WIB)');
 for(let i=0;i<6&&!await endDate.evaluate(el=>el===document.activeElement);i++)await page.keyboard.press('Tab');
 await expect(endDate).toBeFocused();
 for(const width of [375,768,1366]){await page.setViewportSize({width,height:900});await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:`../.superpowers/sdd/2026-10-13-sgwa-reports/reports-${width}.png`,fullPage:true})}
});

test('error CSV mempertahankan filter dan sesi berakhir tidak menghasilkan file palsu',async({page,context})=>{
 await login(page,'admin@demo.sgwa.id');await page.goto('/app/reports');await expect(page.getByRole('button',{name:'Unduh CSV'})).toBeEnabled();await page.getByLabel('Status permohonan').selectOption('pending');await page.getByRole('button',{name:'Terapkan filter'}).click();await expect(page.getByRole('button',{name:'Unduh CSV'})).toBeEnabled();
 let downloads=0;page.on('download',()=>downloads++);await page.route('**/api/v1/reports/requests.csv*',route=>route.fulfill({status:503,contentType:'application/json',body:'{"detail":"CSV belum tersedia"}'}),{times:1});await page.getByRole('button',{name:'Unduh CSV'}).click();await expect(page.getByRole('alert')).toHaveText('CSV belum tersedia');expect(downloads).toBe(0);await expect(page.getByLabel('Status permohonan')).toHaveValue('pending');
 await context.clearCookies();await page.getByRole('button',{name:'Unduh CSV'}).click();await expect(page).toHaveURL(/\/login$/);expect(downloads).toBe(0);
});
