import type {FormAnswers,FormSchema} from './types';

export function reconcileAnswers(oldSchema:FormSchema,nextSchema:FormSchema,answers:FormAnswers){
 const active:FormAnswers={},previous:{key:string;label:string;value:string|number|boolean|Record<string,any>}[]=[];
 for(const [key,value] of Object.entries(answers)){
  const field=nextSchema.fields.find(item=>item.key===key);
  const validDate=typeof value==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(value)&&Number.isFinite(Date.parse(value))&&new Date(value).toISOString().slice(0,10)===value;
  const compatible=field&&((['text','textarea'].includes(field.type)&&typeof value==='string')||(field.type==='date'&&validDate)||(field.type==='number'&&typeof value==='number'&&Number.isFinite(value))||(field.type==='checkbox'&&typeof value==='boolean')||(field.type==='select'&&typeof value==='string'&&field.options?.includes(value))||(field.type==='file'&&(typeof value==='string'||typeof value==='number'||typeof value==='object')));
  if(compatible)active[key]=value;
  else previous.push({key,label:oldSchema.fields.find(item=>item.key===key)?.label??key,value});
 }
 for(const field of nextSchema.fields)if(field.type==='checkbox'&&active[field.key]===undefined)active[field.key]=false;
 return {active,previous};
}
