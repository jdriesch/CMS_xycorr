import ROOT
import argparse
import yaml
import json
import os
from tqdm  import tqdm
import tools.plot as plot
from multiprocessing import Pool, RLock

parser = argparse.ArgumentParser()
parser.add_argument(
    "-H", 
    "--hists", 
    action='store_true', 
    default=False,
    help='set to make 2d met vs npv histograms'
    )
parser.add_argument(
    "-C", 
    "--corr", 
    action='store_true', 
    default=False,
    help='set to get XY corrections'
    )
parser.add_argument(
    "-D", 
    "--datasets", 
    help="path to datasets; default is configs/datasets.yaml", 
    default='configs/datasets.yaml'
    )
parser.add_argument(
    "-S", 
    "--snapshot", 
    action='store_true', 
    default=False, 
    help="set if snapshot of data should be saved (for validation)"
    )
parser.add_argument(
    "-M",
    "--met",
    help="Comma-separated list of MET types; default is 'MET,PuppiMET'",
    default='MET,PuppiMET'
)


def filter_lumi(rdf, golden_json):
    """
    function to get rdf with events filtered with golden json
    
    (ROOT.RDataFrame) rdf: dataframe
    (str) golden_json: path to golden json
    """

    # load content of golden json
    with open(golden_json) as cf:
        goldenruns = json.load(cf)

    # extract runs and lumi sections to lists
    runs = [r for r in goldenruns.keys()]
    lumlist = [goldenruns[r] for r in goldenruns.keys()]

    # make c++ vectors of runlist and lumilist for dataframe
    runstr = "{" + ",".join(runs) + "}"
    lumstr = str(lumlist).replace("[", "{").replace("]", "}")

    # define quantity isGolden that is true iff it matches the lumi criteria
    rdf = rdf.Define(
        "isGolden",
        f"std::vector<int> runs = {runstr};"\
        f"std::vector<std::vector<std::vector<int>>> lums = {lumstr};"\
        """
            int index = -1;
            auto runidx = std::find(runs.begin(), runs.end(), run);
            if (runidx != runs.end()){
                index = runidx - runs.begin();
            }

            if (index == -1) {
                return 0;
            }

            int lumsecs = lums[index].size();
            for (int i=0; i<lumsecs; i++) {
                if (luminosityBlock >= lums[index][i][0] && luminosityBlock <= lums[index][i][1]){
                    return 1;
                }
            }

            return 0;
        """
    )
    return rdf.Filter("isGolden==1")


def make_snapshot(f, golden_json, mets, snap, quants, idx):
    rdf = ROOT.RDataFrame("Events", f)

    if isdata:
        rdf = filter_lumi(rdf, golden_json)
        # print("data filtered using golden lumi json: ", golden_json)

    # definition of x and y component of met
    for met in mets:
        rdf = rdf.Define(f"{met}_x", f"{met}_pt*cos({met}_phi)")
        rdf = rdf.Define(f"{met}_y", f"{met}_pt*sin({met}_phi)")
    spath = f'{snap}file_{idx}.root'
    rdf.Snapshot("Events", spath, quants)


def job_wrapper(args):
    return make_snapshot(*args)



def makehists(infiles, hfile, hbins, golden_json, isdata, snap, snapshot, mets):
    """
    function to make 2d histograms for xy correction

    (list) infiles: list with event root files
    (str) hfile: name of output root file with histograms
    (dict) hbins: names of npv and met with histogram bins
    (str) golden_json: path to golden json
    (bool) isdata: True if data
    (str) snap: path to snapshot if snapshot should be stored; else: False
    (list) mets: list of MET types to be processed
    """

    # create path to root output file and create file
    path = hfile.replace(hfile.split('/')[-1], '')
    os.makedirs(path, exist_ok=True)
    _met, npv = hbins.keys()
    
    hists = {}
    quants = [npv]

    for met in mets:
        hists[met+'_x'] = False
        hists[met+'_y'] = False
        quants += [f'{met}_x', f'{met}_y']

    if snapshot:
        os.makedirs(snap, exist_ok=True)

        arguments = [(f, golden_json, mets, snap, quants, idx) for idx, f in enumerate(infiles)]
        nthreads = len(infiles)

        pool = Pool(nthreads, initargs=(RLock,), initializer=tqdm.set_lock)
        for _ in tqdm(
            pool.imap_unordered(job_wrapper, arguments),
            total=len(arguments),
            desc="Total progess",
            dynamic_ncols=True,
            leave=True
        ): pass

    rdf = ROOT.RDataFrame("Events", f"{snap}file_*.root")
    # definition of 2d histograms met_xy vs npv
    for var in hists.keys():
        h = rdf.Histo2D(
            (
                var, 
                var, 
                hbins[npv][2], 
                hbins[npv][0], 
                hbins[npv][1], 
                hbins[_met][2], 
                hbins[_met][0], 
                hbins[_met][1]
            ),
            npv, var
        )
        hists[var] = h

    hfile = ROOT.TFile(hfile, "RECREATE")
    for var in hists.keys():
        hists[var].Write()
    hfile.Close()

    return


