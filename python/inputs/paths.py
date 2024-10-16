import os

def get_paths(args):

    add_path = f'{args.version}/{args.year}'

    paths = {
        'datasets':f'data/{args.year}/datasets.json',
        'files': f'data/{args.year}/nanoAODs.json',
        'plot_dir': f"results/plots/{add_path}/",
        'corr_dir': f"results/corrections/{add_path}/",
        'hist_dir': f"results/hists/{add_path}/",
        'snap_dir': f"/ceph/jdriesch/CMS_xycorr/snapshots/{add_path}/",
        'condor_dir': f"results/condor/{add_path}/",
        'golden_json': 'data/jsons/Run3_2022_2023_Golden.json',
        'pu_json': f'data/{args.year}/puWeights.json',
    }

    for key in paths.keys():
        if 'dir' in key:
            os.makedirs(paths[key], exist_ok=True)

    return paths