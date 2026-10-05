import argparse
import csv
import hashlib
import json
from pathlib import Path
import random
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline


def train(dataset_path: Path, output_dir: Path) -> dict:
    rows=list(csv.DictReader(dataset_path.open(encoding='utf-8')))
    labels=sorted({r['label'] for r in rows})
    if len(labels)<2:
        raise ValueError('Minimal dua kelas diperlukan')
    groups={}
    for r in rows:
        if not r['text'].strip() or not r['group_id'].strip():
            raise ValueError('Teks dan group_id wajib diisi')
        if r['group_id'] in groups and groups[r['group_id']] != r['label']:
            raise ValueError('Satu group_id harus memiliki satu label')
        groups[r['group_id']]=r['label']
    test_groups=set()
    rng=random.Random(42)
    for label in labels:
        ids=sorted(g for g,l in groups.items() if l==label)
        if len(ids)<5 or sum(r['label']==label for r in rows)<50:
            raise ValueError('Setiap kelas membutuhkan 50 contoh dan minimal 5 kelompok')
        rng.shuffle(ids)
        test_groups.update(ids[:max(1,round(len(ids)*.2))])
    train_rows=[r for r in rows if r['group_id'] not in test_groups]
    test_rows=[r for r in rows if r['group_id'] in test_groups]
    model=Pipeline([('tfidf',TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True)),('classifier',LogisticRegression(max_iter=1000,random_state=42,C=4.0))])
    model.fit([r['text'] for r in train_rows],[r['label'] for r in train_rows])
    predicted=model.predict([r['text'] for r in test_rows])
    actual=[r['label'] for r in test_rows]
    digest=hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    version='tfidf-logreg-'+digest[:12]
    report={'model_version':version,'macro_f1':float(f1_score(actual,predicted,average='macro')),'classification_report':classification_report(actual,predicted,labels=labels,output_dict=True,zero_division=0),'confusion_matrix':confusion_matrix(actual,predicted,labels=labels).tolist(),'classes':labels,'train_count':len(train_rows),'test_count':len(test_rows),'train_groups':len(groups)-len(test_groups),'test_groups':len(test_groups),'random_state':42,'synthetic':True,'errors':[{'text':r['text'],'actual':r['label'],'predicted':str(p)} for r,p in zip(test_rows,predicted) if r['label']!=p]}
    output_dir.mkdir(parents=True,exist_ok=True)
    for name,subset in [('train.csv',train_rows),('test.csv',test_rows)]:
        with (output_dir/name).open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=['text','label','group_id']);writer.writeheader();writer.writerows(subset)
    joblib.dump(model,output_dir/'model.joblib')
    metadata={'model_version':version,'classes':labels,'dataset_hash':digest,'model_hash':hashlib.sha256((output_dir/'model.joblib').read_bytes()).hexdigest(),'synthetic':True,'threshold':.60}
    for name,value in [('metadata.json',metadata),('evaluation.json',report)]:
        (output_dir/name).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--dataset',type=Path,default=Path('ml/data/requests.csv'));parser.add_argument('--output',type=Path,default=Path('ml/artifacts'))
    args=parser.parse_args();report=train(args.dataset,args.output)
    print(f"Macro-F1: {report['macro_f1']:.4f}; test={report['test_count']}; data sintetis")
