"""Conservative versioned Indonesian normalization for training and inference."""
import hashlib
import re
import unicodedata

NORMALIZER_VERSION = 'id-v1'
ALIASES = {'jln':'jalan', 'bnyk':'banyak', 'lampmer':'lampu merah', 'yg':'yang',
           'utk':'untuk', 'dgn':'dengan', 'tdk':'tidak', 'krn':'karena', 'sy':'saya',
           'mhn':'mohon', 'blm':'belum', 'gak':'tidak', 'nggak':'tidak'}

def normalize_text(text: str, version: str = NORMALIZER_VERSION) -> str:
    if version != NORMALIZER_VERSION:
        raise ValueError('Versi normalisasi tidak didukung')
    text = unicodedata.normalize('NFKC', text).lower()
    text = re.sub(r'\b\w+\b', lambda m: ALIASES.get(m[0], m[0]), text)
    return ' '.join(text.split())

def text_hash(text: str, version: str = NORMALIZER_VERSION) -> str:
    return hashlib.sha256(normalize_text(text, version).encode('utf-8')).hexdigest()