def get_corrections(hfile, hbins, corr_file, tag, plots):
    """
    function to get xy corrections and plot results

    (str) hfile: name of root file with histograms
    (dict) hbins: names of npv and met with histogram bins
    (str) corr_file: name of correction file
    (bool) isdata: True or False
    (str) plots: path to plots
    """

    met, npv = hbins.keys()

    corr_dict = {}
    for xy in ['_x', '_y']:

        # read histograms from root file
        tf = ROOT.TFile(hfile, "READ")
        h = tf.Get(met+xy)
        h.SetDirectory(ROOT.nullptr)
        tf.Close()

        # define and fit pol1 function
        f1 = ROOT.TF1("pol1", "[0]*x+[1]", -10, 110)
        h.Fit(f1, "R", "", 0, 100)

        # save fit parameter
        corr_dict[xy] = {
            "m": f1.GetParameter(0),
            "c": f1.GetParameter(1)
        }

        # plot fit results
        plot.plot_2dim(
            h,
            title=tag,
            axis=['NPV', f'{met}{xy} (GeV)'],
            outfile=f"{plots}{met+xy}",
            xrange=[0,100],
            yrange=[hbins[met][0], hbins[met][1]],
            lumi='2022, 13.6 TeV',
            line=f1,
            results=[round(corr_dict[xy]["m"],3), round(corr_dict[xy]["c"],3)]
        )

    os.makedirs(corr_file, exist_ok=True)
    with open(f"{corr_file}{met}.yaml", "w") as f:
        yaml.dump(corr_dict, f)
            
    return


if __name__=='__main__':
    args = parser.parse_args()
    datasets = args.datasets
    mets = args.met.split(',')

    # load datasets
    with open(datasets, "r") as f:
        dsets = yaml.load(f, Loader=yaml.Loader)

    # define histogram bins
    hbins = {
        'met': [-200, 200, 200],
        'PV_npvsGood': [0, 100, 100]
    }

    for year in dsets:
        dir_plots = f"results/plots/{year}/"
        path_corrs = f"results/corrections/{year}.root"

        for dtmc in dsets[year]:
            isdata = (dtmc=="data")
            snaps = f"results/snapshots/{year}/{dtmc}/"
            os.makedirs(snaps, exist_ok=True)

            with open(f'configs/data/{year+dtmc}.yaml') as f:
                files = yaml.load(f, Loader=yaml.Loader)

            for era in dsets[year][dtmc]:
                os.makedirs(f'results/hists/{year}', exist_ok=True)
                path_hists = f"results/hists/{year}/{era}.root"

                # make list of root files of the sample
                rootfiles = files[era]

                if isdata:
                    golden_json = dsets[year][dtmc][era]["gjson"]
                else:
                    golden_json = ''

                if args.hists:
                    if os.path.exists(path_hists):
                        ow = input(f"File {path_hists} already exists. Overwrite? (y/n)")
                        if ow!="y":
                            print("File will not be overwritten.")
                            continue
                
                    makehists(rootfiles, path_hists, hbins, golden_json, isdata, snaps, args.snapshot, mets)

                if args.corr:
                    get_corrections(hists, hbins, corr_files, tag, plots)

