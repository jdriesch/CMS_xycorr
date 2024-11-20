import os

def get_paths(args):

    add_path = f'{args.version}/{args.year}'

    paths = {
        'datasets':f'inputs/config/datasets.json',
        'nanoAODs': f'inputs/nanoAODs/{args.year}.json',
        'plot_dir': f"results/plots/{add_path}/",
        'corr_dir': f"results/corrections/{add_path}/",
        'hist_dir': f"results/hists/{add_path}/",
        'condor_dir': f"results/condor/{add_path}/",
        'golden_json': 'inputs/jsons/Run3_2022_2023_Golden.json',
        'pu_json': f'inputs/jsonpog/POG/LUM/{args.year}/puWeights.json.gz',
        'snap_dir': f"/ceph/jdriesch/CMS_xycorr/snapshots/{add_path}/",
    }

    for key in paths.keys():
        if 'dir' in key:
            os.makedirs(paths[key], exist_ok=True)

    os.makedirs(paths['nanoAODs'].replace(paths['nanoAODs'].split('/')[-1], ''), exist_ok=True)

    return paths