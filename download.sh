#!/bin/sh

set -ex

mkdir -p data

for state in bund bayern berlin nrw brandenburg mecklenburg-vorpommern hamburg niedersachsen bremen rheinland-pfalz thueringen sachsen sachsen-anhalt schleswig-holstein baden-wuerttemberg hessen saarland
do
  python -m wahlrecht $state > data/$state.csv
done
