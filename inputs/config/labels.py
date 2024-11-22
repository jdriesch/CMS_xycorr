def get_labels(year):

    lumilabels = {
        '2022_Summer22': {
            'DATA': '8.0fb^{-1} (13.6 TeV)',
            'MC': '(13.6 TeV)',
        },
        '2022_Summer22EE': {
            'DATA': '26.7fb^{-1} (13.6 TeV)',
            'MC': '(13.6 TeV)',
        },
        '2023_Summer23': {
            'DATA': '17.6fb^{-1} (13.6 TeV)',
            'MC': '(13.6 TeV)',
        },
        '2023_Summer23BPix': {
            'DATA': '9.5fb^{-1} (13.6 TeV)',
            'MC': '(13.6 TeV)',
        }
    }

    datasetlabels = {
        '2022_Summer22': '2022 preEE',
        '2022_Summer22EE': '2022 postEE',
        '2023_Summer23': '2023 preBPix',
        '2023_Summer23BPix': '2023 postBPix'
    }

    axislabels = {
        f"MET_pt": "PFMET (GeV)",
        f"MET_phi": "#phi (MET)",
        f"PuppiMET_pt": "PuppiMET (GeV)",
        f"PuppiMET_phi": "#phi (PuppiMET)"
    }

    return lumilabels[year], axislabels, datasetlabels[year]
