import ROOT
import json
import correctionlib.schemav2 as cs
import correctionlib
import numpy as np
import logging

logger = logging.getLogger(__name__)

correctionlib.register_pyroot_binding()

ROOT.EnableImplicitMT(24)


def make_correction_with_formula(corr_dir, year, datamc, mets):
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

    # Loop over the categories to fill the correction content
    dtmc_content = []
    for dtmc in datamc:

        with open(f'{corr_dir}{dtmc}.json', 'r') as f:
            tmp_dict = json.load(f)

        met_content = []
        for met in mets:
            params = tmp_dict[met]

            vrt_content = []
            variations = list(params["_x"].keys())
            logger.debug(f"Variations for {met} {dtmc}: {variations}")

            for vrt in variations:

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

            # Build the epoch content
            met_content.append(
                {"key": met, "value": cs.Category(
                    nodetype="category",
                    input='variation',
                    content=vrt_content
                )}
            )

        # Build the dtmc content with the variation category
        dtmc_content.append(
            {"key": dtmc, "value": cs.Category(
                nodetype="category",
                input='met_type',
                content=met_content
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
            cs.Variable(name='dtmc', type='string'),     # DATA or MC
            cs.Variable(name='variation', type='string'), # Variation (nom, puup, etc.)
            cs.Variable(name='met_pt', type='real'),     # met_pt (x)
            cs.Variable(name='met_phi', type='real'),    # met_phi (y)
            cs.Variable(name='npvGood', type='real')     # npvGood (z)
        ],
        output=cs.Variable(name='pt_corr', type='real'), # Corrected pt
        data=cs.Category(
            nodetype="category",
            input='dtmc',
            content=dtmc_content
        )
    )

    cset = cs.CorrectionSet(
        schema_version=2,
        corrections=[correction],
        description="Description"
    )

    path = corr_dir.replace(f'{year}/', f'schemaV2_{year}.json')

    with open(path, 'w') as fout:
        fout.write(cset.json(exclude_unset=True, indent=4))

    logger.info(f'Saved clib file in {path}')

    return


def validate_json(snap_dir, corr_dir, hist_dir, datamc, year):
    # validate if the json produces results
    for dtmc in datamc:
        
        rdf = ROOT.RDataFrame("Events", f"{snap_dir}{dtmc}/file_*.root")

        schemav2_json = corr_dir.replace(f'{year}/', f'schemaV2_{year}.json')

        ROOT.gROOT.ProcessLine(
            f'auto cs_pu = correction::CorrectionSet::from_file("{schemav2_json}")->at("met_xy_corrections");'
        )

        rdf = rdf.Define('met_phi', 'atan2(MET_y, MET_x)')
        rdf = rdf.Define('met_pt', 'sqrt(MET_y*MET_y + MET_x*MET_x)')

        rdf = rdf.Define('met_phi_corr', 'cs_pu->evaluate({"phi", "MET", "'+dtmc+'", "nom", met_pt, met_phi, static_cast<float>(PV_npvsGood)})')
        rdf = rdf.Define('met_phi_corr_xup', 'cs_pu->evaluate({"phi_stat_xup", "MET", "'+dtmc+'", "nom", met_pt, met_phi, static_cast<float>(PV_npvsGood)})')
        rdf = rdf.Define('met_phi_corr_xdn', 'cs_pu->evaluate({"phi_stat_xdn", "MET", "'+dtmc+'", "nom", met_pt, met_phi, static_cast<float>(PV_npvsGood)})')
        rdf = rdf.Define('met_phi_corr_yup', 'cs_pu->evaluate({"phi_stat_yup", "MET", "'+dtmc+'", "nom", met_pt, met_phi, static_cast<float>(PV_npvsGood)})')
        rdf = rdf.Define('met_phi_corr_ydn', 'cs_pu->evaluate({"phi_stat_ydn", "MET", "'+dtmc+'", "nom", met_pt, met_phi, static_cast<float>(PV_npvsGood)})')

        if dtmc=='MC':
            rdf = rdf.Define('met_phi_corr_puup', 'cs_pu->evaluate({"phi", "MET", "'+dtmc+'", "pu_up", met_pt, met_phi, static_cast<float>(PV_npvsGood)})')
            rdf = rdf.Define('met_phi_corr_pudn', 'cs_pu->evaluate({"phi", "MET", "'+dtmc+'", "pu_dn", met_pt, met_phi, static_cast<float>(PV_npvsGood)})')

        hists = []
        vars = ["phi", "phi_corr", "phi_corr_xup", "phi_corr_xdn", "phi_corr_yup", "phi_corr_ydn"]
        if dtmc=='MC':
            vars += ["phi_corr_puup", "phi_corr_pudn"]
        for hn in vars:
            hists.append(rdf.Histo1D((hn, "", 30, -3.14, 3.14), f'met_{hn}'))

        f = ROOT.TFile(f'{hist_dir}validation_{dtmc}.root', 'recreate')
        for h in hists:
            h.Write()
        f.Close()

    return