#!/bin/sh
# Unicode 14.0.0's data files that alphabet.py reads, from unicode.org, into DIR.
# alphabet.py checks each by SHA-256 and BLAKE3 before reading it.
set -eu
dir=${1:?usage: sh alphabet/fetch.sh DIR}
mkdir -p "$dir"
for f in ArabicShaping.txt DerivedAge.txt DerivedCoreProperties.txt DerivedNormalizationProps.txt PropList.txt Scripts.txt Unihan.zip; do
	curl -sSfL -o "$dir/$f" "https://www.unicode.org/Public/14.0.0/ucd/$f"
done
