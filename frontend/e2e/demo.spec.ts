import {test,expect,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';
const password=readFileSync('../.env','utf8').split(/\r?\n/).find(line=>line.startsWith('DEMO_PASSWORD='))?.slice('DEMO_PASSWORD='.length);
if(!password)throw new Error('DEMO_PASSWORD is required in .env');
async function login(page:Page,email:string){if(!page.url().endsWith('/login'))await page.goto('/login');await page.getByLabel('Email',{exact:true}).fill(email);await page.getByLabel('Password',{exact:true}).fill(password!);await page.getByRole('button',{name:'Masuk',exact:true}).click();await expect(page).toHaveURL(/\/app(?:\/|$)/)}
async function logout(page:Page){await page.getByRole('button',{name:'Keluar',exact:true}).click();await expect(page).toHaveURL(/\/login$/)}

test('pengajuan warga diproses staf dan hasil muncul di timeline',async({page})=>{
 await login(page,'warga@demo.sgwa.id');await page.goto('/app/requests/new');
 const title='Pengurusan KTP demo '+Date.now();
 await page.getByLabel('Judul permohonan').fill(title);await page.getByLabel('Ceritakan kebutuhan Anda').fill('Saya ingin mengurus KTP elektronik yang hilang dan kartu keluarga penduduk di Dukcapil.');
 await page.getByRole('button',{name:'Kirim permohonan'}).click();await expect(page.getByRole('heading',{name:title})).toBeVisible();
 const detail=page.url();await expect(page.getByText('Menunggu',{exact:true}).first()).toBeVisible();
 await logout(page);await login(page,'dukcapil@demo.sgwa.id');await page.goto(detail);
 await page.getByRole('button',{name:'Mulai proses'}).click();await expect(page.getByText('Diproses',{exact:true}).first()).toBeVisible();
 await page.getByLabel('Catatan keputusan').fill('Dokumen lengkap dan tervalidasi pada demonstrasi.');await page.getByRole('button',{name:'Disetujui',exact:true}).click();await page.getByRole('button',{name:'Konfirmasi',exact:true}).click();
 await expect(page.getByText('Disetujui',{exact:true}).first()).toBeVisible();await logout(page);await login(page,'warga@demo.sgwa.id');await page.goto(detail);await expect(page.getByText('Dokumen lengkap dan tervalidasi pada demonstrasi.')).toBeVisible();
});

test('admin menambah dinas dan mengalihkan kasus eskalasi',async({page})=>{
 await login(page,'warga@demo.sgwa.id');await page.goto('/app/requests/new');
 await page.getByLabel('Judul permohonan').fill('zzzzz qqqqq xxxxx');await page.getByLabel('Ceritakan kebutuhan Anda').fill('zzzzz qqqqq xxxxx yyyyy zzzzz qqqqq');await page.getByRole('button',{name:'Kirim permohonan'}).click();await expect(page).toHaveURL(/requests\/\d+$/);const detail=page.url();
 await expect(page.getByText('Perlu review',{exact:true}).first()).toBeVisible();await logout(page);await login(page,'admin@demo.sgwa.id');await page.goto('/app/agencies');
 const code='pendidikan_'+Date.now(),name='Dinas Pendidikan Demo '+Date.now();
 await page.getByLabel('Kode dinas').fill(code);await page.getByLabel('Nama dinas').fill(name);await page.getByRole('button',{name:'Tambah dinas',exact:true}).click();await expect(page.getByText(name,{exact:true})).toBeVisible();
 await page.goto(detail);await page.getByLabel('Catatan keputusan').fill('Ditinjau admin untuk kebutuhan layanan pendidikan.');await page.getByLabel('Alihkan ke dinas').selectOption({label:name});await page.getByRole('button',{name:'Alihkan permohonan'}).click();await expect(page.getByText('Menunggu',{exact:true}).first()).toBeVisible();await expect(page.getByText(name,{exact:true})).toBeVisible();
 await page.goto('/app/model');await expect(page.getByRole('heading',{name:'Model yang bisa dijelaskan.'})).toBeVisible();await expect(page.getByText(code,{exact:false})).toBeVisible();
});

test('responsive layouts keyboard and screenshots',async({page})=>{
 await login(page,'warga@demo.sgwa.id');
 for(const width of [375,768,1366]){
  await page.setViewportSize({width,height:900});await page.goto('/app');await expect(page.getByRole('heading',{name:/Selamat datang/})).toBeVisible();
  await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await page.screenshot({path:`test-results/dashboard-${width}.png`,fullPage:true});
 }
 await page.goto('/app/requests/new');await page.getByLabel('Judul permohonan').focus();await page.keyboard.press('Tab');await expect(page.getByLabel('Ceritakan kebutuhan Anda')).toBeFocused();
 await page.goto('/');await page.setViewportSize({width:1366,height:900});await page.screenshot({path:'test-results/home.png',fullPage:true});
});

test('draft bertahan ketika sesi berakhir dan warga login ulang',async({page,context})=>{
 await login(page,'warga@demo.sgwa.id');await page.goto('/app/requests/new');
 await page.getByLabel('Judul permohonan').fill('Draft KTP belum dikirim');
 await page.getByLabel('Ceritakan kebutuhan Anda').fill('Saya ingin mengurus kartu identitas tetapi sesi login berakhir.');
 await context.clearCookies();await page.getByRole('button',{name:'Kirim permohonan'}).click();
 await expect(page).toHaveURL(/\/login$/);await login(page,'warga@demo.sgwa.id');
 await expect(page.getByLabel('Judul permohonan')).toHaveValue('Draft KTP belum dikirim');
});
