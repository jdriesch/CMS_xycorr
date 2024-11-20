import json
import os
import sys
import glob
import logging

logger = logging.getLogger(__name__)


def get_files_from_das(datasets, nanoAODs, year):
    '''
    make file lists from DAS identifiers in datasets.json

    Args:
    datasets (str): location of datasets.json
    '''

    logger.info("Starting das queries.")

    if not os.path.exists(datasets):
        logger.critical(f"Path {datasets} does not exist.")

    else:
        with open(datasets) as f:
            dsets = json.load(f)[year]

        # using general redirector
        lib = "root://cms-xrd-global.cern.ch//"

        fdict = {}

        # looping through datasets (DATA, MC)
        for k in dsets.keys():
            fdict[k] = []

            # loop through sub datasets
            for d in dsets[k]["names"]:
                logger.debug(f'dasgoclient -query="file dataset={d}"')
                stream = os.popen(
                    f'dasgoclient -query="file dataset={d}"'
                )
                fdict[k] += [
                    lib+s.replace('\n', '') for s in stream.readlines()
                ]

        with open(nanoAODs, "w") as f:
            json.dump(fdict, f, indent=4)

    logger.info(f"File lists saved in {nanoAODs}")

    return


if __name__=='__main__':
    datasets = sys.argv[1]
    get_files_from_das(datasets)
