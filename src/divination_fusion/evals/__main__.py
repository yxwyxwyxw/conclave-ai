from __future__ import annotations 

import json 

from .harness import run_demo_eval 

def main ()->None :
    results =run_demo_eval ()
    print (json .dumps (results ,ensure_ascii =False ,indent =2 ))

if __name__ =="__main__":
    main ()
