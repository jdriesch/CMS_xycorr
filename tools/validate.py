import ROOT
import yaml
import os
import sys
import plot


def correctXY(rdf, met, corrs):
    """
    (ROOT.RDataFrame) rdf: Dataframe
    (str) met: type of MET
    (str) corrs: path of correction file
    """
    with open(corrs, 'r') as f:
        c = yaml.load(f, Loader=yaml.Loader)

    cmet = f"Corrected{met}"
    for xy in c.keys():
        rdf = rdf.Define(
            f"{cmet}{xy}", 
            f"{met}{xy} - ({c[xy]['m']}*PV_npvsGood + {c[xy]['c']})"
            )

    for m in [met, cmet]:
        rdf = rdf.Define(f"{m}_pt", f"sqrt({m}_x*{m}_x + {m}_y*{m}_y)")
        rdf = rdf.Define(f"{m}_phi", f"atan2({m}_y, {m}_x)")
    
    return rdf


def validation_plots(rdf, hbins, hlabels, plots, tag):
    """
    (ROOT.RDataFrame) rdf: Dataframe
    (dict) hbins: names and bins of validation histograms
    (str) plots: path to plots
    """

    for var in hbins.keys():
        h = rdf.Histo1D(
            (var, var, hbins[var][2], hbins[var][0], hbins[var][1]),
            var
        )

        hc = rdf.Histo1D(
            (f"Corrected{var}", var, hbins[var][2], hbins[var][0], hbins[var][1]),
            f"Corrected{var}"
        )

        plot.plot_ratio(
            hc, # data plot
            h,  # mc plot
            labels=["corrected", "uncorrected"], 
            axis=[hlabels[var], "# Events"],
            title=tag, 
            outfile=f"{plots}{var}.pdf", 
            text=['','',''], 
            xrange=[hbins[var][0], hbins[var][1]],
            ratiorange = [0.8, 1.2],
            lumi = '2022, 13.6 TeV'
        )

    

if __name__=='__main__':
    dname = sys.argv[1]
    datasets = f'../configs/{dname}'
    met = 'MET'

    # load datasets
    with open(datasets, "r") as f:
        dsets = yaml.load(f, Loader=yaml.Loader)

    # define histogram bins
    hbins = {
        f"{met}_pt": [0, 200, 100],
        f"{met}_phi": [-3.14, 3.14, 30],
    }
    hlabels = {
        f"MET_pt": "PFMET (GeV)",
        f"MET_phi": "#phi (MET)"
    }

    # go through runs / mc
    for tag in dsets.keys():
        rfiles = [f"../results/snapshots/{tag}/{met}*.root"]
        corr_file = f"../results/corrections/{tag}/{met}.yaml"
        plots = f"../results/plots/{tag}/validation_"

        
        rdf = ROOT.RDataFrame("Events", rfiles)
        print(rdf.Count().GetValue())

        rdf = correctXY(rdf, met, corr_file)
        print(rdf.Count().GetValue())

        validation_plots(rdf, hbins, hlabels, plots, tag)
