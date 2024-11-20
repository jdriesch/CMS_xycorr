import ROOT
import json


def filter_lumi(rdf, g_json):
    """
    function to get rdf with events filtered with golden json
    
    rdf (ROOT.RDataFrame) : RDataFrame with recorded data
    g_json (str): path to golden json
    """

    # load content of golden json
    with open(g_json) as cf:
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

    rdf = rdf.Filter("isGolden==1")

    return rdf


ROOT.gROOT.ProcessLine(
'''
ROOT::VecOps::RVec<Int_t> get_indices(
    UInt_t nMuon,
    ROOT::VecOps::RVec<Float_t> *Muon_pt,
    ROOT::VecOps::RVec<Float_t> *Muon_eta,
    ROOT::VecOps::RVec<Float_t> *Muon_phi,
    ROOT::VecOps::RVec<Float_t> *Muon_mass,
    ROOT::VecOps::RVec<UChar_t> *Muon_pfIsoId,
    ROOT::VecOps::RVec<Bool_t> *Muon_Id,
    ROOT::VecOps::RVec<Int_t> *Muon_charge,
    Float_t pt_min, Float_t mass,
    Float_t delta_mass,
    Int_t pfIsoId_min
    ){
    Int_t ind1, ind2;
    ind1 = -99;
    ind2 = -99;
    for(int i=0; i<nMuon; i++){
        if (Muon_pt->at(i) < pt_min) continue;
        if(fabs(Muon_eta->at(i)) > 2.4) continue;
        if(Muon_pfIsoId->at(i) < 4) continue; // tight wp
        if(Muon_Id->at(i) == 0) continue;

        for(int j=i; j<nMuon; j++){
            if (Muon_pt->at(j) < pt_min) continue;
            if(fabs(Muon_eta->at(j)) > 2.4) continue;
            if(Muon_pfIsoId->at(j) < pfIsoId_min) continue;
            if(Muon_Id->at(j) == 0) continue;
            if(Muon_charge->at(i) * Muon_charge->at(j) > 0) continue;
            Float_t dEta = Muon_eta->at(i) - Muon_eta->at(j);
            Float_t dPhi = Muon_phi->at(i) - Muon_phi->at(j);
            Float_t dR = sqrt(dEta*dEta + dPhi*dPhi);
            if (dR < 0.3) continue;

            TLorentzVector mui, muj, pair;
            mui.SetPtEtaPhiM(
                Muon_pt->at(i),
                Muon_eta->at(i),
                Muon_phi->at(i),
                Muon_mass->at(i)
            );
            muj.SetPtEtaPhiM(
                Muon_pt->at(j),
                Muon_eta->at(j),
                Muon_phi->at(j),
                Muon_mass->at(j)
            );
            pair = mui + muj;
            if (fabs(pair.M() - mass) < delta_mass){
                delta_mass = fabs(pair.M() - mass);
                if (Muon_charge->at(i) < 0){
                    ind1 = i;
                    ind2 = j;
                }
                else {
                    ind1 = j;
                    ind2 = i;
                }
            }
        }
    }

    ROOT::VecOps::RVec<Int_t> s(2);
    s[0] = ind1;
    s[1] = ind2;
    return s;
}
'''
)


def filter_zmm(rdf):
    """
    function to get rdf with events filtered for Z->mumu
    
    rdf (ROOT.RDataFrame) : RDataFrame with recorded data
    """

    # isomu24 trigger
    rdf = rdf.Filter("HLT_IsoMu24")

    rdf = rdf.Define(
        "ind",
        f"""ROOT::VecOps::RVec<Int_t> (get_indices(
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
            ))"""
    )
    rdf = rdf.Define("ind0", "ind[0]")
    rdf = rdf.Define("ind1", "ind[1]")
    rdf = rdf.Filter("ind0 + ind1 > 0")
    rdf = rdf.Define("pt_1", "Muon_pt[ind[0]]")
    rdf = rdf.Define("pt_2", "Muon_pt[ind[1]]")
    rdf = rdf.Define("eta_1", "Muon_eta[ind[0]]")
    rdf = rdf.Define("eta_2", "Muon_eta[ind[1]]")
    rdf = rdf.Define("phi_1", "Muon_phi[ind[0]]")
    rdf = rdf.Define("phi_2", "Muon_phi[ind[1]]")

    rdf = rdf.Define("mass_Z", "sqrt(2 * pt_1 * pt_2 * (cosh(eta_1 - eta_2) - cos(phi_1 - phi_2)))")

    return rdf