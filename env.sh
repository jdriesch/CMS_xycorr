export ARCH=$(uname -a)

if [[ "$ARCH" == *el9* ]]; then
    echo "Sourcing LCG stack for RHEL9"
    source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc11-opt/setup.sh

else
    if [[ "$HOSTNAME" != "portal1-centos7" ]]; then
        echo "sourcing LCG stack for RHEL9"
        # source /cvmfs/sft.cern.ch/lcg/views/LCG_106/x86_64-el9-gcc13-opt/setup.sh
        source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc11-opt/setup.sh
        echo "Done!"

    else
        echo "sourcing LCG stack for CENTOS7"
        source /cvmfs/sft.cern.ch/lcg/views/LCG_102rc1/x86_64-centos7-gcc11-opt/setup.sh
        echo "Done!"
    fi
fi

if [ ! -d inputs/jsonpog ]; then
    git clone https://gitlab.cern.ch/cms-nanoAOD/jsonpog-integration.git inputs/jsonpog
fi
    
