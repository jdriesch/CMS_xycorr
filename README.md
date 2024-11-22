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
4. conversion to json scheme
5. validation

## 1. Preparations

The preparations include the steps from data and simulation files in the NANOAOD data format to flat ntuples which include only the necessary information, i.e. missing transverse momentum as well as the number of good reconstructed primary vertices, and the pileup correction.
In the framework, this step consists of three sub-steps, that are:
a) Configuration of the setup
b) Collecting the data files
c) Running the ntuple production

### a) Configuration of the setup

Running `. env.sh` ensures a consistent set of program versions is used. Furthermore it will check the availability of a VOMS proxy and copy it to a certain location in order to use it in HTCondor. It will also clone the latest version of the jsonpog correctionlib database in order to have the pileup weights available. Once the jsonpog repo is available, newer versions are not pulled automatically. Please make sure to do it yourself occasionally.
In the `inputs/config` directory, you can add new eras. Please be sure to use a consistent nomenclature and add all necessary information, i.e. datasets, golden json, and labels.

### b) Collecting the data files

Now you can run the main file using the preparation option:

`python3 get_xy_corrs.py -Y 2022_Summer22 --prep`

This will query the files of the datasets in the `inputs/config/datasets.json` file and write the file lists to `inputs/nanoAODs/{year}.json`, which will be of use in the next step.

### c) Running the ntuple production

The ntuple production takes the files in `inputs/nanoAODs/{year}.json`, filters out the data events fulfilling the golden lumi json, and applies a selection to the Z->mumu phase space to both data and simulation. The standard version will construct condor jobs and print how to start the jobs. You can also run locally by providing the option `-j 8` for 8 parallel processes:

`pyhton3 get_xy_corrs.py -Y 2022_Summer22 -S`

The snapshots are automatically saved in your EOS userspace. You can change that in the corresponding entry in `inputs/config/paths.py`.
Often the snapshots will be corrupted or not contain any events. Therefore, an automatic check is performed when running the same again. You will be prompted whether you wish to delete the corrupted files. The statistics for the calculation should suffice even if many files are corrupted. If all files are broken, you can check the logs in `results/condor/{version}/{year}/{dtmc}/logs/`.

## 2. Histograms

The flat ntuples produced in the previous step are used to create 2d histograms of the x or y component of the missing transverse momentum against the number of reconstructed good primary vertices. These histograms are then saved to a root directory determined in `inputs/config/paths.py`.
The arguments needed are:

`python3 get_xy_corrs.py -Y 2022_Summer22 -H -j 8`,

where once again the option `-j 8` uses multithreading techniques, now not using the multiprocessing tool in python but rather the ROOT internal method, speeding up the histogramming process considerably.

## 3. Fits

The fits are done on the profile of the 2d histograms in direction of the momentum. In every bin of the number of primary vertices, the mean and standard deviation are calculated and then a linear fit is performed to the result:

`python3 get_xy_corrs.py -Y 2022_Summer22 -C`

The results and plots of the fits are written to the directory specified in the `inputs/config/paths.py` file. 

## 4. Conversion to json scheme

The last step is the conversion to the json pog integration scheme. It can be started with the following command:

`python3 get_xy_corrs.py -Y 2022_Summer22 --convert`

## 5. Validation

A closure test is performed by comparing the phi modulation of the missing transverse momentum component before and after correction, taking into account systematic variations:

`python3 get_xy_corrs.py -Y 2022_Summer22 --validate -j 8`

The results should show an almost flat MET phi distribution after correction.


## Further options

The types of missing transverse momentum that are investigated can be controlled with the option `--met MET,PuppiMET`. They must be defined in the snapshot process.
The type of pileup can be investigated with the option `--pileup PV_npvsGood`.

A version name can be given to the currently used correction via `-V v0`.

Debug output can be printed by adding `--debug`.

The correction can be performed only on data or MC with the option `--process MC,DATA`.