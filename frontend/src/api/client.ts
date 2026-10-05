export class ApiError extends Error {
 constructor(public status:number,message:string){super(message)}
}

export async function bootstrapCsrf(){
 const response=await fetch('/api/v1/auth/csrf',{credentials:'include'});
 if(!response.ok)throw new ApiError(response.status,'Layanan belum dapat dihubungi.');
 return response.json();
}

export async function api<T>(path:string,options:RequestInit={}):Promise<T>{
 const headers=new Headers(options.headers);
 if(options.body)headers.set('Content-Type','application/json');
 const token=document.cookie.split('; ').find(c=>c.startsWith('sgwa_csrf='))?.split('=').slice(1).join('=');
 if(token)headers.set('X-CSRF-Token',decodeURIComponent(token));
 let response:Response;
 try{response=await fetch('/api/v1'+path,{...options,headers,credentials:'include'})}
 catch{throw new ApiError(0,'Tidak dapat menghubungi layanan. Periksa koneksi dan coba kembali.')}
 const body=await response.json().catch(()=>({}));
 if(!response.ok){
  if(response.status===401)window.dispatchEvent(new Event('sgwa:unauthorized'));
  const message=Array.isArray(body.detail)?'Periksa kembali isian formulir Anda.':body.detail||'Terjadi kesalahan layanan.';
  throw new ApiError(response.status,message);
 }
 return body as T;
}
