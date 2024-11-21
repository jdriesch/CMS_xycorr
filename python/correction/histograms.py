import ROOT
import logging

logger = logging.getLogger(__name__)

def make_hists(snap_dir, hist_dir, hbins, jobs, mets, datamc):
    """
    function to make 2d histograms for xy correction

    snap_dir (str): Directory of snapshots.
    hist_dir (str): Output directory for histograms.
    hbins (dict): Dictionary with histogram binnings.
    jobs (int): Number of threads for parallel processing.
    mets (list): List of mets to process.
    datamc (list): List of datasets to process (data / mc).
    """

    if jobs > 1:
        ROOT.EnableImplicitMT(jobs)

    for dtmc in datamc:
        n = max(jobs, 1)
        logger.info(
            f"Starting histogram production for {dtmc} with {n} threads."
        )

        is_data = (dtmc=='DATA')

        hists = {}

        rdf = ROOT.RDataFrame("Events", f"{snap_dir}/{dtmc}/file_*.root")

        for met in mets:
            met_vars = [met+'_x', met+'_y']

            for npv in hbins['pileup']:

                for variation in ["", "Up", "Dn"]:      
                    # definition of 2d histograms met_xy vs npv
                    for var in met_vars:
                        h = rdf.Histo2D(
                            (
                                f'{var}_puweight{variation}', 
                                '', 
                                hbins['pileup'][npv][2], 
                                hbins['pileup'][npv][0], 
                                hbins['pileup'][npv][1], 
                                hbins['met'][met][2], 
                                hbins['met'][met][0], 
                                hbins['met'][met][1]
                            ),
                            npv, var,
                            "puWeight"+variation
                        )
                        hists[f'{var}_puweight{variation}'] = h

        rfile = hist_dir+dtmc+'.root'
        hfile = ROOT.TFile(rfile, "recreate")
        for var in hists.keys():
            hists[var].Write()
        hfile.Close()

        logger.info(
            f"Histogram production finished for {dtmc}. Saved in {rfile}"
        )

    return