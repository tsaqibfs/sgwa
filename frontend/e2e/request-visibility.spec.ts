import {test,expect} from '@playwright/test';

for(const role of ['citizen','staff','admin'] as const){
 test(`detail ${role}: panel ML khusus admin dan riwayat memakai bahasa umum`,async({page})=>{
  const department={id:1,name:'DINAS KEPENDUDUKAN DAN PENCATATAN SIPIL',code:'dukcapil',active:true,sla_days:3,description:''};
  const actor={id:1,name:'Pengguna uji tampilan',email:'visibility@example.invalid',role,agency_id:role==='staff'?1:null,active:true};
  const item={id:123,reference:'SGWA-VISIBILITY-DEMO',citizen_id:1,title:'Penggantian KTP contoh',description:'Permohonan sintetis untuk memeriksa tampilan hasil layanan.',status:'approved',version:3,assigned_agency_id:1,agency_name:department.name,created_at:'2026-10-24T14:00:00Z',updated_at:'2026-10-24T14:05:00Z',attachments:[],workflows:[{id:1,agency_id:1,agency_name:department.name,status:'approved',version:3,due_at:null,completed_at:'2026-10-24T14:05:00Z',decision_note:'Simulasi selesai.',overdue:false}],classification:{predicted_agency_code:'dukcapil',probabilities:{dukcapil:.9},confidence:.9,needs_review:true,model_version:'visibility-browser-fixture'},events:[{id:1,to_status:'processing',note:'Dinas #1: processing. Pemeriksaan contoh.',created_at:'2026-10-24T14:01:00Z'},{id:2,to_status:'approved',note:'Dinas #1: approved. Simulasi selesai.',created_at:'2026-10-24T14:05:00Z'}]};
  // Mock API data tests presentation independently; backend permission tests use MySQL.
  await page.route('**/api/v1/**',async route=>{
   const path=new URL(route.request().url()).pathname;
   if(path==='/api/v1/live'){await route.fulfill({status:200,contentType:'text/event-stream',body:': heartbeat\n\n'});return}
   let data:unknown=[];
   if(path==='/api/v1/auth/csrf')data={csrf_token:'test-only'};
   else if(path==='/api/v1/auth/me')data=actor;
   else if(path==='/api/v1/requests/123')data=item;
   else if(path==='/api/v1/agencies')data=[department];
   else if(path==='/api/v1/notifications/unread-count')data={count:0};
   else if(path==='/api/v1/ml/feedback')data={items:[],total:0,page:1,page_size:100};
   await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)});
  });
  await page.goto('/app/requests/123');
  await expect(page.getByRole('heading',{name:item.title})).toBeVisible();
  await expect(page.getByText(department.name+': Diproses. Pemeriksaan contoh.')).toBeVisible();
  await expect(page.getByText(department.name+': Disetujui. Simulasi selesai.')).toBeVisible();
  await expect(page.locator('.classification-panel')).toHaveCount(role==='admin'?1:0);
  for(const width of [375,768,1366]){
   await page.setViewportSize({width,height:900});
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
   await page.screenshot({path:`test-results/request-visibility-${role}-${width}.png`,fullPage:true});
  }
  const columns=await page.locator('.detail-layout').evaluate(element=>getComputedStyle(element).gridTemplateColumns.split(' ').length);
  expect(columns).toBe(role==='admin'?2:1);
 });
}
