# pcap2las
Convert an Ouster PCAP file to an LAS or LAZ file. The new LAS or LAZ file is written to the same location as the PCAP file and has the same name as the PCAP file.

## Install
1. Clone or download this repo.
2. Open a command prompt and navigate to the project root directory.
3. Create a new Conda environment: `conda env create -f environment.yml`
4. Activate the new Conda environment: `conda activate ouster`
4. Install: `pip install .`

## Use
* Form: `pcap2las <pcap_file> <metadata_file> [--chunk-size] [--format]`
* Example with defaults: `pcap2las path\to\my\pcap_file.pcap path\to\my\metadata_file.json`
* Example with options: `pcap2las path\to\my\pcap_file.pcap path\to\my\metadata_file.json --chunk-size 500 --format las`

## Arguments and Options
* The `pcap_file` and `metadata_file` arguments are required positional arguments.
* Optional arguments:
    * `chunk-size`: A large size is better (faster) for large PCAP files. [integer; default = `1000`]
    * `format`: Export a LAS or LAZ format file. [`las` or `laz`; default = `laz`]

## Probable
* PCAP files can get huge. For very large PCAP files, this tool will use up your memory and either fail or take forever to complete.
    * Chunked output (i.e., multiple LAS files) will likely be desired.
    * We could probably set it up such that the `chunk-size` option also controls the chunked LAS output.
