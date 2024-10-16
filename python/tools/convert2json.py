import ROOT
import json
import correctionlib.schemav2 as cs
import numpy as np

def get_histograms(path):
    hists = {}
    tf_resol = ROOT.TFile(path+'step2_fitresults.root', 'read')
    tf_scale = ROOT.TFile(path+'step3_correction.root', 'read')
    tf_resol_k = ROOT.TFile(path+'step4_k.root', 'read')

    hists['cb_params'] = {
        "hist": tf_resol.Get("h_results_cb"),
        "description": "Parameters of the Crystal Ball function for the resolution smearing"
    }
    hists['poly_params'] = {
        "hist": tf_resol.Get("h_results_poly"),
        "description": "Parameters of the 2nd order polynomial for the resolution smearing"
    }
    hists['m_data'] = {
        "hist": tf_scale.Get("M_DATA"),
        "description": "Multiplicative part of data scale correction"
    }
    hists['a_data'] = {
        "hist": tf_scale.Get("A_DATA"),
        "description": "Additive part of data scale correction"
    }
    hists['m_mc'] = {
        "hist": tf_scale.Get("M_SIG"),
        "description": "Multiplicative part of MC scale correction"
    }
    hists['a_mc'] = {
        "hist": tf_scale.Get("A_SIG"),
        "description": "Additive part of MC scale correction"
    }
    hists['k_data'] = {
        "hist": tf_resol_k.Get("k_hist_DATA").ProjectionX("k_hist_data", 3, 3),
        "description": "Additional resolution smearing to match data"
    }
    hists['k_mc'] = {
        "hist": tf_resol_k.Get("k_hist_SIG").ProjectionX("k_hist_mc", 3, 3),
        "description": "Additional resolution smearing to match MC"
    }

    for h in hists:
        hists[h]["hist"].SetDirectory(ROOT.nullptr)

    tf_resol.Close()
    tf_scale.Close()
    tf_resol_k.Close()
    return hists


def get_unc_hists(path):
    tf = ROOT.TFile(path, 'read')
    hists = {}
    hists['m_data'] = tf.Get('M_DATA3_all_pyx')
    hists['a_data'] = tf.Get('A_DATA3_all_pyx')
    hists['a_mc'] = tf.Get('A_SIG3_all_pyx')
    hists['m_mc'] = tf.Get('M_SIG3_all_pyx')
    hists['k_data'] = tf.Get('k_all_DATA_pfx')
    hists['k_mc'] = tf.Get('k_all_SIG_pfx')

    for h in hists:
        hists[h].SetDirectory(ROOT.nullptr)

    return hists


def convert_th1(hist):
    xbins = []
    entries = []
    uncs = []

    xaxis = hist.GetXaxis()

    for i in range(xaxis.GetNbins()+1):
        xbins.append(xaxis.GetXbins().At(i))

        if i==0:
            continue
        else:
            entries.append(hist.GetBinContent(i))
            uncs.append(hist.GetBinError(i))

    xbins = [round(x, 2) for x in xbins]
    entries = [round(e, 6) for e in entries]

    return xbins, entries, uncs


def convert_th2(hist):
    xbins, ybins = [], []
    entries = []
    uncs = []

    xaxis = hist.GetXaxis()
    yaxis = hist.GetYaxis()

    for x in range(xaxis.GetNbins()+1):
        xbins.append(xaxis.GetXbins().At(x))

    for y in range(yaxis.GetNbins()+1):
        ybins.append(yaxis.GetXbins().At(y))

    for x in range(len(xbins)-1):
        entries.append([])
        uncs.append([])
        for y in range(len(ybins)-1):
            entries[-1].append(hist.GetBinContent(x+1, y+1))
            uncs[-1].append(hist.GetBinError(x+1, y+1))

    xbins = [round(x, 2) for x in xbins]
    ybins = [round(y, 2) for y in ybins]

    print(xbins, ybins, entries, hist)


    return xbins, ybins, entries, uncs


def convert_th3(hist):
    xbins, ybins, zbins = [], [], []
    entries = []

    xaxis = hist.GetXaxis()
    yaxis = hist.GetYaxis()
    zaxis = hist.GetZaxis()

    for x in range(xaxis.GetNbins()+1):
        xbins.append(xaxis.GetXbins().At(x))

    for y in range(yaxis.GetNbins()+1):
        ybins.append(yaxis.GetXbins().At(y))

    ybins[0] = 0
    ybins[-1] = 100

    for z in range(zaxis.GetNbins()):
        zbins.append(zaxis.GetXbins().At(z))

    for x in range(len(xbins)-1):
        entries.append([])
        for y in range(len(ybins)-1):
            entries[-1].append([])
            for z in range(len(zbins)):
                # print(entries)
                entries[-1][-1].append(hist.GetBinContent(x+1, y+1, z+1))

    xbins = [round(x, 2) for x in xbins]

    return xbins, ybins, zbins, entries
                               

