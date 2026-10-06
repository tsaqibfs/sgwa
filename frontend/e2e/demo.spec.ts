import {test,expect,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';
const password=readFileSync('../.env','utf8').split(/\r?\n/).find(line=>line.startsWith('DEMO_PASSWORD='))?.slice('DEMO_PASSWORD='.length);
if(!password)throw new Error('DEMO_PASSWORD is required in .env');
test('navigasi keyboard langsung menuju konten dan halaman tidak ditemukan',async({page})=>{
 await page.setViewportSize({width:375,height:900});await page.goto('/');
 await expect(page.getByRole('link',{name:'Masuk',exact:true})).toBeVisible();await page.keyboard.press('Tab');
 await expect(page.getByRole('link',{name:'Lompat ke konten'})).toBeFocused();
 await page.keyboard.press('Enter');await expect(page.locator('main')).toBeFocused();
 await page.goto('/halaman-tidak-ada');await expect(page.getByRole('heading',{name:'Halaman tidak ditemukan'})).toBeVisible();
 await page.getByRole('link',{name:'Kembali ke beranda'}).click();await expect(page).toHaveURL(/\/$/);
});
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
 await expect(page.getByText('Disetujui',{exact:true}).first()).toBeVisible();await logout(page);await login(page,'warga@demo.sgwa.id');await page.goto(detail);await expect(page.locator('.timeline').getByText('Dokumen lengkap dan tervalidasi pada demonstrasi.')).toBeVisible();
});

test('admin menambah dinas dan mengalihkan kasus eskalasi',async({page})=>{
 await login(page,'warga@demo.sgwa.id');await page.goto('/app/requests/new');
 await page.getByLabel('Judul permohonan').fill('zzzzz qqqqq xxxxx');await page.getByLabel('Ceritakan kebutuhan Anda').fill('zzzzz qqqqq xxxxx yyyyy zzzzz qqqqq');await page.getByRole('button',{name:'Kirim permohonan'}).click();await expect(page).toHaveURL(/requests\/\d+$/);const detail=page.url();
 await expect(page.getByText('Perlu review',{exact:true}).first()).toBeVisible();await logout(page);await login(page,'admin@demo.sgwa.id');await page.goto('/app/agencies');
 const code='pendidikan_'+Date.now(),name='Dinas Pendidikan Demo '+Date.now();
 await page.getByLabel('Kode dinas').fill(code);await page.getByLabel('Nama dinas').fill(name);await page.getByRole('button',{name:'Tambah dinas',exact:true}).click();await expect(page.getByText(name,{exact:true})).toBeVisible();
 await page.goto(detail);await page.getByLabel('Catatan keputusan').fill('Ditinjau admin untuk kebutuhan layanan pendidikan.');await page.getByLabel('Alihkan ke dinas').selectOption({label:name});await page.getByRole('button',{name:'Alihkan permohonan'}).click();await expect(page.getByText('Menunggu',{exact:true}).first()).toBeVisible();await expect(page.locator('.workflow-task').getByText(name,{exact:true})).toBeVisible();
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
 for(const width of [375,768,1366]){
  await page.setViewportSize({width,height:900});await page.goto('/');await expect(page.getByRole('heading',{name:/Kebutuhan Anda/})).toBeVisible();
  await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await page.screenshot({path:`test-results/home-${width}.png`,fullPage:true});
 }
 await page.goto('/app/requests/new');await page.screenshot({path:'test-results/request-form.png',fullPage:true});
});

test('draft bertahan ketika sesi berakhir dan warga login ulang',async({page,context})=>{
 await login(page,'warga@demo.sgwa.id');await page.goto('/app/requests/new');
 await page.getByLabel('Judul permohonan').fill('Draft KTP belum dikirim');
 await page.getByLabel('Ceritakan kebutuhan Anda').fill('Saya ingin mengurus kartu identitas tetapi sesi login berakhir.');
 await context.clearCookies();await page.getByRole('button',{name:'Kirim permohonan'}).click();
 await expect(page).toHaveURL(/\/login$/);await login(page,'warga@demo.sgwa.id');
 await expect(page.getByLabel('Judul permohonan')).toHaveValue('Draft KTP belum dikirim');
});

test('catatan keputusan staf bertahan saat sesi berakhir',async({page,context})=>{
 await login(page,'warga@demo.sgwa.id');await page.goto('/app/requests/new');
 const title='KTP review catatan '+Date.now();
 await page.getByLabel('Judul permohonan').fill(title);await page.getByLabel('Ceritakan kebutuhan Anda').fill('Saya ingin mengurus KTP elektronik yang hilang dan kartu keluarga di Dukcapil.');
 await page.getByRole('button',{name:'Kirim permohonan'}).click();await expect(page).toHaveURL(/requests\/\d+$/);const detail=page.url();
 await logout(page);await login(page,'dukcapil@demo.sgwa.id');await page.goto(detail);await page.getByRole('button',{name:'Mulai proses'}).click();
 const note='Catatan panjang hasil verifikasi dokumen warga yang harus tetap ada setelah login ulang.';
 await page.getByLabel('Catatan keputusan').fill(note);await page.getByRole('button',{name:'Disetujui',exact:true}).click();
 await context.clearCookies();await page.getByRole('button',{name:'Konfirmasi',exact:true}).click();await expect(page).toHaveURL(/\/login$/);
 await login(page,'dukcapil@demo.sgwa.id');await expect(page.getByLabel('Catatan keputusan')).toHaveValue(note);
 await expect(page.getByRole('dialog')).not.toBeVisible();
});

test('warga melihat progres dinas otomatis dan draft tetap utuh',async({page,browser})=>{
 await login(page,'warga@demo.sgwa.id');await page.goto('/app/requests/new');
 await page.getByLabel('Judul permohonan').fill('KTP live '+Date.now());await page.getByLabel('Ceritakan kebutuhan Anda').fill('Saya ingin mengurus KTP elektronik dan kartu keluarga penduduk di Dukcapil.');
 await page.getByRole('button',{name:'Kirim permohonan'}).click();await expect(page).toHaveURL(/requests\/\d+$/);const detail=page.url();
 await expect(page.getByRole('heading',{name:'Progres tiap dinas'})).toBeVisible();
 const ctx=await browser.newContext({baseURL:'http://127.0.0.1:5173'}),staff=await ctx.newPage();
 try{
  await login(staff,'dukcapil@demo.sgwa.id');await staff.goto(detail);await staff.getByRole('button',{name:'Mulai proses'}).click();
  await expect(page.getByText('Diproses',{exact:true}).first()).toBeVisible({timeout:12000});
  await page.goto('/app/requests/new');await page.getByLabel('Judul permohonan').fill('Draft lain belum selesai');await page.getByLabel('Ceritakan kebutuhan Anda').fill('Saya sedang menuliskan kebutuhan untuk permohonan berikutnya.');
  await staff.getByLabel('Catatan keputusan').fill('KTP selesai diproses pada pengujian live.');await staff.getByRole('button',{name:'Disetujui',exact:true}).click();await staff.getByRole('button',{name:'Konfirmasi',exact:true}).click();
  await expect(staff.getByText('Disetujui',{exact:true}).first()).toBeVisible();
  await expect(page.getByLabel('Judul permohonan')).toHaveValue('Draft lain belum selesai');
  await page.goto(detail);await expect(page.getByText('Disetujui',{exact:true}).first()).toBeVisible();
 }finally{await ctx.close()}
});
