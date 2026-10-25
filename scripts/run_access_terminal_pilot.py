"""Run Uji 3 only on the dedicated disposable port-3308 test database."""
import argparse
import json
import os
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import make_url
import pytest
from backend.tests.safety import validated_test_url


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--test-env',default='.superpowers/test.env')
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    values=dotenv_values(args.test_env)
    url=validated_test_url(values.get('TEST_DATABASE_URL',''))
    parsed=make_url(url)
    if parsed.host not in ('127.0.0.1','localhost') or parsed.port!=3308 or parsed.database!='sgwa_test_service':
        raise SystemExit('Refusing: Uji 3 requires local sgwa_test_service on port 3308')
    output=Path(args.output).resolve()
    if output.exists() and any(output.iterdir()):raise SystemExit('Use a new empty output directory to preserve evidence')
    os.environ['TEST_DATABASE_URL']=url
    os.environ['SGWA_ACCESS_PILOT_OUTPUT']=str(output)
    code=pytest.main(['backend/tests/test_access_terminal_pilot.py','-q'])
    metadata=output/'run_metadata.json'
    if metadata.exists():
        data=json.loads(metadata.read_text(encoding='utf-8'))
        data['pytest_exit_code']=int(code)
        data['run_state']='completed' if code==0 else 'failed_or_incomplete'
        if code!=0:data['all_cases_passed']=False
        metadata.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        print(json.dumps({key:data.get(key) for key in ('completed_cases','passed_cases','failed_cases','all_cases_passed')}))
    raise SystemExit(code)


if __name__=='__main__':main()
