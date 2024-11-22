import os
import sys

def get_paths(args):

    add_path = f'{args.version}/{args.year}'

    home_path = os.path.expanduser("~")
    eos_path = home_path.replace('afs/cern.ch', 'eos')

    paths = {
        'datasets':f'inputs/config/datasets.json',
        'nanoAODs': f'inputs/nanoAODs/{args.year}.json',
        'plot_dir': f"results/plots/{add_path}/",
        'corr_dir': f"results/corrections/{add_path}/",
        'hist_dir': f"results/hists/{add_path}/",
        'condor_dir': f"results/condor/{add_path}/",
        'pu_json': f'inputs/jsonpog/POG/LUM/{args.year}/puWeights.json.gz',
        'snap_dir': f"{eos_path}/CMS_xycorr/snapshots/{add_path}/",
        'proxy_path': f'{home_path}/proxy/x509up_u141674'
    }

    golden_jsons = {
        "2022_Summer22": "/eos/user/c/cmsdqm/www/CAF/certification/Collisions22/Cert_Collisions2022_355100_362760_Golden.json",
        "2022_Summer22EE": "/eos/user/c/cmsdqm/www/CAF/certification/Collisions22/Cert_Collisions2022_355100_362760_Golden.json",
        "2023_Summer23": "/eos/user/c/cmsdqm/www/CAF/certification/Collisions23/Cert_Collisions2023_366442_370790_Golden.json",
        "2023_Summer23BPix": "/eos/user/c/cmsdqm/www/CAF/certification/Collisions23/Cert_Collisions2023_366442_370790_Golden.json"
    }

    try:
        assert args.year in golden_jsons.keys(), f"year must be in {list(golden_jsons.keys())}!"
    except AssertionError as e:
        print(e, "If you are adding a new era, please make sure to adapt the configs.")
        sys.exit(1)

    for key in paths.keys():
        if 'dir' in key:
            os.makedirs(paths[key], exist_ok=True)

    paths['golden_json'] = golden_jsons[args.year]

    os.makedirs(paths['nanoAODs'].replace(paths['nanoAODs'].split('/')[-1], ''), exist_ok=True)

    return paths
