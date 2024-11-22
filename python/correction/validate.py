import ROOT
import json
import os
import sys
import glob
import logging

import python.tools.plot as plot

logger = logging.getLogger(__name__)


def validate_json(snap_dir, corr_dir, hist_dir, datamc, year, bin_dict, mets):
    """
    Create histograms for closure validation.

    Args:
        snap_dir (str): path to snapshots.
        corr_dir (str): path to corrections.
        hist_dir (str): path where histograms are saved.
        datamc (list): DATA or MC to investigate.
        year (str): name of the year.
        bin_dict (dict): bining configuration.
        mets (list): met types to validate.
    """
    logger.info("Starting validation of correction.")

    # define variations for later
    variations = ['', '_stat_xup', '_stat_xdn', '_stat_yup', '_stat_ydn']

    variables = ['pt', 'phi']

    for dtmc in datamc:

        # in MC also define pileup variations
        if dtmc=='MC':
            pu_variations = ['_pu_up', '_pu_dn']
        else:
            pu_variations = []
        
        # setup of dataframe
        rdf = ROOT.RDataFrame("Events", f"{snap_dir}{dtmc}/file_*.root")

        # loading the pileup correctionlib file
        schemav2_json = corr_dir.replace(f'{year}/', f'schemaV2_{year}.json')
        ROOT.gROOT.ProcessLine(
            f'auto cs_xy = correction::CorrectionSet::from_file(\
            "{schemav2_json}")->at("met_xy_corrections");'
        )

        # loop over different met types, calculate correction and histograms
        for met in mets:

            # obtain met pt and phi from x, y components
            rdf = rdf.Define(f'{met}_phi', f'atan2({met}_y, {met}_x)')
            rdf = rdf.Define(f'{met}_pt', f'sqrt({met}_y*{met}_y + {met}_x*{met}_x)')
        
            # correct pt and phi for different variations
            for var in variables:
                
                # statistical variations for both data and mc
                for vrt in variations+pu_variations:

                    rdf = rdf.Define(
                        f'{met}_{var}_corr{vrt}', 
                        f'cs_xy->evaluate({{\
                            "{var}{vrt}", "{met}", "{dtmc}", \
                            {met}_pt, {met}_phi, static_cast<float>(PV_npvsGood)\
                        }})'
                    )                 

        # create histograms for defined variables
        hists = []
        save_variations = ['_corr'+v for v in variations+pu_variations] + ['']
        
        for vrt in save_variations:
            for met in mets:
                for var in variables:

                    logger.debug(f'Making histogram: {met}_{var}{vrt}')

                    bins = bin_dict[var]
                    hists.append(
                        rdf.Histo1D(
                            (f'{met}_{var}{vrt}', '', bins[2], bins[0], bins[1]),
                            f'{met}_{var}{vrt}',
                            "puWeight"
                        ).Clone()
                    )

        # save histograms
        rfile = f'{hist_dir}validation_{dtmc}.root'

        with ROOT.TFile(rfile, 'recreate') as f:
            for h in hists:
                h.Write()

        logger.info(f"{dtmc} histograms successfully saved at {rfile}.")

    return


def make_validation_plots(
    hist_dir, plot_dir, corr_dir, hbins, axislabels, lumilabel, dsetlabel,
    datamc, year, mets
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
    dsetlabel (str): Label for dataset.
    """
    logger.info("Starting validation")

    variations = [
        ['', '_stat_xup', '_stat_xdn'],
        ['', '_stat_yup', '_stat_ydn']
    ]

    for dtmc in datamc:

        # in MC also define pileup variations
        if dtmc=='MC':
            pu_variations = [['', '_pu_up', '_pu_dn']]
        else:
            pu_variations = []

        # load histograms
        rfile = f'{hist_dir}validation_{dtmc}.root'
        tf = ROOT.TFile(rfile, 'read')

        for met in mets:

            for var in ['pt', 'phi']:
            
                h = tf.Get(f"{met}_{var}")
                label_uncor = ['uncorrected']

                for vrt in variations+pu_variations:

                    hists = []
                    labels = label_uncor
                    for v in vrt:
                        hists.append(tf.Get(f"{met}_{var}_corr{v}"))
                        labels.append(f"corrected {v.replace('_', '')}")

                    outfile = f"{plot_dir}{met}_{var}{vrt[1]}_{dtmc}.pdf"
                    outfile = outfile.replace('up_', '_').replace('__', '_')

                    plot.plot_ratio(
                        h,
                        hists,
                        labels=labels,
                        dsetlabel=f'{dsetlabel} - {dtmc}',
                        axis=[axislabels[met+'_'+var], "# Events"],
                        outfile=outfile, 
                        text=['','',''], 
                        xrange=[hbins[var][0], hbins[var][1]],
                        ratiorange = [0.8, 1.2],
                        lumi = lumilabel[dtmc]
                    )

    return