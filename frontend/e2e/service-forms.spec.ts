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

test('hapus lalu tambah field tetap unik dan publikasi meminta draft tersimpan',async({page})=>{
 test.setTimeout(60000);await login(page,'admin@demo.sgwa.id');await page.goto('/app/forms');
 const title='Regresi builder '+Date.now();await page.getByLabel('Nama layanan',{exact:true}).fill(title);await page.getByLabel('Dinas layanan',{exact:true}).selectOption({label:'DINAS KEPENDUDUKAN DAN PENCATATAN SIPIL'});
 await page.getByRole('button',{name:'Tambah field',exact:true}).click();await page.getByRole('button',{name:'Tambah field',exact:true}).click();await page.getByRole('button',{name:'Hapus field 2',exact:true}).click();await page.getByRole('button',{name:'Tambah field',exact:true}).click();
 const keys=await page.locator('fieldset.builder-field input[pattern]').evaluateAll(inputs=>inputs.map(input=>(input as HTMLInputElement).value));expect(new Set(keys).size).toBe(keys.length);
 await page.getByRole('button',{name:'Simpan draft',exact:true}).click();await expect(page.getByText('Draft tersimpan.',{exact:true})).toBeVisible();
 await page.getByLabel('Label field 1',{exact:true}).fill('Label yang baru');await expect(page.getByRole('button',{name:'Publikasikan',exact:true})).toBeDisabled();
 await page.getByRole('button',{name:'Simpan draft',exact:true}).click();await expect(page.getByText('Draft tersimpan.',{exact:true})).toBeVisible();await page.getByRole('button',{name:'Publikasikan',exact:true}).click();await expect(page.getByText('Formulir dipublikasikan.',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Keluar',exact:true}).click();await login(page,'warga@demo.sgwa.id');await page.goto('/app/requests/new');await page.getByLabel('Layanan opsional').selectOption({label:title});await expect(page.getByLabel('Label yang baru',{exact:true})).toBeVisible();
});

test('publikasi tidak mengabaikan perubahan draft yang belum disimpan',async({page})=>{
 await login(page,'admin@demo.sgwa.id');await page.goto('/app/forms');await page.getByLabel('Nama layanan',{exact:true}).fill('Regresi dirty '+Date.now());await page.getByLabel('Dinas layanan',{exact:true}).selectOption({label:'DINAS KEPENDUDUKAN DAN PENCATATAN SIPIL'});await page.getByRole('button',{name:'Simpan draft',exact:true}).click();await expect(page.getByText('Draft tersimpan.',{exact:true})).toBeVisible();await page.getByLabel('Label field 1',{exact:true}).fill('Perubahan belum disimpan');await expect(page.getByRole('button',{name:'Publikasikan',exact:true})).toBeDisabled();
});

test('formulir nonaktif mempertahankan pilihan dan menolak retry teks implisit',async({page,browser})=>{
 test.setTimeout(60000);const admin=await browser.newContext({baseURL:'http://127.0.0.1:5173'}),other=await admin.newPage();await login(other,'admin@demo.sgwa.id');const headers={Origin:'http://127.0.0.1:5173','X-CSRF-Token':(await admin.cookies()).find(c=>c.name==='sgwa_csrf')!.value};const agencies=await (await admin.request.get('/api/v1/agencies')).json();const form=await (await admin.request.post('/api/v1/service-forms',{headers,data:{title:'Regresi nonaktif '+Date.now(),agency_id:agencies.find((a:{code:string})=>a.code==='dukcapil').id,fields:[{key:'nama',label:'Nama tersimpan',type:'text',required:true}]}})).json();await admin.request.post('/api/v1/service-forms/'+form.id+'/publish',{headers,data:{expected_version:1}});
 await login(page,'warga@demo.sgwa.id');await page.goto('/app/requests/new');await page.getByLabel('Layanan opsional').selectOption(String(form.id));await page.getByLabel('Nama tersimpan').fill('Jawaban dipertahankan');await page.getByLabel('Judul permohonan').fill('Pengurusan KTP');await page.getByLabel('Ceritakan kebutuhan Anda').fill('Saya ingin mengurus KTP dan kartu keluarga melalui dinas kependudukan dan pencatatan sipil.');await admin.request.patch('/api/v1/service-forms/'+form.id,{headers,data:{active:false}});await page.getByRole('button',{name:'Kirim permohonan',exact:true}).click();await expect(page.getByRole('alert').first()).toBeVisible();await expect(page.getByLabel('Nama tersimpan')).toHaveValue('Jawaban dipertahankan');await page.getByRole('button',{name:'Kirim permohonan',exact:true}).click();await expect(page).toHaveURL(/requests\/new$/);await expect(page.getByLabel('Layanan opsional')).toHaveValue(String(form.id));await admin.close();
});

test('perubahan tipe dan pilihan meminta review dan menghapus nilai aktif yang tidak cocok',async({page,browser})=>{
 test.setTimeout(90000);const admin=await browser.newContext({baseURL:'http://127.0.0.1:5173'}),other=await admin.newPage();await login(other,'admin@demo.sgwa.id');const headers={Origin:'http://127.0.0.1:5173','X-CSRF-Token':(await admin.cookies()).find(c=>c.name==='sgwa_csrf')!.value};const agencies=await (await admin.request.get('/api/v1/agencies')).json();const old=[{key:'check',label:'Jawaban checkbox lama',type:'text',required:false},{key:'amount',label:'Jawaban angka lama',type:'text',required:false},{key:'choice',label:'Pilihan lama',type:'select',options:['A','B'],required:false}];const form=await (await admin.request.post('/api/v1/service-forms',{headers,data:{title:'Regresi tipe '+Date.now(),agency_id:agencies.find((a:{code:string})=>a.code==='dukcapil').id,fields:old}})).json();await admin.request.post('/api/v1/service-forms/'+form.id+'/publish',{headers,data:{expected_version:1}});
 await login(page,'warga@demo.sgwa.id');await page.goto('/app/requests/new');await page.getByLabel('Layanan opsional').selectOption(String(form.id));await page.getByLabel('Jawaban checkbox lama').fill('nilai checkbox lama');await page.getByLabel('Jawaban angka lama').fill('nilai angka lama');await page.getByLabel('Pilihan lama').selectOption('A');await page.getByLabel('Judul permohonan').fill('Pengurusan KTP versi');await page.getByLabel('Ceritakan kebutuhan Anda').fill('Saya ingin mengurus KTP dan kartu keluarga melalui dinas kependudukan dan pencatatan sipil.');const fields=[{key:'check',label:'Checkbox terbaru',type:'checkbox',required:false},{key:'amount',label:'Angka terbaru',type:'number',required:false},{key:'choice',label:'Pilihan terbaru',type:'select',options:['B','C'],required:false}];await admin.request.patch('/api/v1/service-forms/'+form.id+'/draft',{headers,data:{expected_version:1,fields}});await admin.request.post('/api/v1/service-forms/'+form.id+'/publish',{headers,data:{expected_version:2}});
 await page.getByRole('button',{name:'Kirim permohonan',exact:true}).click();await expect(page.getByText('nilai checkbox lama',{exact:true})).toBeVisible();await expect(page.getByText('nilai angka lama',{exact:true})).toBeVisible();await expect(page.getByLabel('Angka terbaru')).toHaveValue('');await expect(page.getByLabel('Pilihan terbaru')).toHaveValue('');await page.getByRole('button',{name:'Saya sudah meninjau perubahan formulir',exact:true}).click();await page.getByRole('button',{name:'Kirim permohonan',exact:true}).click();await expect(page).toHaveURL(/requests\/\d+$/);await expect(page.getByText('Tidak',{exact:true})).toBeVisible();await admin.close();
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
  await adminPage.screenshot({path:'../.superpowers/sdd/2026-10-10-sgwa-ml-feedback/forms-'+width+'.png',fullPage:true});
 }
 await admin.close();
});
