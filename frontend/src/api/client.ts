export class ApiError extends Error {
 constructor(public status:number,message:string){super(message)}
}

export async function bootstrapCsrf(){
 const response=await fetch('/api/v1/auth/csrf',{credentials:'include'});
 if(!response.ok)throw new ApiError(response.status,'Layanan belum dapat dihubungi.');
 return response.json();
}

async function request(path:string,options:RequestInit={}):Promise<Response>{
 const headers=new Headers(options.headers);
 if(options.body && !(options.body instanceof FormData))headers.set('Content-Type','application/json');
 const token=document.cookie.split('; ').find(c=>c.startsWith('sgwa_csrf='))?.split('=').slice(1).join('=');
 if(token)headers.set('X-CSRF-Token',decodeURIComponent(token));
 let response:Response;
 try{response=await fetch('/api/v1'+path,{...options,headers,credentials:'include'})}
 catch{throw new ApiError(0,'Tidak dapat menghubungi layanan. Periksa koneksi dan coba kembali.')}
 if(!response.ok){
  const body=await response.json().catch(()=>({}));
  if(response.status===401)window.dispatchEvent(new Event('sgwa:unauthorized'));
  const message=Array.isArray(body.detail)?'Periksa kembali isian formulir Anda.':body.detail||'Terjadi kesalahan layanan.';
  throw new ApiError(response.status,message);
 }
 return response;
}

export async function api<T>(path:string,options:RequestInit={}):Promise<T>{
 const response=await request(path,options);
 return await response.json().catch(()=>({})) as T;
}

export type DownloadFile={blob:Blob;filename:string;generatedAt:string|null};
export async function apiFile(path:string):Promise<DownloadFile>{
 const response=await request(path);
 if(response.headers.get('content-type')?.split(';')[0].trim().toLowerCase()!=='text/csv')throw new ApiError(502,'Layanan mengembalikan format unduhan yang tidak sesuai.');
 const disposition=response.headers.get('content-disposition')??'';
 const match=disposition.match(/filename=(?:"([^"]+)"|([^;]+))/i);
 const name=(match?.[1]??match?.[2]??'').trim();
 return {blob:await response.blob(),filename:/^[A-Za-z0-9._-]+\.csv$/.test(name)?name:'sgwa-laporan.csv',generatedAt:response.headers.get('x-report-generated-at')};
}
