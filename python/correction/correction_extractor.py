import ROOT
import os
import python.tools.plot as plot
import json

def get_corrections(hist_dir, hbins, corr_dir, plot_dir, mets, lumilabel):
    """
    function to get xy corrections and plot results

    hist_dir (str): Directory of histograms.
    hbins (dict): Dictionary with histogram binnings.
    corr_dir (str): Directory for correction jsons.
    plot_dir (str): Directory for plots.
    mets (list): List of mets
    lumilabel (dict): Dictionary for lumi label position and text
    """

    corr_dict = {}
    for dtmc in ['DATA', 'MC']:
        for met in mets:
            corr_dict[met] = {}
            for xy in ['_x', '_y']:
                corr_dict[met][xy] = {}

                if dtmc == 'DATA':
                    variations = {
                        'nom': '_puweight',
                    }

                else:
                    variations = {
                        'nom': '_puweight',
                        'pu_dn': '_puweightDn',
                        'pu_up': '_puweightUp'
                    }

                for variation in variations:

                    # read histograms from root file
                    tf = ROOT.TFile(hist_dir+dtmc+'.root', "READ")
                    h = tf.Get(met+xy+variations[variation])
                    h.SetDirectory(ROOT.nullptr)
                    tf.Close()

                    # define and fit pol1 function
                    f1 = ROOT.TF1("pol1", "[0]*x+[1]", -10, 110)
                    h.Fit(f1, "R", "", 10, 70)

                    # save fit parameter
                    corr_dict[met][xy][variation] = {
                        "m": f1.GetParameter(0),
                        "c": f1.GetParameter(1),
                    }
                    if variation == 'nom':
                        corr_dict[met][xy]["stat"] = {
                            "m": f1.GetParError(0),
                            "c": f1.GetParError(1),
                        }

                        # plot fit results
                        plot.plot_2dim(
                            h,
                            axis=['NPV', (met+xy+'} (GeV)').replace('_', '_{')],
                            outfile=f"{plot_dir}{met+xy+'_'+dtmc}",
                            xrange=[0,100],
                            yrange=[hbins['met'][met][0], hbins['met'][met][1]],
                            lumi=lumilabel[dtmc],
                            line=f1,
                            results=[
                                round(corr_dict[met][xy][variation]["m"],3),
                                round(corr_dict[met][xy][variation]["c"],3)
                            ]
                        )

        with open(f"{corr_dir+dtmc}.json", "w") as f:
            json.dump(corr_dict, f, indent=4)
            
    return