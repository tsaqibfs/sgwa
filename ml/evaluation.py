"""Group-isolated evaluation and conservative selective-routing policy."""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from ml.text import normalize_text

CONFIG = {'C':4.0, 'max_iter':1000, 'random_state':42, 'ngram_range':[1,2], 'folds':5, 'format':'ml25-v1'}


def make_pipeline() -> Pipeline:
    return Pipeline([('tfidf',TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True)),
                     ('classifier',LogisticRegression(max_iter=1000,random_state=42,C=4.0))])


def choose_threshold(actual: list[str], predicted: list[str], confidence: list[float]) -> dict:
    if not (len(actual)==len(predicted)==len(confidence)) or not all(np.isfinite(confidence)):
        raise ValueError('Prediksi validasi tidak valid')
    grid=[]
    for threshold in (.70,.75,.80,.85,.90,.95):
        accepted=[i for i,c in enumerate(confidence) if c>=threshold]
        precision=sum(actual[i]==predicted[i] for i in accepted)/len(accepted) if accepted else 0.0
        grid.append(dict(threshold=threshold, accepted_count=len(accepted), accepted_precision=precision,
                         coverage=len(accepted)/len(actual) if actual else 0.0))
    eligible=[row for row in grid if row['accepted_count']>=25 and row['accepted_precision']>=.90]
    chosen=max(eligible,key=lambda row: (row['coverage'],-row['threshold'])) if eligible else grid[0]
    return {**chosen,'auto_routing_enabled':bool(eligible),'grid':grid}


def evaluate_groups(rows: list[dict], holdout: dict) -> dict:
    train_rows=[r for r in rows if r['group_id'] not in set(holdout['groups'])]
    labels=sorted({r['label'] for r in rows})
    if any(len({r['group_id'] for r in train_rows if r['label']==label})<5 for label in labels):
        raise ValueError('Setiap kelas membutuhkan minimal 5 kelompok non-holdout')
    texts=np.array([normalize_text(r['text']) for r in train_rows]);actual=np.array([r['label'] for r in train_rows])
    groups=np.array([r['group_id'] for r in train_rows])
    predicted=np.empty(len(train_rows),dtype=object)
    confidence=np.zeros(len(train_rows));folds=[];scores=[]
    for n,(fit,valid) in enumerate(StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=42).split(texts,actual,groups),1):
        if set(actual[fit])!=set(labels) or set(actual[valid])!=set(labels):
            raise ValueError('Fold tidak mencakup semua kelas; perbaiki kelompok dataset')
        pipeline=make_pipeline();pipeline.fit(texts[fit].tolist(),actual[fit].tolist())
        probabilities=pipeline.predict_proba(texts[valid].tolist())
        winners=probabilities.argmax(axis=1)
        predicted[valid]=pipeline.classes_[winners]
        confidence[valid]=probabilities.max(axis=1)
        score=float(f1_score(actual[valid],predicted[valid].tolist(),average='macro',labels=labels,zero_division=0));scores.append(score)
        folds.append(dict(fold=n,macro_f1=score,train_groups=sorted(set(groups[fit])),validation_groups=sorted(set(groups[valid])),classes=labels))
    return dict(folds=folds,mean_macro_f1=float(np.mean(scores)),std_macro_f1=float(np.std(scores)),
                routing_policy=choose_threshold(actual.tolist(),predicted.tolist(),confidence.tolist()))
