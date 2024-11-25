import ROOT
import logging
from multiprocessing import Pool, RLock
from tqdm import tqdm
import os
import correctionlib
import json

import python.tools.filters as filters
import python.tools.condor_configurizer as condor 

correctionlib.register_pyroot_binding()

logger = logging.getLogger(__name__)


def get_corrections(rdf, is_data, pu_json):
    """
    Apply pileup corrections to the provided dataframe.

    Parameters:
    rdf (RDataFrame): Input ROOT RDataFrame.
    is_data (bool): Flag indicating if data or simulation.
    pu_json (str): Path to the JSON file containing pileup corrections.

    Returns:
    RDataFrame: Updated dataframe with nominal / up / dn puWeight columns.
    """
    # obtain name of correction
    cset = correctionlib.CorrectionSet.from_file(pu_json)
    cname = list(cset.keys())[0]

    # define weights
    if is_data:
        rdf = rdf.Define("puWeight", "1")
        rdf = rdf.Define("puWeightUp", "1")
        rdf = rdf.Define("puWeightDn", "1")
    else:
        ROOT.gROOT.ProcessLine(
            f"""
            auto cset = correction::CorrectionSet::from_file("{pu_json}");
            auto cs_pu = cset->at("{cname}");
            """
        )

        rdf = rdf.Define("puWeight", 
                         'cs_pu->evaluate({Pileup_nTrueInt, "nominal"})')
        rdf = rdf.Define("puWeightDn", 
                         'cs_pu->evaluate({Pileup_nTrueInt, "up"})')
        rdf = rdf.Define("puWeightUp", 
                         'cs_pu->evaluate({Pileup_nTrueInt, "down"})')

    return rdf


def make_single_snapshot(
    f, g_json, pu_json, mets, snap_dir, quants, idx, isdata
):
    """
    Creates a snapshot of filtered events and saves it to a ROOT file.

    Parameters:
    f (str): Path to the input ROOT file.
    g_json (str): Path to the golden JSON file.
    pu_json (str): Path to the JSON file containing pileup corrections.
    mets (list): List of MET types (e.g., MET, PuppiMET).
    snap_dir (str): Output snapshot directory.
    quants (list): Quantities (columns) to save in the snapshot.
    idx (int): Index for the output filename.
    isdata (bool): Flag indicating whether the input is data or simulation.

    Returns:
    None
    """

    rdf = ROOT.RDataFrame("Events", f)

    logger.debug(
        f"Processing input file {f}"
    )

    # check golden lumi
    if isdata:
        rdf = filters.filter_lumi(rdf, g_json)

    # check for dimuon Z resonance events
    rdf = filters.filter_zmm(rdf)

    # get pileup weights
    rdf = get_corrections(rdf, isdata, pu_json)

    # ensure the datatype is consistent
    npv = quants[0]
    rdf = rdf.Redefine(npv, f"static_cast<int>({npv})")

    # definition of x and y component of met
    for met in mets:
        rdf = rdf.Define(f"{met}_x", f"{met}_pt * cos({met}_phi)")
        rdf = rdf.Define(f"{met}_y", f"{met}_pt * sin({met}_phi)")

    spath = f'{snap_dir}file_{idx}.root'

    logger.debug(
        f"The rdf contains the following columns: {rdf.GetColumnNames()}"
    )
    logger.debug(
        f'Mean pileup weight" {rdf.Mean("puWeight").GetValue()}'
    )

    rdf.Snapshot("Events", spath, quants)

    return


def job_wrapper(args):
    return make_single_snapshot(*args)


def make_snapshot(
    file_path, g_json, pu_json, mets, pileups, snap_dir, 
    nthreads, condor_no, condor_dir, datamc, year, proxy_path
):
    '''
    Creates ntuples using input data and applies the necessary filters
    and corrections.

    Args:
        file_path (str): Path to the file list (JSON).
        g_json (str): Path to golden JSON file.
        pu_json (str): Path to pileup corrections JSON.
        mets (list): List of MET types.
        pileups (list): List of pileup variables.
        snap_dir (str): Output directory for snapshots.
        nthreads (int): Number of threads for multiprocessing.
        condor_no (int): Condor job number (-1 for local execution).
        condor_dir (str): Condor directory.
        datamc (list): List of dataset types (e.g., 'DATA', 'MC').
        year (str): Data taking epoch.
    '''
    logger.info("Starting production of ntuples")

    # load files
    with open(file_path, 'r') as f:
        files = json.load(f)

    for dtmc in datamc:

        logger.info(f"Now processing {dtmc}")

        infiles = files[dtmc]
        logger.debug(f"Input file list: {infiles}")

        is_data = (dtmc == 'DATA')

        # output quantities for snapshots
        quants = pileups
        quants += ['puWeight', 'puWeightUp', 'puWeightDn']
        quants += ['mass_Z']
        for met in mets:
            quants += [f'{met}_x', f'{met}_y']

        # output directory for snapshots
        snap_dir_dtmc = snap_dir+'/'+dtmc + '/'
        os.makedirs(snap_dir_dtmc, exist_ok=True)

        # arguments for running snapshot production
        arguments = [
            (f, g_json, pu_json, mets, snap_dir_dtmc, quants, idx, is_data)
            for idx, f in enumerate(infiles)
        ]

        nthreads = min(nthreads, len(infiles))

        if condor_no >= 0:
            # start single job
            job_wrapper(arguments[condor_no])

        elif nthreads==0:
            # setup condor job script
            condor.setup_job(condor_dir, dtmc, year)

            # setup condor submit file
            condor.setup_condor_lxplus(
                len(arguments),
                condor_dir,
                dtmc,
                proxy_path
            )

        else:
            # setup multiprocessing
            logger.info(
                f"Producing ntuples locally with {nthreads} threads."
            )
            pool = Pool(
                nthreads,
                initargs=(RLock,),
                initializer=tqdm.set_lock
            )
            for _ in tqdm(
                pool.imap_unordered(job_wrapper, arguments),
                total=len(arguments),
                desc="Total progess",
                dynamic_ncols=True,
                leave=True
            ): 
                pass
            logger.info("Ntuple production finished.")

    return