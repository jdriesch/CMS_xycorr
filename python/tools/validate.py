import ROOT
import json
import os
import sys
import glob
import logging

import python.tools.plot as plot

logger = logging.getLogger(__name__)

def correctXY(rdf, met, corrs):
    """
    (ROOT.RDataFrame) rdf: Dataframe
    (str) met: type of MET
    (str) corrs: path of correction file
    """
    with open(corrs, 'r') as f:
        c = json.load(f)

    cmet = f"Corrected{met}"
    for xy in c[met].keys():
        rdf = rdf.Define(
            f"{cmet}{xy}", 
            f"{met}{xy} - ({c[met][xy]['nom']['m']}*int(PV_npvsGood) + {c[met][xy]['nom']['c']})"
            )

    for m in [met, cmet]:
        rdf = rdf.Define(f"{m}_pt", f"sqrt({m}_x*{m}_x + {m}_y*{m}_y)")
        rdf = rdf.Define(f"{m}_phi", f"atan2({m}_y, {m}_x)")
    
    return rdf


def make_validation_plots(snap_dir, plot_dir, corr_dir, hbins, axislabels, lumilabel):
    """
    (ROOT.RDataFrame) rdf: Dataframe
    (dict) hbins: names and bins of validation histograms
    (str) plots: path to plots
    """
    logger.info("Starting validation")

    for dtmc in ['DATA', 'MC']:
        files = snap_dir+dtmc+'/*.root'
        logger.debug(f"Building RDataFrame from files in {files}")
        rdf = ROOT.RDataFrame('Events', files)

        for met in hbins['pt']:
            rdf = correctXY(rdf, met, corr_dir+dtmc+'.json')

            for var in ['pt', 'phi']:
                h = rdf.Histo1D(
                    (var, var, hbins[var][met][2], hbins[var][met][0], hbins[var][met][1]),
                    met+'_'+var
                )

                hc = rdf.Histo1D(
                    (f"Corrected{var}", var, hbins[var][met][2], hbins[var][met][0], hbins[var][met][1]),
                    f"Corrected{met}_{var}"
                )

                logger.debug(f"Starting to plot {met}_{var} for {dtmc}.")

                plot.plot_ratio(
                    hc, # data plot
                    h,  # mc plot
                    labels=["corr", "uncorr"], 
                    axis=[axislabels[met+'_'+var], "# Events"],
                    outfile=f"{plot_dir}{met}_{var}_{dtmc}.pdf", 
                    text=['','',''], 
                    xrange=[hbins[var][met][0], hbins[var][met][1]],
                    ratiorange = [0.8, 1.2],
                    lumi = lumilabel[dtmc]
                )

    return




if __name__=='__main__':
    year = sys.argv[1]
    datasets = f'../data/{year}/datasets.yaml'
    met = 'PuppiMET'
    ROOT.gROOT.SetBatch()
    ROOT.EnableImplicitMT()

    # load datasets
    with open(datasets, "r") as f:
        dsets = yaml.load(f, Loader=yaml.Loader)

    # define histogram bins
    hbins = {
        f"{met}_pt": [0, 200, 100],
        f"{met}_phi": [-3.14, 3.14, 30],
    }
    hlabels = {
        f"MET_pt": "PFMET (GeV)",
        f"MET_phi": "#phi (MET)",
        f"PuppiMET_pt": "PuppiMET (GeV)",
        f"PuppiMET_phi": "#phi (PuppiMET)"
    }
    lumilabels = {
        '2022': {
            'DATA': ['2022 preEE, 8.0fb^{-1} (13.6 TeV)', 0.335],
            'MC': ['2022 preEE (13.6 TeV)', 0.26],
        },
        '2022EE': {
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

    # go through runs / mc
    for tag in ['MC', 'DATA']:
        rfiles = f"/ceph/jdriesch/CMS_xycorr/snapshots/{year}{tag}/file*.root"
        corr_file = f"../results/corrections/{year}/{year}_{tag}.yaml"
        plots = f"../results/plots/{year}/{year}_validation_{tag}"
        print(rfiles)

        all_files = glob.glob(rfiles)

        # rdf = ROOT.RDataFrame(load_chain(all_files))
        rdf = ROOT.RDataFrame('Events', [rfiles])
        print(rdf.Count().GetValue())

        rdf = correctXY(rdf, met, corr_file)
        print(rdf.Count().GetValue())

        validation_plots(rdf, hbins, hlabels, plots, tag, lumilabels[year][tag])
