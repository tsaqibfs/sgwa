import {test,expect,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {manualRoute} from './manual-routing';
const seedPassword=readFileSync('../.env','utf8').split(/\r?\n/).find(line=>line.startsWith('DEMO_PASSWORD='))!.slice(14);
async function login(page:Page,email:string,password=seedPassword){await page.goto('/login');await page.getByLabel('Email',{exact:true}).fill(email);await page.getByLabel('Password',{exact:true}).fill(password);await page.getByRole('button',{name:'Masuk',exact:true}).click();await expect(page).toHaveURL(/\/app/)}

test('notifikasi persisten, simulasi, keputusan dan bukti cetak',async({page,browser})=>{
 test.setTimeout(120000);
 const email='service-'+Date.now()+'@test.sgwa.id',password='ServiceDemo123!';
 await page.goto('/register');await page.getByLabel('Nama lengkap').fill('Pemohon layanan sintetis');await page.getByLabel('Email',{exact:true}).fill(email);await page.getByLabel('Password',{exact:true}).fill(password);await page.getByRole('button',{name:'Buat akun & masuk',exact:true}).click();await expect(page).toHaveURL(/\/app$/);
 await page.goto('/app/notifications');await expect(page.getByRole('heading',{name:'Notifikasi',exact:true})).toBeVisible();
 await page.goto('/app/requests/new');await page.getByLabel('Judul permohonan').fill('Perizinan bukti '+Date.now());await page.getByLabel('Ceritakan kebutuhan Anda').fill('Saya ingin mengurus izin usaha dan izin mendirikan bangunan melalui dinas perizinan. Berkas perizinan usaha sudah siap.');await page.getByRole('button',{name:'Kirim permohonan',exact:true}).click();await expect(page).toHaveURL(/requests\/\d+$/);
 const detail=page.url();await expect(page.getByRole('link',{name:'Lihat bukti hasil'})).toHaveCount(0);await expect(page.getByRole('heading',{name:'Simulasi pemeriksaan'})).toHaveCount(0);
 await page.goto('/app/notifications');await expect(page.locator('.notification-row')).toHaveCount(1);await page.getByRole('button',{name:'Tandai dibaca',exact:true}).click();await expect(page.getByRole('link',{name:'Notifikasi, 0 belum dibaca'})).toBeVisible();
 await page.getByRole('button',{name:'Keluar',exact:true}).click();await login(page,email,password);await page.goto('/app/notifications');await expect(page.locator('.notification-row')).toHaveCount(1);await expect(page.getByText('Sudah dibaca',{exact:true})).toBeVisible();
 const context=await browser.newContext({baseURL:'http://127.0.0.1:5173'}),staff=await context.newPage();
 try{
  await manualRoute(browser,detail,'DINAS PENANAMAN MODAL DAN PELAYANAN TERPADU SATU PINTU');await expect(page.locator('.notification-row')).toHaveCount(2,{timeout:12000});
  await login(staff,'perizinan@demo.sgwa.id');await staff.goto(detail);
  for(const scenario of ['success','mismatch','unavailable']){
   await staff.getByLabel('Skenario simulasi').selectOption(scenario);await staff.getByRole('button',{name:'Jalankan simulasi',exact:true}).click();await expect(staff.locator('.mock-history').getByText(scenario,{exact:true})).toBeVisible();
  }
  await staff.getByLabel('Jenis pemeriksaan').selectOption('general_service');
  await staff.route('**/api/v1/requests/*/mock-checks',async route=>{if(route.request().method()==='POST'){await route.fetch();await route.abort('failed')}else await route.continue()},{times:1});
  await staff.getByRole('button',{name:'Jalankan simulasi',exact:true}).click();await expect(staff.getByRole('alert')).toBeVisible();
  await staff.getByRole('button',{name:'Jalankan simulasi',exact:true}).click();await expect(staff.locator('.mock-history article')).toHaveCount(4);
  await staff.getByRole('button',{name:'Mulai proses',exact:true}).click();await expect(page.locator('.notification-row')).toHaveCount(3,{timeout:12000});
  await staff.getByLabel('Catatan keputusan').fill('Dokumen sintetis telah diperiksa untuk demo akademik.');await staff.getByRole('button',{name:'Disetujui',exact:true}).click();await staff.getByRole('button',{name:'Konfirmasi',exact:true}).click();await expect(staff.getByRole('link',{name:'Lihat bukti hasil'})).toBeVisible();
  await page.goto(detail);await page.getByRole('link',{name:'Lihat bukti hasil'}).click();
  await expect(page.getByText('Bukti hasil demonstrasi akademik — bukan dokumen resmi',{exact:true})).toBeVisible();await expect(page.locator('.result-sheet').getByText('Pemohon layanan sintetis',{exact:true})).toBeVisible();await expect(page.getByText('Dokumen sintetis telah diperiksa untuk demo akademik.',{exact:true}).first()).toBeVisible();
  await page.emulateMedia({media:'print'});await expect(page.locator('.sidebar')).toBeHidden();await expect(page.locator('.topbar')).toBeHidden();await expect(page.getByRole('button',{name:'Cetak / simpan PDF'})).toBeHidden();await expect(page.locator('.result-sheet')).toBeVisible();await page.screenshot({path:'../.superpowers/sdd/2026-10-10-sgwa-ml-feedback/result-print.png',fullPage:true});
  await page.emulateMedia({media:'screen'});for(const width of [375,768,1366]){await page.setViewportSize({width,height:900});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)}
  const stranger=await browser.newContext({baseURL:'http://127.0.0.1:5173'}),other=await stranger.newPage();await login(other,'warga@demo.sgwa.id');await other.goto(detail+'/result');await expect(other.getByRole('alert')).toBeVisible();await expect(other.locator('.result-sheet')).toHaveCount(0);await stranger.close();
 }finally{await context.close()}
});

test('review admin menolak permohonan dan menyediakan bukti final',async({page})=>{
 test.setTimeout(60000);await login(page,'warga@demo.sgwa.id');await page.goto('/app/requests/new');
 await page.getByLabel('Judul permohonan').fill('zzzzz qqqqq demo');await page.getByLabel('Ceritakan kebutuhan Anda').fill('zzzzz qqqqq xxxxx yyyyy zzzzz qqqqq xxxxx');await page.getByRole('button',{name:'Kirim permohonan',exact:true}).click();await expect(page).toHaveURL(/requests\/\d+$/);const detail=page.url();
 await page.goto(detail+'/result');await expect(page.getByRole('alert')).toBeVisible();await expect(page.locator('.result-sheet')).toHaveCount(0);
 await page.getByRole('button',{name:'Keluar',exact:true}).click();await login(page,'admin@demo.sgwa.id');await page.goto(detail);await page.getByLabel('Catatan keputusan').fill('Data sintetis tidak cukup untuk diproses.');await page.getByRole('button',{name:'Ditolak',exact:true}).click();await page.getByRole('button',{name:'Konfirmasi',exact:true}).click();await page.getByRole('link',{name:'Lihat bukti hasil'}).click();await expect(page.locator('.result-sheet').getByText('Ditolak',{exact:true})).toBeVisible();await expect(page.getByText('Bukti hasil demonstrasi akademik — bukan dokumen resmi',{exact:true})).toBeVisible();
});
