# general packages
import ROOT
import json
import logging

# correction steps
from python.correction.snapshot_maker import make_snapshot, check_snapshots
from python.correction.histograms import make_hists
from python.correction.correction_extractor import get_corrections

# python inputs
from inputs.config.paths import get_paths
from inputs.config.binning import get_bins
from inputs.config.labels import get_labels

# tools
from python.tools.parsers import parse_arguments
from python.tools.logger_setup import setup_logger
from python.tools.das_query import get_files_from_das
from python.tools.validate import make_validation_plots
from python.tools.convert2json import build_combined_dict, make_correction_with_formula, validate_json

ROOT.gROOT.SetBatch(1)


def main():

    # get inputs
    args = parse_arguments()
    path_dict = get_paths(args)
    hbins = get_bins()
    mets = args.met.split(',')
    datamc = args.processes.split(',')
    lumilabels, axislabels = get_labels(args.year)

    # setup logger
    setup_logger('main.log', args.debug)
    logger = logging.getLogger(__name__)

    logger.info(
        f"Main script started for {args.year} and {args.met}."
    )

    # Preparation: getting files from DAS
    if args.prep:
        get_files_from_das(
            path_dict['datasets'],
            path_dict['nanoAODs'],
            args.year
        )

    # step 1: make flat ntuples with necessary information
    if args.snapshot:
        make_snapshot(
            path_dict['nanoAODs'],
            path_dict['golden_json'], 
            path_dict['pu_json'],
            mets, 
            list(hbins['pileup'].keys()),
            path_dict['snap_dir'],
            args.jobs,
            args.condor, path_dict['condor_dir'],
            datamc,
            args.year
        )
        check_snapshots(path_dict['snap_dir'], datamc)

    # step 2: make 2d histograms met xy vs pileup
    if args.hists:
        make_hists(
            path_dict['snap_dir'],
            path_dict['hist_dir'],
            hbins,
            args.jobs,
            mets
        )

    # step 3: fit linear functions to 2d histograms
    if args.corr:
        get_corrections(
            path_dict['hist_dir'],
            hbins,
            path_dict['corr_dir'],
            path_dict['plot_dir'],
            mets,
            lumilabels
        )

    # make correction lib schema v2
    if args.convert != '':
        combined_dict = build_combined_dict(
            mets=mets,
            epochs=args.convert.split(','),
            corr_dir=path_dict['corr_dir'],
            year=args.year
        )
        make_correction_with_formula(
            combined_dict,
            path_dict['corr_dir'],
            args.year
        )

    # closure
    # TODO: make flexible wrt year
    if args.validate:
        # make_validation_plots(
        #     path_dict['snap_dir'],
        #     path_dict['plot_dir'],
        #     path_dict['corr_dir'],
        #     hbins,
        #     axislabels,
        #     lumilabels
        # )
        validate_json()

if __name__=='__main__':
    main()

