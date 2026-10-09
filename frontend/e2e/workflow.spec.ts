import {test,expect,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';
const password=readFileSync('../.env','utf8').split(/\r?\n/).find(line=>line.startsWith('DEMO_PASSWORD='))!.slice('DEMO_PASSWORD='.length);
async function login(page:Page,email:string){await page.goto('/login');await page.getByLabel('Email',{exact:true}).fill(email);await page.getByLabel('Password',{exact:true}).fill(password);await page.getByRole('button',{name:'Masuk',exact:true}).click();await expect(page).toHaveURL(/\/app/)}
async function logout(page:Page){await page.getByRole('button',{name:'Keluar',exact:true}).click();await expect(page).toHaveURL(/\/login$/)}

test('admin mengatur SLA dan dua dinas memproses satu permohonan',async({page,browser})=>{
 test.setTimeout(90000);
 await login(page,'admin@demo.sgwa.id');await page.goto('/app/workflow');await expect(page.getByRole('heading',{name:'Aturan routing layanan'})).toBeVisible();
 await page.getByLabel('Kelas utama').selectOption('perizinan');await page.getByLabel('DINAS KESEHATAN',{exact:true}).check();await page.getByRole('button',{name:'Simpan rute'}).click();await expect(page.getByText('Rute tersimpan.',{exact:true})).toBeVisible();
 await page.goto('/app/agencies');await page.locator('.agency-row').filter({hasText:'DINAS PENANAMAN MODAL DAN PELAYANAN TERPADU SATU PINTU'}).getByRole('button',{name:'Edit',exact:true}).click();
 await page.getByLabel('SLA (hari kalender)').fill('4');await page.getByRole('button',{name:'Simpan perubahan'}).click();await expect(page.getByText('SLA 4 hari kalender',{exact:false})).toBeVisible();
 await logout(page);await login(page,'warga@demo.sgwa.id');await page.goto('/app/requests/new');
 const title='Perizinan paralel '+Date.now();await page.getByLabel('Judul permohonan').fill(title);await page.getByLabel('Ceritakan kebutuhan Anda').fill('Saya ingin mengurus izin usaha dan izin mendirikan bangunan melalui dinas perizinan. Berkas perizinan usaha sudah siap.');await page.getByRole('button',{name:'Kirim permohonan'}).click();await expect(page).toHaveURL(/requests\/\d+$/);const detail=page.url();
 await expect(page.locator('.workflow-task')).toHaveCount(2);
 const ctx=await browser.newContext({baseURL:'http://127.0.0.1:5173'}),staff=await ctx.newPage();
 try{
  await login(staff,'perizinan@demo.sgwa.id');await staff.goto(detail);await staff.getByRole('button',{name:'Mulai proses'}).click();await staff.getByLabel('Catatan keputusan').fill('Perizinan lengkap; menunggu dinas lainnya.');await staff.getByRole('button',{name:'Disetujui',exact:true}).click();await staff.getByRole('button',{name:'Konfirmasi',exact:true}).click();await expect(page.locator('.page-heading .status')).toHaveText('Diproses',{timeout:12000});
  await logout(staff);await login(staff,'kesehatan@demo.sgwa.id');await staff.goto(detail);await staff.getByRole('button',{name:'Mulai proses'}).click();await staff.getByLabel('Catatan keputusan').fill('Pemeriksaan dinas kesehatan selesai.');await staff.getByRole('button',{name:'Disetujui',exact:true}).click();await staff.getByRole('button',{name:'Konfirmasi',exact:true}).click();await expect(page.locator('.page-heading .status')).toHaveText('Disetujui',{timeout:12000});
  await page.screenshot({path:'test-results/parallel-detail.png',fullPage:true});
 }finally{await ctx.close()}
 await logout(page);await login(page,'admin@demo.sgwa.id');await page.goto('/app/audit');await expect(page.getByRole('heading',{name:'Jejak aktivitas layanan'})).toBeVisible();await page.getByLabel('Filter aksi').fill('request.task_updated');await page.getByRole('button',{name:'Terapkan filter'}).click();await expect(page.getByText('request.task_updated',{exact:true}).first()).toBeVisible();
 for(const width of [375,768,1366]){await page.setViewportSize({width,height:900});await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:`test-results/audit-${width}.png`,fullPage:true})}
 await page.goto('/app/workflow');await page.getByLabel('Kelas utama').selectOption('perizinan');await page.getByLabel('DINAS KESEHATAN',{exact:true}).uncheck();await page.getByRole('button',{name:'Simpan rute'}).click();await expect(page.getByText('Rute tersimpan.',{exact:true})).toBeVisible();
});
