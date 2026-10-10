import math
import re
from datetime import date
from fastapi import HTTPException
from backend.app.forms.schemas import FormSchema


def validate_answers(schema: FormSchema, answers: dict) -> dict:
    keys = {field.key for field in schema.fields}
    if set(answers) - keys:
        raise HTTPException(422, 'Jawaban memuat field yang tidak dikenal.')
    clean = {}
    for field in schema.fields:
        value = answers.get(field.key)
        if value is None or value == '' and field.type != 'checkbox':
            if field.required:
                raise HTTPException(422, f'{field.label} wajib diisi.')
            continue
        valid = False
        if field.type in ('text','textarea'):
            valid = isinstance(value,str) and (field.min_length or 0) <= len(value.strip()) <= (field.max_length or (255 if field.type=='text' else 5000))
            if field.required and isinstance(value,str) and not value.strip():valid=False
            if isinstance(value,str):value=value.strip()
        elif field.type=='number':
            valid=type(value) in (int,float) and abs(value)<=9007199254740991 and (type(value) is int or math.isfinite(value)) and (field.min_value is None or value>=field.min_value) and (field.max_value is None or value<=field.max_value)
        elif field.type=='date':
            try:
                valid=isinstance(value,str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}',value) is not None and bool(date.fromisoformat(value))
            except ValueError:valid=False
        elif field.type=='select':valid=isinstance(value,str) and value in field.options
        elif field.type=='checkbox':valid=type(value) is bool
        if not valid:raise HTTPException(422,f'Jawaban {field.label} tidak sesuai format atau batas formulir.')
        clean[field.key]=value
    return clean
