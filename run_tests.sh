#!/bin/bash
source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:.
pytest test_fuwa.py
