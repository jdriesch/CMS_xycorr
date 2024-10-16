import json
import os
import sys
import glob
import logging

logger = logging.getLogger(__name__)


def get_files_from_das(datasets):

    logger.info("Starting das queries.")

    if not os.path.exists(datasets):
        logger.critical(f"Path {datasets} does not exist. Please make sure to call the script\
            from the parent directory and provide the path to the datasets from\
            the same directory as well.")

    else:
        with open(datasets) as f:
            dsets = json.load(f)

        lib = "root://cms-xrd-global.cern.ch//"
        fdict = {}

        for k in dsets.keys():
            fdict[k] = []
            for d in dsets[k]["names"]:
                if 'ceph' in d:
                    fdict[k] += glob.glob(d)
                    logger.debug(d)
                else:
                    logger.debug(f'dasgoclient -query="file dataset={d}"')
                    stream = os.popen(f'dasgoclient -query="file dataset={d}"')
                    fdict[k] += [
                        lib+s.replace('\n', '') for s in stream.readlines()
                    ]

        nanoaod_path = datasets.replace("datasets", 'nanoAODs')

        with open(nanoaod_path, "w") as f:
            json.dump(fdict, f, indent=4)

    logger.info(f"File lists saved in {nanoaod_path}")

    return


if __name__=='__main__':
    datasets = sys.argv[1]
    get_files_from_das(datasets)
