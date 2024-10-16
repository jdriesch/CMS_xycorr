import ROOT
import json


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


ROOT.gROOT.ProcessLine(
'''
Float_t get_trg_sf(
    Float_t eta_1, Float_t eta_2, 
    Float_t pt_1, Float_t pt_2, 
    Bool_t trg_match_1, Bool_t trg_match_2,
    TH2F trg_mc, TH2F trg_dt
){
    double sf = 1.0;  // Default scale factor
    double eff_mc_1 = trg_mc.GetBinContent(trg_mc.FindBin(abs(eta_1), pt_1));
    double eff_mc_2 = trg_mc.GetBinContent(trg_mc.FindBin(abs(eta_2), pt_2));
    double eff_dt_1 = trg_dt.GetBinContent(trg_dt.FindBin(abs(eta_1), pt_1));
    double eff_dt_2 = trg_dt.GetBinContent(trg_dt.FindBin(abs(eta_2), pt_2));

    if(trg_match_1 == 0){
        eff_mc_1 = 0;
        eff_dt_1 = 0;
    }
    if(trg_match_2 == 0){
        eff_mc_2 = 0;
        eff_dt_2 = 0;
    }

    double eff_mc = 1.0 - (1.0 - eff_mc_1) * (1.0 - eff_mc_2);
    double eff_dt = 1.0 - (1.0 - eff_dt_1) * (1.0 - eff_dt_2);

    if (eff_mc == 0) {
        // std::cout << "mc efficiency is 0 in this bin: " << pt_1 << ", " << pt_2 << ", " << eta_1 << ", " << eta_2 << std::endl;
        return 1.0;  // Return default scale factor if eff_mc is zero
    } else {
        sf = eff_dt / eff_mc;  // Calculate scale factor
        return sf;
    }
}
'''
)


ROOT.gROOT.ProcessLine(
'''
// trigger matching
UInt_t trg_match_ind(
    Float_t eta,
    Float_t phi,
    Int_t nTrigObj,
    ROOT::VecOps::RVec<UShort_t> *TrigObj_id,
    ROOT::VecOps::RVec<Float_t> *TrigObj_eta,
    ROOT::VecOps::RVec<Float_t> *TrigObj_phi,
    Int_t match1
){
    Int_t index = -99;
    Float_t dRmin = 1000;
    Float_t dR, dEta, dPhi;
    for(int i=0; i<nTrigObj; i++){
        if (TrigObj_id->at(i) != 13) continue;
        if (TrigObj_id->at(i) == match1) continue;
        dEta = eta - TrigObj_eta->at(i);
        dPhi = (phi - TrigObj_phi->at(i));
        if (dPhi > 3.1415) dPhi = 2*3.1415 - dPhi;
        dR = sqrt(dEta*dEta + dPhi*dPhi);
        if (dR > 0.1) continue;
        if (index > -1){
            if(dR < dRmin) {
                dRmin = dR;
                index = i;
            }
            else continue;
        }
        else index = i;
    }
    return index;
}
'''
)