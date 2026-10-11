"""Migrate, seed and bootstrap an existing, isolated E2E MySQL schema."""
import argparse,os,subprocess,sys
from scripts.e2e_env import configure

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--env-file',default='.env.e2e');parser.add_argument('--model-dir');args=parser.parse_args()
    values=configure(args.env_file,args.model_dir)
    for command in [['alembic','-c','backend/alembic.ini','upgrade','head'],['backend.app.seed'],['scripts.bootstrap_ml']]:
        subprocess.run([sys.executable,'-m',*command],env={**os.environ,**values},check=True)
    print('E2E siap pada schema dan artefak test terpisah; tidak mereset data.')
