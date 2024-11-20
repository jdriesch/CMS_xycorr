import ROOT
import json
import correctionlib.schemav2 as cs
import correctionlib
import numpy as np
import logging

logger = logging.getLogger(__name__)

correctionlib.register_pyroot_binding()

ROOT.EnableImplicitMT(24)


def build_combined_dict(mets, epochs, corr_dir, year):
    '''
    combine the correction dictionaries provided

    Args:
        mets (list): types of met
        epochs (list): different epochs to combine
        corr_dir (str): correction directory of year (year will be replaced)
        year (str): year (will be replaced)
    '''

    logger.info("Combining the dictionaries")

    comb_dict = {}
    for epoch in epochs:
        path = corr_dir.replace(year, epoch)

        comb_dict[epoch] = {}
        for dtmc in ['DATA', 'MC']:
            with open(f'{path}{dtmc}.json', 'r') as f:
                comb_dict[epoch][dtmc] = json.load(f)

    return comb_dict


def make_correction_with_formula(comb_dict, corr_dir, year):
    """
    Create a correctionlib json file with corrections.
    
    Args:
        comb_dict (dict): output dictionary from previous step
        corr_dir (str): correction directory
        year (str): year
    """

    logger.info("Setting up clib file.")

    h = 'met_xy_corrections'
    description = 'Apply MET xy corrections to PuppiMET or MET'

    # getting variations from dictionary
    epochs = list(comb_dict.keys())
    dtmc = list(comb_dict[epochs[0]].keys())
    mets = list(comb_dict[epochs[0]][dtmc[0]].keys())
    variations = {}
    for d in dtmc:
        variations[d] = list(comb_dict[epochs[0]][d][mets[0]]["_x"].keys())

    met_content = []

    # Loop over the categories to fill the correction content
    for met in mets:
        epochs_content = []
        for e in epochs:
            dtmc_content = []
            for d in dtmc:
                vrt_content = []
                logger.debug(f"Variations for {met}, {e}, {d}: {variations[d]}")

                for vrt in variations[d]:
                    params = comb_dict[e][d][met]

                    # Expression for pt correction
                    pt_x = "(x * cos(y) - ([0] * z + [1]))"
                    pt_y = "(x * sin(y) - ([2] * z + [3]))"

                    sigma_pt_x = "sqrt("\
                            f"pow({pt_x} * [4], 2) + "\
                            f"pow([5], 2) +"\
                            f"2 * {pt_x} * [4] * [5] * [6])"
                    sigma_pt_y = "sqrt("\
                            f"pow({pt_y} * [7], 2) + "\
                            f"pow([8], 2) +"\
                            f"2 * {pt_y} * [7] * [8] * [9])"

                    pt_x_up = f"{pt_x} + {sigma_pt_x}"
                    pt_x_dn = f"{pt_x} - {sigma_pt_x}"

                    pt_y_up = f"{pt_y} + {sigma_pt_y}"
                    pt_y_dn = f"{pt_y} - {sigma_pt_y}"

                    pt_expression = (f"sqrt(pow({pt_x},2) + pow({pt_y},2))")
                    phi_expression = (f"atan2({pt_y}, {pt_x})")

                    pt_expression_xup = (f"sqrt(pow({pt_x_up},2) + pow({pt_y},2))")
                    phi_expression_xup = (f"atan2({pt_y}, {pt_x_up})")
                    pt_expression_xdn = (f"sqrt(pow({pt_x_dn},2) + pow({pt_y},2))")
                    phi_expression_xdn = (f"atan2({pt_y}, {pt_x_dn})")

                    pt_expression_yup = (f"sqrt(pow({pt_x},2) + pow({pt_y_up},2))")
                    phi_expression_yup = (f"atan2({pt_y_up}, {pt_x})")
                    pt_expression_ydn = (f"sqrt(pow({pt_x},2) + pow({pt_y_dn},2))")
                    phi_expression_ydn = (f"atan2({pt_y_dn}, {pt_x})")


                    expressions = {
                        "pt": pt_expression,
                        "phi": phi_expression,
                        "pt_stat_xup": pt_expression_xup,
                        "pt_stat_xdn": pt_expression_xdn,
                        "pt_stat_yup": pt_expression_yup,
                        "pt_stat_ydn": pt_expression_ydn,
                        "phi_stat_xup": phi_expression_xup,
                        "phi_stat_xdn": phi_expression_xdn,
                        "phi_stat_yup": phi_expression_yup,
                        "phi_stat_ydn": phi_expression_ydn,
                    }

                    content = []

                    for exp in expressions:
                        formula = cs.Formula(
                            nodetype="formula",
                            expression=expressions[exp],
                            parameters=[
                                params["_x"][vrt]["m"],
                                params["_x"][vrt]["c"],
                                params["_y"][vrt]["m"],
                                params["_y"][vrt]["c"],
                                params["_x"][vrt]["m_stat"],
                                params["_x"][vrt]["c_stat"],
                                params["_x"][vrt]["correlation"],
                                params["_y"][vrt]["m_stat"],
                                params["_y"][vrt]["c_stat"],
                                params["_y"][vrt]["correlation"]
                            ],
                            parser='TFormula',
                            variables=["met_pt", "met_phi", "npvGood"],
                        )

                        content.append({"key": exp, "value": formula})

                    # Append the variation content with both formulas
                    vrt_content.append(
                        {
                            "key": vrt,
                            "value": cs.Category(
                                nodetype="category",
                                input='pt_phi',
                                content=content
                            )
                        }
                    )


                # Build the dtmc content with the variation category
                dtmc_content.append(
                    {"key": d, "value": cs.Category(
                        nodetype="category",
                        input='variation',
                        content=vrt_content
                    )}
                )

            # Build the epoch content
            epochs_content.append(
                {"key": e, "value": cs.Category(
                    nodetype="category",
                    input='dtmc',
                    content=dtmc_content
                )}
            )

        # Build the MET type content
        met_content.append(
            {"key": met, "value": cs.Category(
                nodetype="category",
                input='epoch',
                content=epochs_content
            )}
        )

    # Define the correction using correctionlib schema
    correction = cs.Correction(
        name=h,
        description=description,
        version=1,
        inputs=[
            cs.Variable(name='pt_phi', type='string'),     # MET type (MET or PuppiMET)
            cs.Variable(name='met_type', type='string'),     # MET type (MET or PuppiMET)
            cs.Variable(name='epoch', type='string'),    # Epoch (2022 or 2022EE)
            cs.Variable(name='dtmc', type='string'),     # DATA or MC
            cs.Variable(name='variation', type='string'), # Variation (nom, puup, etc.)
            cs.Variable(name='met_pt', type='real'),     # met_pt (x)
            cs.Variable(name='met_phi', type='real'),    # met_phi (y)
            cs.Variable(name='npvGood', type='real')     # npvGood (z)
        ],
        output=cs.Variable(name='pt_corr', type='real'), # Corrected pt
        data=cs.Category(
            nodetype="category",
            input='met_type',
            content=met_content
        )
    )

    cset = cs.CorrectionSet(
        schema_version=2,
        corrections=[correction],
        description="Description"
    )

    path = corr_dir. replace(f'{year}/', 'schemaV2')

    for epoch in epochs:
        path += f'_{epoch}'
    
    path += '.json'

    with open(path, 'w') as fout:
        fout.write(cset.json(exclude_unset=True, indent=4))

    logger.info(f'Saved clib file in {path}')

    return


