# define histogram bins
def get_bins():

    hbins = {
        'met': {
            'MET': [-200, 200, 200],
            'PuppiMET': [-200, 200, 200]
        },
        'pileup': {
            'PV_npvsGood': [0, 100, 100]
        },
        "pt": {
            'MET': [0, 200, 100],
            'PuppiMET': [0, 200, 100]
        },
        "phi": {
            'MET': [-3.14, 3.14, 30],
            'PuppiMET': [-3.14, 3.14, 30]
        },
    }

    return hbins