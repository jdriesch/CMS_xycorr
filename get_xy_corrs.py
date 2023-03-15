import ROOT
import argparse
import numpy as np
import json
import os

parser = argparse.ArgumentParser()
parser.add_argument("--hists", action='store_true', default=False)
parser.add_argument("--corr", action='store_true', default=False)


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


def makehists(fdict, rfile, hbins, golden_json):
    """
    function to make 2d histograms for xy correction

    (dict) fdict: dictionary with mc and data root files
    (str) rfile: name of root file with histograms
    (dict) hbins: names of npv and met with histogram bins
    """

    # create path to root output file and create file
    path = rfile.replace(rfile.split('/')[-1], '')
    os.makedirs(path, exist_ok=True)
    rfile = ROOT.TFile(rfile, "RECREATE")

    met, npv = hbins.keys()

    # loop over data and mc
    for dtmc in fdict.keys():

        # prepare chain and create rdf
        chain = ROOT.TChain("Events")
        for f in fdict[dtmc]:
            chain.Add(f)

        rdf = ROOT.RDataFrame(chain)

        if dtmc == 'data':
            rdf = filter_lumi(rdf, golden_json)
            print("data filtered using golden lumi json: ", golden_json)

        # definition of x and y component of met
        rdf = rdf.Define(f"{met}_x", f"{met}_pt*cos({met}_phi)")
        rdf = rdf.Define(f"{met}_y", f"{met}_pt*sin({met}_phi)")
        
        # definition of 2d histograms met_xy vs npv
        for xy in ["_x", "_y"]:
            h = rdf.Histo2D(
                (
                    dtmc+met+xy, 
                    met+xy, 
                    hbins[npv][2], 
                    hbins[npv][0], 
                    hbins[npv][1], 
                    hbins[met][2], 
                    hbins[met][0], 
                    hbins[met][1]
                ),
                npv, met+xy,
            )
            h.Write()

    rfile.Close()

    return


def get_corrections(fdict, rfile, hbins, corr_file):
    """
    function to get xy corrections and plot results

    (dict) fdict: dictionary with mc and data root files
    (str) rfile: name of root file with histograms
    (dict) hbins: names of npv and met with histogram bins
    (str) corr_file: name of correction file
    """

    met, npv = hbins.keys()

    corr_dict = {}
    for dtmc in fdict.keys():
        for xy in ['_x', '_y']:

            # read histograms from root file
            tf = ROOT.TFile(rfile, "READ")
            h = tf.Get(dtmc+met+xy)
            h.SetDirectory(ROOT.nullptr)
            tf.Close()

            # define and fit pol1 function
            f1 = ROOT.TF1("pol1", "[0]*x+[1]", -10, 110)
            h.Fit(f1, "R", "", 0, 100)

            # save fit parameter
            corr_dict[dtmc+xy] = {
                "m": f1.GetParameter(0),
                "c": f1.GetParameter(1)
            }

            # plot fit results
            plot_2dim(
                h,
                title=dtmc,
                axis=['NPV', f'{met}{xy} (GeV)'],
                outfile=f"plots/{dtmc+xy}",
                xrange=[0,100],
                yrange=[hbins[met][0], hbins[met][1]],
                lumi='2022, 13.6 TeV',
                line=f1,
            )

    with open(corr_file, "w") as f:
        json.dump(corr_dict, f)
            
    return
    

def plot_2dim(
        h,
        title="",
        axis=["",""],
        outfile="dummy.pdf",
        xrange = [0,100],
        yrange = [-100,100],
        lumi = '2022, 13.6 TeV',
        drawoption='COLZ',
        line = False,
    ):
    c = ROOT.TCanvas("c", title, 800, 700)
    ROOT.gROOT.SetBatch(1)
    ROOT.gPad.SetGrid()
    
    h.SetStats(0)
    h.GetXaxis().SetRangeUser(xrange[0], xrange[1])
    h.GetYaxis().SetRangeUser(yrange[0], yrange[1])

    h.GetXaxis().SetLabelSize(0.03)
    #h.GetXaxis().SetTitleOffset(0.1)
    h.GetXaxis().SetTitleSize(0.03)
    h.GetXaxis().SetTitle(axis[0])

    h.GetYaxis().SetLabelSize(0.03)
    h.GetYaxis().SetTitle(axis[1])
    h.GetYaxis().SetTitleOffset(1.2)
    h.GetYaxis().SetTitleSize(0.03)

    h.Draw(drawoption)
    h.SetTitle(title)

    cmsTex=ROOT.TLatex()
    cmsTex.SetTextFont(42)
    cmsTex.SetTextSize(0.025)
    cmsTex.SetNDC()
    cmsTex.SetTextSize(0.035)
    cmsTex.DrawLatex(0.11,0.915,'#bf{CMS} #it{Preliminary}')
    cmsTex.DrawLatex(0.60, 0.915, lumi)

    if line:
        prof = h.ProfileX("prof", 0, 200)
        prof.SetLineWidth(2)
        prof.SetLineColor(ROOT.kBlack)
        prof.Draw("same")
        line.Draw("same")
    
    path = outfile.replace(outfile.split('/')[-1], '')
    os.makedirs(path, exist_ok=True)

    c.SaveAs(outfile+'.pdf')    
    c.SaveAs(outfile+'.png')

    return


if __name__=='__main__':
    args = parser.parse_args()
    hists = 'hists/hists.root'    
    corr_file = 'corr.json'
    golden_json = 'Cert_Collisions2022_eraC_355862_357482_Golden.json'

    rootlib = "root://xrootd-cms.infn.it//"
    path_data = "/store/data/Run2022C/Muon/NANOAOD/PromptNanoAODv10_v1-v1/2520000/"
    path_mc = "/store/mc/Run3Summer22NanoAODv11/DYto2L-2Jets_MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/NANOAODSIM/126X_mcRun3_2022_realistic_v2-v1/2560000/"


    fdict = {
        'data': [
            rootlib+path_data+"1d902a9f-0383-4fe5-9bb5-1ddc57f155fb.root",
            rootlib+path_data+"26a9a100-7f53-4dcf-afc7-f510bd83b80b.root",
        ],
        'mc': [
            rootlib+path_mc+"055461fb-e9b3-4c9d-ac5c-0c794b7e6006.root",
            rootlib+path_mc+"09d0bebf-fb5b-4f04-95ab-e6ac8f7e5dee.root",
        ],
    }   

    hbins = {
        'MET': [-200, 200, 200],
        'PV_npvsGood': [0, 100, 100]
    }
    
    if args.hists:
        makehists(fdict, hists, hbins, golden_json)

    if args.corr:
        get_corrections(fdict, hists, hbins, corr_file)

