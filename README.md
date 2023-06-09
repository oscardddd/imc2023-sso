# Requirements

The ```just``` command line tool https://github.com/casey/just

# Raw Data Used in Paper

## Crawler data 
**Warning:** This data was collected automatically from a top list. Across website screenshots there is *a lot* of porn.

### Top 1K (1.3 GB)
https://drive.google.com/file/d/1tQV7UarMKjv7cF1aSW4HKSrhKIeFikZh/view?usp=sharing

### Top 10K

Incoming...

## Top list (221 MB)
https://drive.google.com/file/d/1wo8uXII3PQmXO13rMwunSCBQc3QcspFJ/view?usp=share_link

## Ground Truth Labled Data (17 KB)
https://drive.google.com/file/d/1e89O5qxPy8931kNITVMncUss350BuTzq/view?usp=sharing

# Code and Tools

## Crawler Data Collection

1. See the **Quick Start** in [crawler/README.md](crawler/README.md).

## Ground Truth Labeling

1. Navigate to the analysis/ground-truth-labeling directory.
2. Follow the instructions in the README.

## Logo Detection

1. Navigate to the logo-detection directory.
2. Edit the justfile ```datadir``` variable to point to the crawler data folder.
3. Run ```just install-dependencies```
4. Execute logo detection
    * ```just match-one```: displays results for 1 image.
    * ```just match-all```: Runs on a directory of login screenshots.
    * ```just match-parallel```: parallelizes processing of match-all.
