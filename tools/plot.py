import ROOT
import os


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
        results = ["", ""]
    ):
    c = ROOT.TCanvas("c", title, 800, 600)
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

    c.SetRightMargin(0.12)
    ROOT.TGaxis.SetMaxDigits(3)

    h.Draw(drawoption)
    h.SetTitle(title)

    cmsTex=ROOT.TLatex()
    cmsTex.SetTextFont(42)
    cmsTex.SetTextSize(0.025)
    cmsTex.SetNDC()
    cmsTex.SetTextSize(0.035)
    cmsTex.DrawLatex(0.11,0.915,'#bf{CMS} #it{Preliminary}')
    cmsTex.DrawLatex(0.75, 0.915, lumi)

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
        lumi = '5.05 fb^{-1} (2022, 13.6 TeV)'
    ):
    c = ROOT.TCanvas("c", title, 800, 700)
    ROOT.gROOT.SetBatch(1)

    # Split canvas
    pad1 = ROOT.TPad("pad1", "pad1", 0,0.3,1,1)
    pad1.SetBottomMargin(0)

    # Upper pad
    pad1.Draw()
    pad1.cd()

    h1.SetStats(0)
    #h1.SetMarkerStyle(32)
    #h1.SetMarkerSize(1.5)
    h1.GetXaxis().SetRangeUser(xrange[0], xrange[1])
    h1.GetYaxis().SetRangeUser(0.0, 1.5* max(h0.GetMaximum(), h1.GetMaximum()))
    h1.GetYaxis().SetTitle(axis[1])
    h1.Draw("same")
    h1.SetLineWidth(2)
    h1.SetTitle(title)
    
    h0.SetMarkerStyle(20)
    h0.SetMarkerSize(0.9)
    h0.GetXaxis().SetRangeUser(xrange[0], xrange[1])
    h0.DrawCopy("same pe x0")

    # legend
    legend = ROOT.TLegend(0.12, 0.7, 0.3, 0.88)
    legend.AddEntry(h0.GetName(), labels[0], "PE X0")
    legend.AddEntry(h1.GetName(), labels[1], "LE")
    legend.SetBorderSize(0)
    legend.Draw('same')

    test_chi2 = h0.Chi2Test(h1.GetPtr(), "WW CHI2/NDF")
    cmsTex=ROOT.TLatex()
    cmsTex.SetTextFont(42)
    cmsTex.SetTextSize(0.025)
    cmsTex.SetNDC()
    cmsTex.SetTextSize(0.035)
    cmsTex.DrawLatex(0.15,0.913,'#bf{CMS} #it{Preliminary}')
    cmsTex.DrawLatex(0.77, 0.913, lumi)
    cmsTex.DrawLatex(0.69, 0.8, 'chi2/NDF = {}'.format(round(test_chi2,3)))

    # lower pad
    c.cd()
    pad2 = ROOT.TPad("pad2", "pad2", 0,0,1,0.3)
    pad2.SetTopMargin(.03)
    pad2.SetBottomMargin(.3)
    pad2.Draw()
    pad2.cd()
    h0.SetStats(0)
    h0.Sumw2()
    h0.Divide(h1.GetPtr())
    #plots['dt'].SetMarkerStyle(20)
    h0.Draw("e")
    h0.GetXaxis().SetLabelSize(0.1)
    h0.GetXaxis().SetTitleSize(0.1)
    h0.GetXaxis().SetTitleOffset(1)
    h0.GetXaxis().SetTitle(axis[0])

    h0.GetYaxis().SetTitleOffset(0.5)
    h0.GetYaxis().SetTitleSize(0.07)
    h0.GetYaxis().SetLabelSize(0.07)
    # h0.GetYaxis().SetRangeUser(ratiorange[0], ratiorange[1])
    h0.GetYaxis().SetRangeUser(1-1.1*(1-h0.GetMinimum()), 1+1.1*(h0.GetMaximum()-1))
    h0.GetYaxis().SetTitle(f"{labels[0]}/{labels[1]}")

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
