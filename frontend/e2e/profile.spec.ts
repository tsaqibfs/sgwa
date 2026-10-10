import {test,expect} from '@playwright/test';

test('profil dan perubahan password mengakhiri sesi dua browser',async({page,browser})=>{
 test.setTimeout(60000);
 const email=`profile-${Date.now()}@test.sgwa.id`,oldPassword='ProfileDemo123!',newPassword='ProfileChanged123!';
 await page.goto('/register');
 await page.getByLabel('Nama lengkap',{exact:true}).fill('Warga Profil');
 await page.getByLabel('Email',{exact:true}).fill(email);
 await page.getByLabel('Password',{exact:true}).fill(oldPassword);
 await page.getByRole('button',{name:'Buat akun & masuk',exact:true}).click();
 await expect(page).toHaveURL(/\/app$/);
 const other=await browser.newContext({baseURL:'http://127.0.0.1:5173'}),second=await other.newPage();
 try{
  await second.goto('/login');await second.getByLabel('Email',{exact:true}).fill(email);await second.getByLabel('Password',{exact:true}).fill(oldPassword);await second.getByRole('button',{name:'Masuk',exact:true}).click();await expect(second).toHaveURL(/\/app$/);
  await page.goto('/app/profile');await page.getByLabel('Nama lengkap',{exact:true}).fill('Nama Profil Baru');await page.getByLabel('Nomor telepon').fill('081234567');await page.getByRole('button',{name:'Simpan profil',exact:true}).click();await expect(page.getByText('Profil diperbarui.',{exact:true})).toBeVisible();await expect(page.locator('.profile strong')).toHaveText('Nama Profil Baru');
  await page.getByLabel('Password saat ini',{exact:true}).fill(oldPassword);await page.getByLabel('Password baru',{exact:true}).fill(newPassword);await page.getByLabel('Konfirmasi password baru',{exact:true}).fill('MismatchDemo123!');await page.getByRole('button',{name:'Ganti password',exact:true}).click();await expect(page.getByText('Konfirmasi password tidak sesuai.',{exact:true})).toBeVisible();
  await page.getByLabel('Konfirmasi password baru',{exact:true}).fill(newPassword);await page.getByRole('button',{name:'Ganti password',exact:true}).click();await expect(page).toHaveURL(/\/login$/);await expect(second).toHaveURL(/\/login$/,{timeout:12000});
  await page.getByLabel('Email',{exact:true}).fill(email);await page.getByLabel('Password',{exact:true}).fill(oldPassword);await page.getByRole('button',{name:'Masuk',exact:true}).click();await expect(page.getByRole('alert')).toBeVisible();await page.getByLabel('Password',{exact:true}).fill(newPassword);await page.getByRole('button',{name:'Masuk',exact:true}).click();await expect(page).toHaveURL(/\/app(?:\/profile)?$/);
 }finally{await other.close()}
});
