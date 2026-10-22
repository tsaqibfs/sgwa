import {describe,it,expect} from 'vitest';
import {reconcileAnswers} from './formAnswers';
import type {FormSchema} from './types';

describe('answers after schema publication',()=>{
 it('keeps incompatible date text for review without submitting an invisible date',()=>{
  const old:FormSchema={fields:[{key:'day',label:'Tanggal lama',type:'text',required:false}]};
  const next:FormSchema={fields:[{key:'day',label:'Tanggal baru',type:'date',required:false}]};
  for(const value of ['catatan bebas','2026-02-30']){
   const result=reconcileAnswers(old,next,{day:value});
   expect(result.active).toEqual({});expect(result.previous[0].value).toBe(value);
  }
  expect(reconcileAnswers(old,next,{day:'2026-10-10'}).active).toEqual({day:'2026-10-10'});
 });
});
