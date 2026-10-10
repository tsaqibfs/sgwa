import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
const password=readFileSync('../.env','utf8').split(/\r?\n/).find(x=>x.startsWith('DEMO_PASSWORD='))!.slice('DEMO_PASSWORD='.length);
async function login(page:import('@playwright/test').Page,email:string){await page.goto('/login');await page.getByLabel('Email',{exact:true}).fill(email);await page.getByLabel('Password',{exact:true}).fill(password);await page.getByRole('button',{name:'Masuk',exact:true}).click();await expect(page).toHaveURL(/\/app/)}

test('admin menerbitkan formulir dan jawaban historis tetap terbaca',async({page})=>{
 test.setTimeout(75000);
 const title='Formulir usaha '+Date.now();
 await login(page,'admin@demo.sgwa.id');await page.goto('/app/forms');await expect(page.getByRole('heading',{name:'Formulir layanan',exact:true})).toBeVisible();
 await page.getByLabel('Nama layanan',{exact:true}).fill(title);await page.getByLabel('Dinas layanan',{exact:true}).selectOption({label:'DINAS PENANAMAN MODAL DAN PELAYANAN TERPADU SATU PINTU'});
 await page.getByLabel('Key field 1',{exact:true}).fill('nama_usaha');await page.getByLabel('Label field 1',{exact:true}).fill('Nama usaha');await page.getByLabel('Wajib field 1',{exact:true}).check();await page.getByRole('button',{name:'Simpan draft',exact:true}).click();await expect(page.getByText('Draft tersimpan.',{exact:true})).toBeVisible();await page.getByRole('button',{name:'Publikasikan',exact:true}).click();await expect(page.getByText('Formulir dipublikasikan.',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Keluar',exact:true}).click();await login(page,'warga@demo.sgwa.id');await page.goto('/app/requests/new');await page.getByLabel('Layanan opsional').selectOption({label:title});await page.getByLabel('Nama usaha',{exact:true}).fill('Usaha contoh');await page.getByLabel('Judul permohonan').fill('Perizinan formulir demo');await page.getByLabel('Ceritakan kebutuhan Anda').fill('Saya ingin mengurus izin usaha dan izin mendirikan bangunan melalui dinas perizinan. Berkas usaha sudah siap.');await page.getByRole('button',{name:'Kirim permohonan',exact:true}).click();await expect(page).toHaveURL(/requests\/\d+$/);const detail=page.url();await expect(page.getByText('Usaha contoh',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Keluar',exact:true}).click();await login(page,'admin@demo.sgwa.id');await page.goto('/app/forms');await page.getByRole('button',{name:'Edit '+title,exact:true}).click();await page.getByLabel('Label field 1',{exact:true}).fill('Nama usaha terbaru');await page.getByRole('button',{name:'Simpan draft',exact:true}).click();await page.getByRole('button',{name:'Publikasikan',exact:true}).click();await expect(page.getByText('Formulir dipublikasikan.',{exact:true})).toBeVisible();await page.goto(detail);await expect(page.getByText('Nama usaha',{exact:true})).toBeVisible();await expect(page.getByText('Nama usaha terbaru',{exact:true})).toHaveCount(0);
});

test('isian wajib, publikasi baru, layanan nonaktif dan ukuran layar',async({page,browser})=>{
 test.setTimeout(90000);
 const admin=await browser.newContext(),adminPage=await admin.newPage();
 await login(adminPage,'admin@demo.sgwa.id');
 const csrf=(await admin.cookies()).find(c=>c.name==='sgwa_csrf')!.value;
 const headers={Origin:'http://127.0.0.1:5173','X-CSRF-Token':csrf};
 const agencies=await (await admin.request.get('http://127.0.0.1:5173/api/v1/agencies')).json();
 const agency=agencies.find((a:{code:string})=>a.code==='perizinan');
 const fields=[{key:'nama',label:'Nama pemohon',type:'text',required:true}];
 const form=await (await admin.request.post('http://127.0.0.1:5173/api/v1/service-forms',{headers,data:{title:'Layanan race '+Date.now(),agency_id:agency.id,fields}})).json();
 const base='http://127.0.0.1:5173/api/v1/service-forms/'+form.id;
 expect((await admin.request.post(base+'/publish',{headers,data:{expected_version:1}})).status()).toBe(200);
 await login(page,'warga@demo.sgwa.id');await page.goto('/app/requests/new');
 await page.getByLabel('Layanan opsional').selectOption(String(form.id));
 await page.getByLabel('Judul permohonan').fill('Mengurus izin usaha');
 await page.getByLabel('Ceritakan kebutuhan Anda').fill('Saya ingin mengurus perizinan usaha di dinas perizinan, berkas sudah lengkap.');
 await page.getByRole('button',{name:'Kirim permohonan',exact:true}).click();
 expect(await page.getByLabel('Nama pemohon').evaluate((input:HTMLInputElement)=>input.validity.valueMissing)).toBe(true);
 await page.getByLabel('Nama pemohon').fill('Nilai tetap');
 expect((await admin.request.patch(base+'/draft',{headers,data:{expected_version:1,fields:[{...fields[0],label:'Nama baru'}]}})).status()).toBe(200);
 expect((await admin.request.post(base+'/publish',{headers,data:{expected_version:2}})).status()).toBe(200);
 await page.getByRole('button',{name:'Kirim permohonan',exact:true}).click();
 await expect(page.getByLabel('Nama baru')).toHaveValue('Nilai tetap');
 await expect(page.getByRole('alert')).toBeVisible();
 await expect(page).toHaveURL(/requests\/new$/);
 expect((await admin.request.patch(base,{headers,data:{active:false}})).status()).toBe(200);
 await page.reload();await expect(page.locator('select#request-service option[value="'+form.id+'"]')).toHaveCount(0);
 await adminPage.goto('/app/forms');
 for(const width of [375,768,1366]){
  await adminPage.setViewportSize({width,height:900});
  expect(await adminPage.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await adminPage.screenshot({path:'../.superpowers/sdd/2026-10-10-sgwa-service-features/forms-'+width+'.png',fullPage:true});
 }
 await admin.close();
});
