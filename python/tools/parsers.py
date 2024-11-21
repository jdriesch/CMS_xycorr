from argparse import ArgumentParser

def parse_arguments():
    parser = ArgumentParser(
        description=
            "Derivation script for MET xy correction. \n"
            "For standard use : python get_xy_corrs.py --prep -S -H -C --validate -Y 2022 -j 8"
    )
    parser.add_argument(
        "-H", 
        "--hists", 
        action='store_true', 
        default=False,
        help='set to make 2d met vs npv histograms'
        )
    parser.add_argument(
        "-C", 
        "--corr", 
        action='store_true', 
        default=False,
        help='set to get XY corrections'
        )
    parser.add_argument(
        "-Y", 
        "--year", 
        help="Year / epoch to be run over (needs to be defined in ./data/)", 
        default='2022_Summer22'
        )
    parser.add_argument(
        "-S", 
        "--snapshot", 
        action='store_true', 
        default=False, 
        help="set if snapshot of data should be saved (for validation)"
        )
    parser.add_argument(
        "-M",
        "--met",
        help="Comma-separated list of MET types; default is 'MET,PuppiMET'",
        default='MET,PuppiMET'
    )
    parser.add_argument(
        "-V",
        "--version",
        help="Version string; default is v0",
        default='v0'
    )
    parser.add_argument(
        "-D",
        "--debug",
        help="Print debugging output",
        default=False,
        action='store_true'
    )
    parser.add_argument(
        "--prep",
        help="Do preparation, i.e. query files from DAS",
        default=False,
        action='store_true'
    )
    parser.add_argument(
        "--validate",
        help="Do validation, i.e. closure plots",
        default=False,
        action='store_true'
    )
    parser.add_argument(
        "--jobs",
        "-j",
        help='Number of jobs for parallel processing',
        default=0,
        type=int
    )
    parser.add_argument(
        "--condor",
        help='Indicating job number. -1 is default and does everything locally.',
        default=-1,
        type=int
    )
    parser.add_argument(
        "--processes",
        help="Comma separated list of what shall be processes. Default is 'DATA,MC'",
        default='DATA,MC',
        type=str
    )
    parser.add_argument(
        "--convert",
        help="Comma separated list of years to combine and convert",
        default='',
        type=str
    )

    args = parser.parse_args()

    return args