"""Validate an explicitly separate E2E database and artifact directory."""
import os
from pathlib import Path
from dotenv import dotenv_values
from sqlalchemy.engine import make_url

def configure(path,model_dir=None):
    file=Path(path)
    if not file.is_file():raise ValueError('Salin .env.e2e.example ke .env.e2e dan isi konfigurasi test terlebih dahulu.')
    values={k:v for k,v in dotenv_values(file).items() if v is not None}
    url=make_url(values.get('DATABASE_URL',''))
    if url.get_backend_name()!='mysql' or not (url.database or '').startswith('sgwa_test'):
        raise ValueError('E2E memerlukan database terpisah dengan nama berawalan sgwa_test.')
    if not (model_dir or values.get('MODEL_DIR')):raise ValueError('MODEL_DIR E2E wajib diisi.')
    root=Path.cwd().resolve();directory=Path(model_dir or values['MODEL_DIR']).resolve()
    if not directory.is_relative_to(root/'.superpowers') or directory==root/'.superpowers':
        raise ValueError('MODEL_DIR E2E harus berada di subdirektori .superpowers, terpisah dari model aplikasi.')
    values['MODEL_DIR']=str(directory);os.environ.update(values)
    return values
