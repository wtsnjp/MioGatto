#!/bin/bash

python -m server -d datasets/ -s sources/ --host 0.0.0.0 $@
