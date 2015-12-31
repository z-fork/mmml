#!/bin/sh
PROJ_DIR=/home/shenfei/work/dagobah
Rscript ${PROJ_DIR}/cet/data_prepare.R
PYTHONPATH=${PROJ_DIR} python ${PROJ_DIR}/cet/irt.py --cross_validation
PYTHONPATH=${PROJ_DIR} python ${PROJ_DIR}/cet/mock_predict.py

#Rscript ${PROJ_DIR}/cet/data_prepare.R --banker
#PYTHONPATH=${PROJ_DIR} python ${PROJ_DIR}/cet/irt.py --cross_validation --banker
#PYTHONPATH=${PROJ_DIR} python ${PROJ_DIR}/cet/mock_predict.py --banker

