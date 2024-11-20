def get_labels(year):

    lumilabels = {
        '2022_Summer22': {
            'DATA': ['2022 preEE, 8.0fb^{-1} (13.6 TeV)', 0.34],
            'MC': ['2022 preEE (13.6 TeV)', 0.26],
        },
        '2022_Summer22EE': {
            'DATA': ['2022 postEE, 26.7fb^{-1} (13.6 TeV)', 0.36],
            'MC': ['2022 postEE (13.6 TeV)', 0.27],
        },
        '2023': {
            'DATA': ['2023 preBPix, 17.6fb^{-1} (13.6 TeV)', .37],
            'MC': ['2023 preBPix (13.6 TeV)', .28],
        },
        '2023BPix': {
            'DATA': ['2023 postBPix, 9.5fb^{-1} (13.6 TeV)', .37],
            'MC': ['2023 postBPix (13.6 TeV)', .29],
        }
    }

    axislabels = {
        f"MET_pt": "PFMET (GeV)",
        f"MET_phi": "#phi (MET)",
        f"PuppiMET_pt": "PuppiMET (GeV)",
        f"PuppiMET_phi": "#phi (PuppiMET)"
    }

    return lumilabels[year], axislabels
