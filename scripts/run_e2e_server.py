import argparse
import uvicorn
from scripts.e2e_env import configure

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--env-file',default='.env.e2e');parser.add_argument('--model-dir');args=parser.parse_args()
    configure(args.env_file,args.model_dir)
    uvicorn.run('backend.app.main:app',host='127.0.0.1',port=8000,access_log=False)