def validate_json():
    dtmc = 'MC'
    rdf = ROOT.RDataFrame("Events", f'/ceph/jdriesch/CMS_xycorr/snapshots/v0/2022/{dtmc}/*.root')

    ROOT.gROOT.ProcessLine(
        'auto cs_pu = correction::CorrectionSet::from_file("results/corrections/v0/schemaV2_2022_2022EE.json")->at("met_xy_corrections");'
    )

    rdf = rdf.Define('met_phi', 'atan2(MET_y, MET_x)')
    rdf = rdf.Define('met_pt', 'sqrt(MET_y*MET_y + MET_x*MET_x)')

    rdf = rdf.Define('met_phi_corr', 'cs_pu->evaluate({"phi", "MET", "2022","'+dtmc+'", "nom", met_pt, met_phi, static_cast<float>(PV_npvsGood)})')
    rdf = rdf.Define('met_phi_corr_xup', 'cs_pu->evaluate({"phi_stat_xup", "MET", "2022", "'+dtmc+'", "nom", met_pt, met_phi, static_cast<float>(PV_npvsGood)})')
    rdf = rdf.Define('met_phi_corr_xdn', 'cs_pu->evaluate({"phi_stat_xdn", "MET", "2022", "'+dtmc+'", "nom", met_pt, met_phi, static_cast<float>(PV_npvsGood)})')
    rdf = rdf.Define('met_phi_corr_yup', 'cs_pu->evaluate({"phi_stat_yup", "MET", "2022", "'+dtmc+'", "nom", met_pt, met_phi, static_cast<float>(PV_npvsGood)})')
    rdf = rdf.Define('met_phi_corr_ydn', 'cs_pu->evaluate({"phi_stat_ydn", "MET", "2022", "'+dtmc+'", "nom", met_pt, met_phi, static_cast<float>(PV_npvsGood)})')

    rdf = rdf.Define('met_phi_corr_puup', 'cs_pu->evaluate({"phi", "MET", "2022", "'+dtmc+'", "pu_up", met_pt, met_phi, static_cast<float>(PV_npvsGood)})')
    rdf = rdf.Define('met_phi_corr_pudn', 'cs_pu->evaluate({"phi", "MET", "2022", "'+dtmc+'", "pu_dn", met_pt, met_phi, static_cast<float>(PV_npvsGood)})')

    hists = []
    for hn in ["phi", "phi_corr", "phi_corr_xup", "phi_corr_xdn", "phi_corr_yup", "phi_corr_ydn", "phi_corr_puup", "phi_corr_pudn"]:
        hists.append(rdf.Histo1D((hn, "", 30, -3.14, 3.14), f'met_{hn}'))

    f = ROOT.TFile(f'test_{dtmc}.root', 'recreate')
    for h in hists:
        h.Write()
    f.Close()

    return


if __name__=='__main__':

    comb_dict = build_combined_dict(
        ['MET', 'PuppiMET'],
        ['2022', '2022EE']
    )
    
    make_correction_with_formula(comb_dict, ['MET', 'PuppiMET'], ['2022', '2022EE'])

    cset = correctionlib.CorrectionSet.from_file("schemaV2.json")

    print(cset.get("met_xy_corrections").evaluate('pt', 'MET', '2022', 'DATA', 'nom', 50., 1.1, 40.))
    print(cset.get("met_xy_corrections").evaluate('pt', 'MET', '2022', 'MC', 'nom', 50., 1.11, 25.))

    validate_json()
