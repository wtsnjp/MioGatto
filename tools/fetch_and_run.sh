#!/bin/bash

arxiv_id=$1

# Simply remove '/' to obtain paper_id from arxiv_id.
paper_id=$(echo ${arxiv_id} | sed -e "s/\///g")

arxmliv_dir="./arxmliv"
template_dir="./templates"
source_dir="./sources"
data_dir="./data"

arxmliv_filename=${arxmliv_dir}/${paper_id}.html

# Exit when error occurs and show the commands to execute.
set -e -x

################
## Fetch HTML ##
################

python -m tools.fetch_html --arxmliv-dir ${arxmliv_dir} ${arxiv_id}

################
## Preprocess ##
################

python -m tools.preprocess --data=${template_dir} --sources=${source_dir} ${arxmliv_filename}

# Copy the templates to data directory.
cp ${template_dir}/${paper_id}_anno.json ${data_dir}/
cp ${template_dir}/${paper_id}_mcdict.json ${data_dir}/

#########################
## Run MioGatto Server ##
#########################

python -m server --host 0.0.0.0 --data=${data_dir} --sources=${source_dir} ${paper_id}