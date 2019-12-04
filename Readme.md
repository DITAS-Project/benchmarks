# DITAS Load Test Experimentes

For more details see the  (experiment plan)[TestPlan.url]

## Prerequisites

To perform the benchmarks you need to have a linux system with:
 - make
 - curl
 - git

To compile the workload generator, you need:
 - git
 - go-lang 1.12
 - make

To perform data analytics you need:
 - python
 - jupyter-notebooks
 - scipy


## Usage

It is recommended that you run `scripts/prepare.sh` once to set linux properties  to perform this benchmark in a fair way.

To run the test modify run `make bench-<location>`, before that make sure to prepare the system under test according to the experiment plan.

## Data
Once your down with the experiments, run `git add data/` and `git commit -m "<Your Name> <Experiment Location>" && git push` to upload the data to this repo.


## Analytics and Reports
Run `make start` to work on processing the data. Put all plots into the images folder.