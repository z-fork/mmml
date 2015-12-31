#!/bin/sh
PROJ_DIR=/home/shenfei/work/dagobah

# question_factor
PYTHONPATH=${PROJ_DIR} python ${PROJ_DIR}/english/question_factor.py
echo "english question factor done"
PYTHONPATH=${PROJ_DIR} python ${PROJ_DIR}/maths/question_factor.py
echo "maths question factor done"
PYTHONPATH=${PROJ_DIR} python ${PROJ_DIR}/art/question_factor.py
echo "art question factor done"
PYTHONPATH=${PROJ_DIR} python ${PROJ_DIR}/science/question_factor.py
echo "science question factor done"

# user_factor
PYTHONPATH=${PROJ_DIR} python ${PROJ_DIR}/english/user_factor.py
PYTHONPATH=${PROJ_DIR} python ${PROJ_DIR}/maths/user_factor.py
PYTHONPATH=${PROJ_DIR} python ${PROJ_DIR}/art/user_factor.py
echo "art user factor done"
PYTHONPATH=${PROJ_DIR} python ${PROJ_DIR}/science/user_factor.py
echo "science user factor done"
