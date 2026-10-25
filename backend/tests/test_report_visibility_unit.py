"""Report projection and CSV privacy without changing application data."""
import csv
import io
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest
from sqlalchemy import select
from backend.app.models import Request
from backend.app.reports.service import report_rows
from backend.app.reports.csv_export import encode_csv

@pytest.mark.parametrize('include',[False,True])
def test_report_projection_and_csv_ml_visibility(include):
    db=MagicMock()
    item=SimpleNamespace(id=1,reference='TEST-1',title='Example',status='pending',assigned_agency_id=None,created_at=datetime(2026,10,25),updated_at=datetime(2026,10,25))
    prediction=SimpleNamespace(request_id=1,predicted_agency_code='dukcapil',confidence=0.462,model_version='private-model')
    db.scalars.return_value.all.return_value=[item]
    db.scalars.side_effect=[SimpleNamespace(all=lambda:[item]),[],[prediction]]
    db.execute.return_value=[]
    rows=report_rows(db,select(Request),offset=0,limit=20,include_classification=include)
    assert (rows[0].classification is not None)==include
    assert db.scalars.call_count==(3 if include else 2)
    parsed=list(csv.DictReader(io.StringIO(encode_csv(rows,include_classification=include).decode('utf-8-sig'))))
    if include:
        assert parsed[0]['versi_model']=='private-model'
    else:
        assert not {'prediksi_dinas','confidence','versi_model'} & parsed[0].keys()
        assert 'private-model' not in str(parsed)
