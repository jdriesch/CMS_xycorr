import ROOT
import os
import python.tools.plot as plot
import json

def get_corrections(
    hist_dir, hbins, corr_dir, plot_dir, mets, pileups, 
    lumilabel, axislabels, datamc
):
    """
    function to get xy corrections and plot results

    hist_dir (str): Directory of histograms.
    hbins (dict): Dictionary with histogram binnings.
    corr_dir (str): Directory for correction jsons.
    plot_dir (str): Directory for plots.
    mets (list): List of mets.
    pileups (list): List of pileups.
    lumilabel (dict): Dictionary for lumi label position and text.
    axislabels (dict): Dictionary for axis labels.
    datamc (list): List of datasets to process (data / mc).
    """

    corr_dict = {}
    for dtmc in datamc:
        for met in mets:
            corr_dict[met] = {}
            for pu in pileups:
                corr_dict[met][pu] = {}
                for xy in ['_x', '_y']:
                    corr_dict[met][pu][xy] = {}

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
                        h = tf.Get(f'{pu}_{met}{xy}{variations[variation]}')
                        h.SetDirectory(ROOT.nullptr)
                        tf.Close()

                        # define and fit pol1 function
                        f1 = ROOT.TF1("pol1", "[0]*x+[1]", -10, 110)
                        fitresult = h.Fit(f1, "R S", "", 10, 70)

                        # save fit parameter
                        corr_dict[met][pu][xy][variation] = {
                            "m": f1.GetParameter(0),
                            "m_stat": f1.GetParError(0),
                            "c": f1.GetParameter(1),
                            "c_stat": f1.GetParError(1),
                            "correlation": fitresult.Correlation(0,1)
                        }

                        stat_unc = " sqrt( x*x*[2]*[2] + [3]*[3] + 2*[4]*x*[2]*[3] )"

                        f1_up = ROOT.TF1("pol1up", f"[0]*x+[1] + {stat_unc}", -10, 110)
                        f1_up.SetParameter(0, f1.GetParameter(0))
                        f1_up.SetParameter(1, f1.GetParameter(1))
                        f1_up.SetParameter(2, f1.GetParError(0))
                        f1_up.SetParameter(3, f1.GetParError(1))
                        f1_up.SetParameter(4, fitresult.Correlation(0,1))
                        f1_dn = ROOT.TF1("pol1dn", f"[0]*x+[1] - {stat_unc}", -10, 110)
                        f1_dn.SetParameter(0, f1.GetParameter(0))
                        f1_dn.SetParameter(1, f1.GetParameter(1))
                        f1_dn.SetParameter(2, f1.GetParError(0))
                        f1_dn.SetParameter(3, f1.GetParError(1))
                        f1_dn.SetParameter(4, fitresult.Correlation(0,1))

                        # if variation == "nom":
                        # plot fit results
                        plot.plot_2dim(
                            h,
                            axis=[axislabels['pileup'], (met+xy+'} (GeV)').replace('_', '_{')],
                            outfile=f"{plot_dir}{met}/{dtmc+xy}_{variation}",
                            xrange=[0,100],
                            yrange=[hbins['met'][0], hbins['met'][1]],
                            lumi=lumilabel[dtmc],
                            lines=[f1_up, f1_dn, f1],
                            results=[
                                round(corr_dict[met][pu][xy][variation]["m"],3),
                                round(corr_dict[met][pu][xy][variation]["c"],3),
                                round(corr_dict[met][pu][xy][variation]["m_stat"],3),
                                round(corr_dict[met][pu][xy][variation]["c_stat"],3),
                            ]
                        )

        with open(f"{corr_dir+dtmc}.json", "w") as f:
            json.dump(corr_dict, f, indent=4)
            
    return