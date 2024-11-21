# define histogram bins
def get_bins():

    hbins = {
        'met': [-200, 200, 200],
        'pileup': [0, 100, 100],
        "pt": [0, 200, 100],
        "phi": [-3.15, 3.15, 30],
    }

    return hbins