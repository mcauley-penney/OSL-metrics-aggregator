# OSL Metrics Aggregator

This tool derives social network metrics from issue data mined from the GitHub API v3.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7740450.svg)](https://doi.org/10.5281/zenodo.7740450)

## How to run
The metrics aggregator uses a simple JSON configuration file:

```json
{
	"issue_data": "/path/to/issue/data",
	"out_path": "/path/to/output",
}
```

The `issue_data` key should have the path to the output of the extractor stage of the OSL pipeline. The `output_path` key should have the place you would like your metrics written to.

The call format to the program from the command line would be:

`python aggregator_main.py <cfg_path>`

For example:

`python aggregator_main.py audacity_cfg.json`


## Requirements
- Written in `Python 3.10`
- Install library dependencies via `requirments.txt`
    - `pip install -r requirements.txt`



## Contributing
#### commit formatting
- Please abide by the ["Conventional Commits"](https://www.conventionalcommits.org) specification for all commits

#### source code standards
Using default settings for each, please:
- format all contributions with [black](https://pypi.org/project/black/)
    - `pip install black`
- lint all contributions with [pylint](https://pypi.org/project/pylint/)
    - `pip install pylint`
