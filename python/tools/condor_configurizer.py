import os
import logging
logger = logging.getLogger(__name__)


def setup_job(condor_dir, dtmc, year):
    logger.info("Setting up the job script")
    # setup condor job script
    path = os.getcwd()
    job_script = f"#!/bin/bash \n"\
        f"cd {path} \n"\
        f"source env.sh \n"\
        f"python get_xy_corrs.py -S --condor $1 --process {dtmc} --year {year}"

    os.makedirs(f'{condor_dir}{dtmc}/logs/', exist_ok=True)
    with open(f'{condor_dir}{dtmc}/job.sh', 'w') as job:
        job.write(job_script)

    return


def setup_condor_etp(njobs, condor_dir, dtmc):

    logger.info("Setting up the submit file.")

    # setup condor submit file
    submit_script = f"""executable = ./job.sh
arguments = $(Process)

# Output/Error/Log files
Output = logs/job_$(Cluster)_$(Process).out
Error  = logs/job_$(Cluster)_$(Process).err
Log    = logs/job_$(Cluster)_$(Process).log

# job requirements
+RequestWalltime = 3600*2
RequestCPUs = 1
RequestMemory = 2000
request_disk = 5000000
Requirements = TARGET.ProvidesEKPResources =?= True
accounting_group = cms.higgs
Universe = docker
docker_image = mschnepf/slc7-condocker:latest
getenv = True

queue {njobs}"""
    
    path_submit = f'{condor_dir}{dtmc}/submit.sub'
    logger.info(f"Saving submit file in {path_submit}.")

    with open(path_submit, 'w') as submit:
        submit.write(submit_script)

    run_script = f"cd {condor_dir}{dtmc}/ && condor_submit submit.sub && cd ../../../../.."

    logger.info(f"Run script via: {run_script}")    
    return


def setup_condor_lxplus(njobs, condor_dir, dtmc):

    logger.info("Setting up the submit file.")

    # setup condor submit file
    submit_script = f"""executable = ./job.sh
arguments = $(Process)

# output/error/log files
output = logs/job_$(Cluster)_$(Process).out
eror = logs/job_$(Cluster)_$(Process).err
log = logs/job_$(Cluster)_$(Process).log

# job requirements
universe = vanilla
+JobFlavour = "espresso"
RequestCPUs = 1

queue {njobs}"""
    
    path_submit = f'{condor_dir}{dtmc}/submit.sub'
    logger.info(f"Saving submit file in {path_submit}.")

    with open(path_submit, 'w') as submit:
        submit.write(submit_script)

    run_script = f"cd {condor_dir}{dtmc}/ && condor_submit submit.sub && cd ../../../../.."

    logger.info(f"Run script via: {run_script}")    
    return