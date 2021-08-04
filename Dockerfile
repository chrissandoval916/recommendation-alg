FROM centos:7

RUN yum update -y \
    && yum install -y \
      https://repo.ius.io/ius-release-el7.rpm \
      https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm \
      https://centos7.iuscommunity.org/ius-release.rpm \
    && yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

RUN yum install --enablerepo='cr' -y \
      jq \
      git \
      gcc \
      sudo \
      make \
      unzip \
      maven \
      curl \
      python36 \
      python36-pip \
      docker-ce \
      bind-utils \
      gcc-c++ \
      libpng-devel \
      libtool \
      automake \
      autoconf \
      nasm \
    && yum clean all

###########
# Simple Python setup:
###########
#RUN pip3 install --upgrade pip
#
#COPY requirements.txt .
#RUN pip3 install -r requirements.txt
#
#RUN mkdir ./data
#
#ENTRYPOINT ["tail"]
#CMD ["-f","/dev/null"]
###########
# END
###########

ENV PYTHON_VERSION 3.6

#Conda needs bash as sh doesnt play nice
SHELL [ "/bin/bash", "--login", "-c" ]

COPY environment.yml requirements.txt /tmp/
#COPY postBuild /usr/local/bin/postBuild.sh

ENV PYTHON_VERSION 3.6
ENV CONDA_DIR /opt/conda/

# Install Conda and test dependencies
RUN curl -L https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -o /tmp/miniconda.sh \
    && sudo bash /tmp/miniconda.sh -bfp $CONDA_DIR \
    && rm -rf /tmp/miniconda.sh \
    && sudo $CONDA_DIR/bin/conda install -y -c conda-canary -c defaults -c conda-forge \
        conda conda-package-handling \
        python=$PYTHON_VERSION pycosat requests ruamel_yaml cytoolz \
        anaconda-client nbformat \
        pytest pytest-cov pytest-timeout mock responses pexpect xonsh \
        flake8 \
    && sudo $CONDA_DIR/bin/conda clean --all --yes

# Make non-activate conda commands available
ENV PATH=$CONDA_DIR/bin:$PATH
# Make conda activate command available from /bin/bash --login shells
RUN echo ". $CONDA_DIR/etc/profile.d/conda.sh" >> ~/.profile
# Make conda activate command available from /bin/bash --interative shells
RUN conda init bash

# Make work directory
ENV PROJECT_DIR /data
RUN mkdir $PROJECT_DIR
WORKDIR $PROJECT_DIR

# Build the conda environment
ENV ENV_PREFIX $PWD/env
RUN conda update --name base --channel defaults conda && \
    conda env create --prefix $ENV_PREFIX --file /tmp/environment.yml --force && \
    conda clean --all --yes
# Run the postBuild script to install any JupyterLab extensions
RUN conda activate $ENV_PREFIX && \
    #/usr/local/bin/postBuild.sh && \
    conda deactivate
RUN conda config --add channels conda-forge
RUN conda config --add channels anaconda
# Install requirements
RUN conda install --file /tmp/requirements.txt

ENTRYPOINT ["tail"]
CMD ["-f","/dev/null"]