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


def get_corrections(df, is_data, SFs, pu_json):
    if is_data:
        rdf = df.Define("sf_iso", "1")
        rdf = rdf.Define("sf_id", "1")
        rdf = rdf.Define("sf_trg", "1")
        rdf = rdf.Define("puWeight", "1")
        rdf = rdf.Define("puWeightUp", "1")
        rdf = rdf.Define("puWeightDn", "1")

    else:

        trgpath = SFs['trg'][0]
        trgname = SFs['trg'][1]
        ROOT.gROOT.ProcessLine(f'''
            TFile *trg_tf = TFile::Open("{trgpath}", "READ");
            TH2F *trg_mc = (TH2F*)trg_tf->Get("{trgname}_efficiencyMC");
            TH2F *trg_dt = (TH2F*)trg_tf->Get("{trgname}_efficiencyData");
        ''')

        path_id, name_id = SFs['id'][0], SFs['id'][1]
        path_iso, name_iso = SFs['iso'][0], SFs['iso'][1]
        print(path_id, name_id)
        ROOT.gROOT.ProcessLine(
            f'auto cset_id = correction::CorrectionSet::from_file("{path_id}")->at("{name_id}");\
            auto cset_iso = correction::CorrectionSet::from_file("{path_iso}")->at("{name_iso}");\
            auto cset_pu = correction::CorrectionSet::from_file("{pu_json}")->at("puweights");'
        ) # changed puweights name to be consistent

        rdf = df.Define("sf_id_1", 'cset_id->evaluate({abs(eta_1), pt_1, "nominal"})')
        rdf = rdf.Define("sf_id_2", 'cset_id->evaluate({abs(eta_2), pt_2, "nominal"})')
        rdf = rdf.Define("sf_id", "sf_id_1 * sf_id_2")

        rdf = rdf.Define("sf_iso_1", 'cset_iso->evaluate({abs(eta_1), pt_1, "nominal"})')
        rdf = rdf.Define("sf_iso_2", 'cset_iso->evaluate({abs(eta_2), pt_2, "nominal"})')
        rdf = rdf.Define("sf_iso", "sf_iso_1 * sf_iso_2")

        rdf = rdf.Define("sf_trg", 'get_trg_sf(eta_1, eta_2, pt_1, pt_2, trg_match_1, trg_match_2, *trg_mc, *trg_dt)')

        rdf = rdf.Define("puWeight", 'cset_pu->evaluate({Pileup_nTrueInt, "nominal"})')
        rdf = rdf.Define("puWeightDn", 'cset_pu->evaluate({Pileup_nTrueInt, "up"})')
        rdf = rdf.Define("puWeightUp", 'cset_pu->evaluate({Pileup_nTrueInt, "down"})')

    return rdf


def get_trigger_matches(df):
    
    rdf = df.Define("trg_ind0", "trg_match_ind(eta_1, phi_1, nTrigObj, &TrigObj_id, &TrigObj_eta, &TrigObj_phi, -99)")
    rdf = rdf.Define("trg_ind1", "trg_match_ind(eta_2, phi_2, nTrigObj, &TrigObj_id, &TrigObj_eta, &TrigObj_phi, trg_ind0)")
    rdf = rdf.Filter("trg_ind0 >= 0 || trg_ind1 >= 0")

    rdf = rdf.Define("trg_match_1", "int match; if(trg_ind0 >= 0) match = 1; else match = 0; return match;")
    rdf = rdf.Define("trg_match_2", "int match; if(trg_ind1 >= 0) match = 1; else match = 0; return match;")

    return rdf



def make_single_snapshot(f, golden_json, pu_json, mets, snap, quants, idx, isdata, SFs):
    rdf = ROOT.RDataFrame("Events", f)

    if isdata:
        rdf = filters.filter_lumi(rdf, golden_json)

    # filter dimuon events in Z region
    rdf = rdf.Define("ind", f"""ROOT::VecOps::RVec<Int_t> (get_indices(
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
                            ))""")
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
    rdf = get_corrections(rdf, isdata, SFs, pu_json)

    # definition of x and y component of met
    for met in mets:
        rdf = rdf.Define(f"{met}_x", f"{met}_pt*cos({met}_phi)")
        rdf = rdf.Define(f"{met}_y", f"{met}_pt*sin({met}_phi)")
    spath = f'{snap}file_{idx}.root'

    logger.debug(f"The rdf contains the following columns: {rdf.GetColumnNames()}")

    print(rdf.Mean("puWeight").GetValue())
    print(rdf.Mean("sf_iso").GetValue())
    print(rdf.Mean("sf_trg").GetValue())
    print(rdf.Mean("sf_id").GetValue())

    quants += ['puWeight', 'puWeightUp', 'puWeightDn', 'sf_iso', 'sf_trg', 'sf_id']
    rdf.Snapshot("Events", spath, quants)

    return


def job_wrapper(args):
    return make_single_snapshot(*args)


def make_snapshot(files, golden_json, pu_json, mets, pileups, snap_dir, nthreads, condor_no, condor_dir, datamc, SFs, year):
    '''
    (str) golden_json: path to golden json
    '''
    logger.info("Starting production of ntuples")

    for dtmc in datamc:
        if dtmc == 'skip': continue
        logger.info(f"Now processing {dtmc}")

        infiles = files[dtmc]
        logger.debug(f"Input file list: {infiles}")

        is_data = (dtmc == 'DATA')

        quants = pileups

        snap_dir_dtmc = snap_dir+'/'+dtmc + '/'
        os.makedirs(snap_dir_dtmc, exist_ok=True)

        for met in mets:
            quants += [f'{met}_x', f'{met}_y']

        arguments = [(f, golden_json, pu_json, mets, snap_dir_dtmc, quants, idx, is_data, SFs) for idx, f in enumerate(infiles)]
        nthreads = min(nthreads, len(infiles))

        if condor_no >= 0:
            job_wrapper(arguments[condor_no])

        else:
            logger.info(f"The number of files to produce is: {len(arguments)}.")
            do_proceed = input(f"Want to proceed producing the ntuples locally with {nthreads} threads? (y/n)")

            if do_proceed == 'y':
                pool = Pool(nthreads, initargs=(RLock,), initializer=tqdm.set_lock)
                for _ in tqdm(
                    pool.imap_unordered(job_wrapper, arguments),
                    total=len(arguments),
                    desc="Total progess",
                    dynamic_ncols=True,
                    leave=True
                ): pass
                logger.info("Ntuple production finished.")
            else:
                condor.setup_job(condor_dir, dtmc, year)
                condor.setup_condor_etp(len(arguments), condor_dir, dtmc)

    return


def check_snapshots(snap_dir, datamc):
    zombies = []
    notrees = []
    noevents = []

    for dtmc in datamc:
        files = f'{snap_dir}{dtmc}/*.root'
        logger.info(f"Checking snapshots {files}")

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
            logger.info("Not deleting corrupted files. There may be problems in the subsequent steps.")

    return
