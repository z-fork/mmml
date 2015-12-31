#!/bin/sh
PROJ_DIR=/home/shenfei/work/dagobah

PYTHONPATH=${PROJ_DIR} python ${PROJ_DIR}/capability/capability_rank.py
PYTHONPATH=${PROJ_DIR} python ${PROJ_DIR}/capability/math_capability_rank.py
PYTHONPATH=${PROJ_DIR} python ${PROJ_DIR}/cet/capability_rank.py
PYTHONPATH=${PROJ_DIR} python ${PROJ_DIR}/chart.py
PYTHONPATH=${PROJ_DIR} python ${PROJ_DIR}/cet/chart.py
