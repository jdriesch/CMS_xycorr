# general packages
import ROOT
import json
import logging

# correction steps
from python.correction.snapshot_maker import make_snapshot, check_snapshots
from python.correction.histograms import make_hists
from python.correction.correction_extractor import get_corrections

# input paths
from python.inputs.parsers import parse_arguments
from python.inputs.paths import get_paths
from python.inputs.binning import get_bins
from python.inputs.logger_setup import setup_logger
from python.inputs.labels import get_labels

# scripts
from python.tools.das_query import get_files_from_das
from python.tools.validate import make_validation_plots


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
        get_files_from_das(path_dict['datasets'])

    # step 1: make flat ntuples with necessary information
    if args.snapshot:
        make_snapshot(
            path_dict['files'],
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
            args.jobs
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

    # closure
    if args.validate:
        make_validation_plots(
            path_dict['snap_dir'],
            path_dict['plot_dir'],
            path_dict['corr_dir'],
            hbins,
            axislabels,
            lumilabels
        )


if __name__=='__main__':
    main()

