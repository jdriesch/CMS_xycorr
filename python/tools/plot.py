import ROOT
import os
import logging

logger = logging.getLogger(__name__)


def plot_2dim(
        h,
        axis=["",""],
        outfile="dummy.pdf",
        xrange = [0,100],
        yrange = [-100,100],
        lumi = ['2022, 13.6 TeV', 0.2],
        drawoption='COLZ',
        line = False,
        results = ["", ""]
    ):
    c = ROOT.TCanvas("c", '', 800, 600)
    ROOT.gROOT.SetBatch(1)
    ROOT.gPad.SetGrid()

    h.SetStats(0)
    h.GetXaxis().SetRangeUser(xrange[0], xrange[1])
    h.GetYaxis().SetRangeUser(yrange[0], yrange[1])

    h.GetXaxis().SetLabelSize(0.04)
    h.GetXaxis().SetTitleOffset(1.05)
    h.GetXaxis().SetTitleSize(0.045)
    h.GetXaxis().SetTitle(axis[0])

    h.GetYaxis().SetLabelSize(0.04)
    h.GetYaxis().SetTitle(axis[1])
    h.GetYaxis().SetTitleOffset(1.05)
    h.GetYaxis().SetTitleSize(0.045)

    c.SetRightMargin(0.12)
    ROOT.TGaxis.SetMaxDigits(3)

    h.Draw(drawoption)
    h.SetTitle('')

    cmsTex=ROOT.TLatex()
    cmsTex.SetTextFont(42)
    cmsTex.SetTextSize(0.025)
    cmsTex.SetNDC()
    cmsTex.SetTextSize(0.04)
    cmsTex.DrawLatex(0.11,0.915,'#bf{CMS} #it{Preliminary}')
    cmsTex.DrawLatex(0.9 - lumi[1], 0.915, lumi[0])

    cmsTex.SetTextSize(0.02)
    stats = ROOT.TPaveText(0.47, 0.82, 0.86, 0.88, "br ARC NDC")
    stats.SetFillColorAlpha(ROOT.kGray, 0.8)
    stats.AddText(fr"Fit result: {results[0]} \times NPV + {results[1]}")
    stats.GetListOfLines().Last().SetTextColor(ROOT.kRed)
    stats.Draw("SAME")

    if line:
        prof = h.ProfileX("prof", 0, 200)
        prof.SetLineWidth(2)
        prof.SetLineColor(ROOT.kBlack)
        prof.Draw("same")
        line.Draw("same")
    
    path = outfile.replace(outfile.split('/')[-1], '')
    os.makedirs(path, exist_ok=True)

    c.SaveAs(outfile+'.png')
    c.SaveAs(outfile+'.pdf')    

    return




def plot_ratio(
        h0, # data plot
        h1,  # mc plot
        labels=["", ""], 
        axis=["", ""],
        title="", 
        outfile="dummy.pdf", 
        text=['','',''], 
        xrange=[60, 120],
        ratiorange = [0.8, 1.2],
        lumi = ['5.05 fb^{-1} (2022, 13.6 TeV)', 0.2]
    ):
    c = ROOT.TCanvas("c", title, 800, 700)
    ROOT.gROOT.SetBatch(1)

    # Split canvas
    pad1 = ROOT.TPad("pad1", "pad1", 0,0.3,1,1)
    pad1.SetBottomMargin(0.03)
    pad1.SetLeftMargin(0.1)

    # Upper pad
    pad1.Draw()
    pad1.cd()

    h1.SetStats(0)
    #h1.SetMarkerStyle(32)
    #h1.SetMarkerSize(1.5)
    h1.GetXaxis().SetRangeUser(xrange[0], xrange[1])
    h1.GetXaxis().SetLabelSize(0)
    h1.GetYaxis().SetRangeUser(0.0, 1.5* max(h0.GetMaximum(), h1.GetMaximum()))
    h1.GetYaxis().SetTitle(axis[1])
    h1.GetYaxis().SetTitleSize(0.065)
    h1.GetYaxis().SetTitleOffset(0.7)
    h1.GetYaxis().SetLabelSize(0.05)
    h1.GetYaxis().SetMaxDigits(3)
    h1c = h1.Clone("clone h1")
    h1c.Draw("same")
    h1c.SetLineWidth(2)
    h1c.SetTitle('')
    
    h0.SetMarkerStyle(20)
    h0.SetMarkerSize(0.9)
    h0.GetXaxis().SetRangeUser(xrange[0], xrange[1])
    h0c = h0.Clone("clone h0")
    h0c.Draw("same pe x0")

    # legend
    legend = ROOT.TLegend(0.12, 0.7, 0.3, 0.88)
    logger.debug(f'Labels, clones of h0 and h1: {labels}, {h0c}, {h1c}')
    legend.AddEntry(h0c, labels[0])
    legend.AddEntry(h1c, labels[1])
    legend.SetBorderSize(0)
    legend.Draw('same')

    test_chi2 = h0.Chi2Test(h1.GetPtr(), "WW CHI2/NDF")
    cmsTex=ROOT.TLatex()
    cmsTex.SetTextFont(42)
    cmsTex.SetTextSize(0.025)
    cmsTex.SetNDC()
    cmsTex.SetTextSize(0.045)
    cmsTex.DrawLatex(0.18,0.915,'#bf{CMS} #it{Preliminary}')
    cmsTex.DrawLatex(0.9 - lumi[1], 0.913, lumi[0])
    # cmsTex.DrawLatex(0.69, 0.8, 'chi2/NDF = {}'.format(round(test_chi2,3)))

    # lower pad
    c.cd()
    pad2 = ROOT.TPad("pad2", "pad2", 0,0,1,0.3)
    pad2.SetTopMargin(.035)
    pad2.SetBottomMargin(.3)
    pad2.Draw()
    pad2.cd()
    h0.SetStats(0)
    h0.Sumw2()
    h0.Divide(h1.GetPtr())
    #plots['dt'].SetMarkerStyle(20)
    h0.Draw("e")
    h0.GetXaxis().SetLabelSize(0.12)
    h0.GetXaxis().SetTickSize(0.08)
    h0.GetXaxis().SetTitleSize(0.15)
    h0.GetXaxis().SetTitleOffset(0.9)
    h0.GetXaxis().SetTitle(axis[0])

    h0.GetYaxis().SetTitleOffset(0.32)
    h0.GetYaxis().SetTitleSize(0.15)
    h0.GetYaxis().SetLabelSize(0.12)
    h0.GetYaxis().SetNdivisions(502)
    # h0.GetYaxis().SetRangeUser(ratiorange[0], ratiorange[1])
    h0.GetYaxis().SetRangeUser(0.4, 1.6)
    if '_pt' in outfile:
        h0.GetYaxis().SetRangeUser(0.8, 1.2)
    #h0.GetYaxis().SetTitle(f"{labels[0]}/{labels[1]}")
    h0.GetYaxis().SetTitle(f"ratio")

    #h.GetXaxis().SetTitleOffset(0.1)
    #h0.GetXaxis().SetTitleSize(0.03)
    h0.SetTitle("")
    line = ROOT.TLine(xrange[0], 1, xrange[1], 1)
    line.SetLineWidth(2)
    line.Draw("same")
    c.cd()
    c.SaveAs(outfile)    
    c.SaveAs(outfile.split(".pdf")[0]+".png")
    return test_chi2
