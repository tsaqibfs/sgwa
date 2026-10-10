"""Reproducible synthetic teaching dataset with immutable grouped holdout."""
import csv
import hashlib
import json
from pathlib import Path
import random
from ml.scenarios import SCENARIOS
from ml.text import NORMALIZER_VERSION, text_hash

DATASET_VERSION = 'sgwa-25-synthetic-v1'
FIELDS = ['text', 'label', 'group_id', 'provenance', 'dataset_version', 'text_hash']
TEMPLATES = [
 'Saya ingin {text}. Mohon informasi persyaratan dan prosesnya.',
 'Mohon bantuan untuk {text} karena saya belum mengetahui tahapannya.',
 'Bagaimana prosedur untuk {text}? Saya membutuhkan arahan petugas.',
 'Saya mengajukan permohonan untuk {text}. Dokumen akan saya lengkapi.',
 'Tolong bantu warga yang perlu {text}, kapan dapat diproses?',
 'Mhn arahannya, sy perlu {text}. Harus mulai dari mana ya?',
 'Saya belum mendapat jawaban tentang cara {text}. Bisa dibantu?',
 'Warga di lingkungan kami perlu {text}. Kepada siapa kami melapor?',
 'Mohon tindak lanjut untuk {text}. Sudah beberapa hari kami menunggu.',
 'Saya bingung soal {text}, minta penjelasan petugas dong.',
]

def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()

def build_dataset(path: Path, manifest_path: Path) -> dict:
    from backend.app.agencies.catalog import AGENCIES
    if set(SCENARIOS) != {code for code, _ in AGENCIES}:
        raise ValueError('Dataset wajib mencakup 25 kode katalog')
    rows = []; seen = set(); holdout = []
    rng = random.Random(42)
    for label in sorted(SCENARIOS):
        families = SCENARIOS[label]
        if len(families) < 10:
            raise ValueError('Minimal 10 keluarga per kelas')
        groups = [f'{label}-{i:02d}' for i in range(len(families))]
        choices = list(groups); rng.shuffle(choices)
        holdout.extend(choices[:round(len(groups)*.2)])
        for group, text in zip(groups, families):
            for template in TEMPLATES:
                original = template.format(text=text)
                digest = text_hash(original)
                if digest in seen:
                    raise ValueError('Teks duplikat setelah normalisasi')
                seen.add(digest)
                rows.append(dict(text=original, label=label, group_id=group, provenance='synthetic', dataset_version=DATASET_VERSION, text_hash=digest))
    manifest = dict(dataset_version=DATASET_VERSION, normalizer_version=NORMALIZER_VERSION,
                    seed=42, groups=sorted(holdout), rows_hash=canonical_hash(rows))
    manifest['manifest_hash'] = canonical_hash(manifest)
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS); writer.writeheader(); writer.writerows(rows)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False)+'\n', encoding='utf-8')
    return manifest

if __name__ == '__main__':
    manifest = build_dataset(Path('ml/data/requests.csv'), Path('ml/data/holdout.json'))
    print(f'Dataset sintetis 25 kelas; holdout {len(manifest["groups"])} kelompok')
