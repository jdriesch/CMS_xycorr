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
    Calculate the xy corrected MET.

    Args:
    rdf (ROOT.RDataFrame): RDataFrame that is to be examined
    met (str): type of MET
    corrs (str): path of correction file
    """
    with open(corrs, 'r') as f:
        c = json.load(f)

    cmet = f"Corrected{met}"

    for xy in c[met].keys():

        rdf = rdf.Define(
            f"{cmet}{xy}", 
            f"{met}{xy} - ({c[met][xy]['nom']['m']} * int(PV_npvsGood)\
             + {c[met][xy]['nom']['c']})"
            )

    for m in [met, cmet]:
        rdf = rdf.Define(f"{m}_pt", f"sqrt({m}_x*{m}_x + {m}_y*{m}_y)")
        rdf = rdf.Define(f"{m}_phi", f"atan2({m}_y, {m}_x)")
    
    return rdf


def make_validation_plots(
    snap_dir, plot_dir, corr_dir, hbins, axislabels, lumilabel
):
    """
    Create MC vs Mc or Data vs Data plot before vs after xy correction.

    Args:
    snap_dir (str): Path to snapshot directory.
    plot_dir (str): Path to plot directory.
    corr_dir (str): Path to correction directory.
    hbins (dict): Dictionary with histogram binning information.
    axislabels (dict): Improved axis labels.
    lumilabel (dict): Labels for lumi in the corresponding epoch.
    """
    logger.info("Starting validation")

    for dtmc in ['DATA', 'MC']:
        files = snap_dir+dtmc+'/*.root'
        logger.debug(f"Building RDataFrame from files in {files}")
        rdf = ROOT.RDataFrame('Events', files)

        for met in hbins['pt']:
            rdf = correctXY(rdf, met, corr_dir+dtmc+'.json')

            for var in ['pt', 'phi']:

                # uncorrected histogram
                h = rdf.Histo1D(
                    (
                        var, var, 
                        hbins[var][met][2],
                        hbins[var][met][0],
                        hbins[var][met][1]
                    ),
                    met+'_'+var
                )

                # corrected histogram
                hc = rdf.Histo1D(
                    (
                        f"Corrected{var}", var,
                        hbins[var][met][2],
                        hbins[var][met][0],
                        hbins[var][met][1]
                    ),
                    f"Corrected{met}_{var}"
                )

                logger.debug(f"Starting to plot {met}_{var} for {dtmc}.")

                plot.plot_ratio(
                    hc,
                    h,
                    labels=["corr", "uncorr"], 
                    axis=[axislabels[met+'_'+var], "# Events"],
                    outfile=f"{plot_dir}{met}_{var}_{dtmc}.pdf", 
                    text=['','',''], 
                    xrange=[hbins[var][met][0], hbins[var][met][1]],
                    ratiorange = [0.8, 1.2],
                    lumi = lumilabel[dtmc]
                )

    return