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
        'sf_path': f'data/{args.year}/scalefactors.json',
        'trg_path': f'data/{args.year}/scalefactors.root'
    }

    paths['SFs'] = {
        'id': [paths['sf_path'], 'NUM_TightID_DEN_genTracks'],
        'iso': [paths['sf_path'], 'NUM_TightPFIso_DEN_TightID'],
        'trg': [paths['trg_path'], 'NUM_IsoMu24_DEN_TightIDandTightPFIso_abseta_pt']
    }

    for key in paths.keys():
        if 'dir' in key:
            os.makedirs(paths[key], exist_ok=True)

    return paths