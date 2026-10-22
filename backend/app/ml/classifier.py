import hashlib
import json
from pathlib import Path
import joblib
from io import BytesIO
from ml.train import validate_artifacts
from ml.text import normalize_text
from backend.app.ml.schemas import Prediction


class ModelUnavailable(Exception):
    pass


class Classifier:
    def __init__(self, directory: Path):
        try:
            self.directory = directory
            self.info = validate_artifacts(directory)
            model_path=directory/'model.joblib'
            if hashlib.sha256(model_path.read_bytes()).hexdigest() != self.info['model_hash']:
                raise ValueError('Model hash mismatch')
            data=model_path.read_bytes()
            if hashlib.sha256(data).hexdigest()!=self.info['model_hash']:raise ValueError('Model hash mismatch')
            self.model = joblib.load(BytesIO(data))
            if list(self.model.classes_) != self.info['classes']:
                raise ValueError('Model classes mismatch')
            self.report=json.loads((directory/'evaluation.json').read_text(encoding='utf-8'))
            if self.report['model_version'] != self.info['model_version']:
                raise ValueError('Report version mismatch')
        except Exception as exc:
            raise ModelUnavailable('Model belum tersedia atau tidak valid. Jalankan training.') from exc

    def predict(self, text: str) -> Prediction:
        text=normalize_text(text,self.info['normalizer_version'])
        features = self.model.named_steps['tfidf'].transform([text])
        values = self.model.predict_proba([text])[0]
        probabilities={str(k):float(v) for k,v in zip(self.model.classes_,values)}
        agency=max(probabilities,key=probabilities.get)
        policy=self.info['routing_policy']
        return Prediction(agency,probabilities,probabilities[agency],features.nnz>0,self.info['model_version'],policy['threshold'],policy['auto_routing_enabled'])

    def metadata(self) -> dict:
        return dict(self.info)
