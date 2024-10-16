# Repo for XY corrections
The xy corrections are ad-hoc corrections aiming at the reduction of a phi modulation in the missing transverse momentum at the CMS experiment.
Such modulations indicate the presence of a bias in the measurement of the missing transverse momentum in one physical direction of the experiment.
Possible sources of such biases are:
- anisotropic detector response
- inactive calorimeter cells/tracking regions
- misalignment
- displacement of the beam spot
The resulting bias is observed to be roughly linear in the number of primary vertices. Consequently, the effect can be corrected without deeper understanding of the underlying reason by measuring the dependence of the mean missing transverse momentum in x or y direction on the number of primary vertices. The values are then corrected by shifting the means back to zero.

In this framework, the Z->mumu phase space property of no intrinsic missing transverse momentum is leveraged to find out the aforementioned dependence.
The correction procedure can be roughly categorized into four steps:
1. preparations
2. histograms
3. fits
4. validation

## 1. Preparations

The preparations include the steps from data and simulation files in the NANOAOD data format to flat ntuples which include only the necessary information, i.e. missing transverse momentum as well as the number of good reconstructed primary vertices, and the pileup correction.
In the framework, this step consists of three sub-steps, that are:
a) Configuration of the setup
b) Collecting the data files
c) Running the ntuple production

### a) Configuration of the setup

In the data directory, create a subdirectory with a unique name for the epoch of data under investigation.
Then create a file called `datasets.json`, which contains the DAS names of the files you would like to investigate.
Furthermore, this is the place for the json containing the pileup correction from the LUM POG. You might need to rename the name in the correctionlib file to "puweights". The golden lumi json needs to be placed in the `data/jsons` directory, with the path in `python/inputs/paths.py` adjusted correspondingly.
In order to obtain a consistent set of program version, it is advised to source an LCG stack, e.g. one of those provided in `env.sh`.

### b) Collecting the data files

Now you can run the main file using the preparation option:
`python3 get_xy_corrs.py -Y 2022 --prep`
This will query the files of the datasets in the `datasets.json` file and write the file lists into the file `nanoAODs.json`, which will be of use in the next step. You will need a valid VO CMS proxy in this step as well as the next one.

### c) Running the ntuple production

The ntuple production takes the files in `nanoAODs.json`, filters out the data events fulfilling the golden lumi json, and applies a selection to the Z->mumu phase space to both data and simulation:
`pyhton3 get_xy_corrs.py -Y 2022 -S`
The `snap_dir` path in `python/inputs/paths.py` determines the place to save the snapshots.
You will be prompted whether to produce the snapshots locally or using HTCondor.
In the first case, you can adjust the number of jobs with the additional option `-j 8` for the usage of multiprocessing with 8 threads.
In the latter case, you might have to adjust the condor submit setup in the `python/tools/condor_configurizer.py` file. The prompt for the condor file submission will be given from the logger.

Sometimes the snapshots will be corrupted, which will is checked after the production.

## 2. Histograms

The flat ntuples produced in the previous step are used to create 2d histograms of the x or y component of the missing transverse momentum against the number of reconstructed good primary vertices. These histograms are then saved to a root file determined in `python/inputs/paths.py`.
The arguments needed are:
`python3 get_xy_corrs.py -Y 2022 -H -j 8`,
where once again the option `-j 8` uses multithreading techniques, now not using the multiprocessing tool in python but rather the ROOT internal method, speeding up the histogramming process considerably.

## 3. Fits

The fits are done on the profile of the 2d histograms in direction of the momentum. In every bin of the number of primary vertices, the mean and standard deviation are calculated and then a linear fit is performed to the result:
`python3 get_xy_corrs.py -Y 2022 -C`
The results and plots of the fits are written to the directory specified in the `python/inputs/paths.py` file. 

## 4. Validation

A closure test is performed by comparing the phi modulation of the missing transverse momentum component before and after correction:
`python3 get_xy_corrs.py -Y 2022 --validate`

# Further options

The types of missing transverse momentum that are investigated can be controlled with the option `-M MET,PuppiMET`.
A version name can be given to the currently used correction via `-V v0`.
Debug output can be printed by adding `--debug`.
The correction can be performed only on data or MC with the option `--process MC,DATA`.