# Repo for XY corrections
This repo is aimed at correcting the modulations in MET.
For that, the following steps should be performed:
1. Write desired datasets names into configs/datasets.yaml
2. run `python3 tools/make_yaml.py datasets.yaml` in order to get yamls with rootfiles
3. run `python3 get_xy_corrs.py -H -C -S -D datasets.yaml` in order to obtain xy corrections
4. run `python3 tools/validate.py datasets.yaml` in order to obtain validation plots
