import json
import yaml
import os
import sys

dname = sys.argv[1]
datasets = f'configs/{dname}'
dpath = 'configs/data/'
os.makedirs(dpath, exist_ok=True)

# open file with dataset names
with open(datasets) as f:
    dsets = yaml.load(f, yaml.Loader)

lib = "root://xrootd-cms.infn.it//"

for year in dsets:
    for dtmc in dsets[year]:
        fdict = {}
        for era in dsets[year][dtmc]:
            fdict[era] = []
            for sample in dsets[year][dtmc][era]["samples"]:
                stream = os.popen(f'dasgoclient -query="file dataset={sample}"')
                fdict[era] += [
                    lib+s.replace('\n', '') for s in stream.readlines()[:10]
                ]
        with open(dpath+year+dtmc+'.yaml', "w") as f:
            yaml.dump(fdict, f)
