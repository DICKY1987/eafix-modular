import argparse
from registry_core import run

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--check',action='store_true')
 p.add_argument('--report-only',action='store_true')
 a=p.parse_args()
 return run(check=a.check,report_only=a.report_only)

if __name__=="__main__": raise SystemExit(main())