hdir = '../hists/2022EE_nlo/'     
hists = get_histograms(hdir)
uncs = {
    "step3": get_unc_hists(hdir+'systs/bin_step3.root'),
    "step4": get_unc_hists(hdir+'systs/bin_step4.root'),
    "stat": get_unc_hists(hdir+'systs/stat.root'),
}
corrections = []

# for h in subset:
for h in hists:
    print(h)
    histo = hists[h]["hist"]
    description = hists[h]["description"]
    dim = histo.GetDimension()

    if dim==1:
        xbins, entries, _ = convert_th1(histo)
        _, _, syst = convert_th1(uncs["step4"][h])
        _, _, stat = convert_th1(uncs["stat"][h])

        content = []
        for x_bin_idx in range(len(entries)):
            content.append(cs.Category(
                nodetype='category',
                input='variation',
                content=[
                    {"key": "nom", "value": entries[x_bin_idx]},
                    {"key": "syst", "value": syst[x_bin_idx]},
                    {"key": "stat", "value": stat[x_bin_idx]}
                ]
            ))

        correction = cs.Correction(
            name=h,
            description=description,
            version=1,
            inputs=[
                cs.Variable(name='abseta', type='real'),
                cs.Variable(name='variation', type='string')
            ],
            output=cs.Variable(name='k', type='real'),
            data=cs.Binning(
                nodetype="binning",
                input='abseta',
                edges=xbins,
                content=content,
                flow='clamp'
            )
        )
    elif dim==2:
        xbins, ybins, entries, _ = convert_th2(histo)
        _, _, _, syst = convert_th2(uncs["step3"][h])
        _, _, _, stat = convert_th2(uncs["stat"][h])

        if h == 'a_mc':
            print(entries)
            print(syst)
            print(stat)

        x_binnings = []

        # Create the binning structure for each pt bin
        for x_bin_idx in range(len(xbins)-1):

            content = []
            for y_bin_idx in range(len(entries[x_bin_idx])):

                content.append(cs.Category(
                    nodetype='category',
                    input='variation',
                    content=[
                        {"key": "nom", "value": entries[x_bin_idx][y_bin_idx]},
                        {"key": "syst", "value": syst[x_bin_idx][y_bin_idx]},
                        {"key": "stat", "value": stat[x_bin_idx][y_bin_idx]}
                    ]
                ))

            x_binning = cs.Binning(
                nodetype="binning",
                input='phi',
                edges=ybins,
                content=content,
                flow='clamp'
            )
            x_binnings.append(x_binning)

        # Define the correction object
        correction = cs.Correction(
            name=h,
            description=description,
            version=1,
            inputs=[
                cs.Variable(name='eta', type='real'),
                cs.Variable(name='phi', type='real'),
                cs.Variable(name='variation', type='string')
            ],
            output=cs.Variable(name='correction', type='real'),
            data=cs.Binning(
                nodetype="binning",
                input='eta',
                edges=xbins,
                content=x_binnings,
                flow='clamp'
            )
        )

    elif dim==3:
        xbins, ybins, zbins, entries = convert_th3(histo)

        x_binnings = []
        # Create the binning structure for each pt bin
        for x_bin_idx in range(len(xbins)-1):
    
            y_binnings = []
            entries_y = entries[x_bin_idx]

            for y_bin_idx in range(len(ybins)-1):
                
                entries_z = []

                for z_bin_idx in range(len(zbins)):
                    entries_z.append({"key": z_bin_idx, "value": entries_y[y_bin_idx][z_bin_idx]})

                y_binning = cs.Category(
                    nodetype="category",
                    input='parameter',
                    content=entries_z,
                )

                y_binnings.append(y_binning)
            
            x_binning = cs.Binning(
                nodetype="binning",
                input='nTrackerLayers',
                edges=ybins,
                content=y_binnings,
                flow='clamp'
            )
            x_binnings.append(x_binning)

        # Define the correction object
        correction = cs.Correction(
            name=h,
            description=description,
            version=1,
            inputs=[
                cs.Variable(name='abseta', type='real'),
                cs.Variable(name='nTrackerLayers', type='real'),
                cs.Variable(name='parameter', type='int')
            ],
            output=cs.Variable(name='correction', type='real'),
            data=cs.Binning(
                nodetype="binning",
                input='abseta',
                edges=xbins,
                content=x_binnings,
                flow='clamp'
            )
        )

    else:
        print("Something is wrong, check dimension of histogram")

    corrections.append(correction)
    # print(correction)

cset = cs.CorrectionSet(
    schema_version=2,
    corrections=corrections,
    description="Parameters for muon scale/resolution correction"
)

with open(f'{hdir}schemaV2.json', 'w') as fout:
    fout.write(cset.json(exclude_unset=True, indent=4))