import {expect,type Browser} from '@playwright/test';
import {readFileSync} from 'node:fs';
const password=readFileSync('../.env','utf8').split(/\r?\n/).find(line=>line.startsWith('DEMO_PASSWORD='))!.slice(14);
export async function manualRoute(browser:Browser,detail:string,agency:string,companion?:string){
 const context=await browser.newContext({baseURL:'http://127.0.0.1:5173'}),page=await context.newPage();
 try{
  await page.goto('/login');await page.getByLabel('Email',{exact:true}).fill('admin@demo.sgwa.id');await page.getByLabel('Password',{exact:true}).fill(password);await page.getByRole('button',{name:'Masuk',exact:true}).click();await expect(page).toHaveURL(/\/app/);
  await page.goto(detail);await expect(page.getByText('Perlu review',{exact:true}).first()).toBeVisible();
  await page.getByLabel('Alihkan ke dinas').selectOption({label:agency});if(companion)await page.getByLabel(companion,{exact:true}).check();
  await page.getByLabel('Catatan keputusan').fill('Admin memverifikasi tujuan pada pengujian sintetis, routing otomatis nonaktif.');await page.getByRole('button',{name:'Alihkan permohonan'}).click();await expect(page.getByText('Menunggu',{exact:true}).first()).toBeVisible();
 }finally{await context.close()}
}
