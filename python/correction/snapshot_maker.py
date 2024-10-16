import ROOT
import logging
from multiprocessing import Pool, RLock
from tqdm import tqdm
import os
import correctionlib
from glob import glob

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

    if is_data:
        rdf = rdf.Define("puWeight", "1")
        rdf = rdf.Define("puWeightUp", "1")
        rdf = rdf.Define("puWeightDn", "1")
    else:
        ROOT.gROOT.ProcessLine(
            f'auto cs_pu = correction::CorrectionSet::from_file("{pu_json}")'
            '->at("puweights");'
        )  # Ensure 'puweights' name is consistent with correction file

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

    if isdata:
        rdf = filters.filter_lumi(rdf, g_json)

    # filter dimuon events in Z region
    rdf = rdf.Define(
        "ind",
        f"""ROOT::VecOps::RVec<Int_t> (get_indices(
            nMuon,
            &Muon_pt,
            &Muon_eta,
            &Muon_phi,
            &Muon_mass,
            &Muon_pfIsoId,
            &Muon_tightId,
            &Muon_charge,
            25,
            91.1876,
            20,
            4
            ))"""
    )
    rdf = rdf.Define("ind0", "ind[0]")
    rdf = rdf.Define("ind1", "ind[1]")
    rdf = rdf.Filter("ind0 + ind1 > 0")
    rdf = rdf.Define("pt_1", "Muon_pt[ind[0]]")
    rdf = rdf.Define("pt_2", "Muon_pt[ind[1]]")
    rdf = rdf.Define("eta_1", "Muon_eta[ind[0]]")
    rdf = rdf.Define("eta_2", "Muon_eta[ind[1]]")
    rdf = rdf.Define("phi_1", "Muon_phi[ind[0]]")
    rdf = rdf.Define("phi_2", "Muon_phi[ind[1]]")

    rdf = get_trigger_matches(rdf)
    rdf = get_corrections(rdf, isdata, pu_json)

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
    nthreads, condor_no, condor_dir, datamc, year
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

        quants = pileups + ['puWeight', 'puWeightUp', 'puWeightDn']
        snap_dir_dtmc = snap_dir+'/'+dtmc + '/'
        os.makedirs(snap_dir_dtmc, exist_ok=True)

        for met in mets:
            quants += [f'{met}_x', f'{met}_y']

        arguments = [
            (f, g_json, pu_json, mets, snap_dir_dtmc, quants, idx, is_data)
            for idx, f in enumerate(infiles)
        ]

        nthreads = min(nthreads, len(infiles))

        if condor_no >= 0:
            job_wrapper(arguments[condor_no])

        else:
            logger.info(
                f"The number of files to produce is: {len(arguments)}."
            )
            do_proceed = input(
                f"Want to proceed producing the ntuples locally "
                "with {nthreads} threads? (y/n)"
            )

            if do_proceed == 'y':
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
            else:
                condor.setup_job(condor_dir, dtmc, year)
                condor.setup_condor_etp(len(arguments), condor_dir, dtmc)

    return


def check_snapshots(snap_dir, datamc):
    '''
    Check whether produced snapshots are usable.

    Args:
    snap_dir (str): Directory of snapshots.
    datamc (list): List of dataset types (e.g., 'DATA', 'MC').
    '''
    logger.info(f"Checking snapshots in {snap_dir} for {dtmc}")

    zombies = []
    notrees = []
    noevents = []

    for dtmc in datamc:
        files = f'{snap_dir}{dtmc}/*.root'

        files = glob(files)

        for f in files:
            try:
                f_tmp = ROOT.TFile.Open(f)

                if f_tmp.IsZombie():
                    zombies.append(f)

                else:
                    tree = f_tmp.Get("Events")
                    if not tree:
                        notrees.append(f)
                    
                    if tree.GetEntries() == 0:
                        noevents.append(f)

            except OSError:
                zombies.append(f)

    logger.info(
        f"The following files are zombies: {zombies}\n"
        f"The following files have no tree 'Events': {notrees}\n"
        f"The following files have zero entries: {noevents}\n"
    )

    failed_files = zombies + notrees + noevents

    if len(failed_files)>0:

        do_delete = (input("Would you like to delete them? (y/n)")=='y')

        if do_delete:
            logger.info("Deleting selected files.")
            for f in failed_files:
                os.remove(f)

        else:
            logger.info(
                "Not deleting corrupted files. "
                "There may be problems in the subsequent steps."
            )

    return
