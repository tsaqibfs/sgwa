import {Button} from '@radix-ui/themes';
export function PageState({loading,error,reload}:{loading:boolean;error:string;reload?:()=>void}){
 if(loading)return <div className="state" role="status"><span className="loader"/>Memuat data layanan…</div>;
 if(error)return <div className="state"><p className="error" role="alert">{error}</p>{reload&&<Button variant="soft" onClick={reload}>Coba kembali</Button>}</div>;
 return null;
}
