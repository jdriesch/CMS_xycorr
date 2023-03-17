import json
import yaml
import os
import sys

dname = sys.argv[1]
datasets = f'../configs/{dname}'

# open file with dataset names
with open(datasets) as f:
    dsets = yaml.load(f, yaml.Loader)

lib = "root://xrootd-cms.infn.it//"

for k in dsets.keys():
    fdict = {}
    for d in dsets[k]["names"]:
        stream = os.popen(f'dasgoclient -query="file dataset={d}"')
        fdict[d] = [
            lib+s.replace('\n', '') for s in stream.readlines()
        ]

    with open(datasets.replace("datasets", k), "w") as f:
        yaml.dump(fdict, f)
