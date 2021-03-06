# National Monument Audit

_Under construction until Spring 2021_

[Front-end interface is here](https://monumentlab.github.io/national-monument-audit/app/map.html). And [full documentation of technical process is here](https://monumentlab.github.io/national-monument-audit/app/docs.html).

This repository will contain:

1. Scripts that process monument data from a number of sources
2. The latest processed aggregate monument dataset
3. An interface for exploring that dataset

## Code repository organization

1. [./app/](https://github.com/MonumentLab/national-monument-audit/tree/main/app) directory contains the files (HTML, CSS, JS, JSON) for the front-end user interface. The files in [./app/data/](https://github.com/MonumentLab/national-monument-audit/tree/main/app/data) are generated by running the Python scripts outlined further down in this document.
1. [./config/](https://github.com/MonumentLab/national-monument-audit/tree/main/config) directory contains configuration files in JSON format. This is used during the data processing step (via Python scripts) outlined further down in this document.
    1. [data-model.json](https://github.com/MonumentLab/national-monument-audit/blob/main/config/data-model.json) is the main configuration file that contains all the logic for generating the monument study set.
       1. `"fields"` key contains a list of all the fields that will be indexed by the search engine
       1. `"fieldsForEntities"` contains the fields that should be used for extracting PEOPLE and EVENT entities from
       1. `"conditionalFieldsForEntities"` is the same as above, but only includes entities that are also part of the object's name
       1. `"types"` is a list of rules for determining an object's group (e.g. Marker, Building, Monument, etc) and a monument's type (e.g. pyramid, bust, obelisk, etc) when applicable.
    1. [ingest/](https://github.com/MonumentLab/national-monument-audit/tree/main/config/ingest) directory contains one JSON file per data source that is processed. Each one of these files contains the logic for how the source data set should be parsed and mapped to the study set fields.
1. [./data/](https://github.com/MonumentLab/national-monument-audit/tree/main/data) directory contains all the data (before, during, and after processing):
    1. [./compiled/](https://github.com/MonumentLab/national-monument-audit/tree/main/data/compiled) the output data from the data processing (as a result of running Python scripts outlined below)
    1. [./preprocessed/](https://github.com/MonumentLab/national-monument-audit/tree/main/data/preprocessed) cached data (e.g. geocoded locations) used during the data processing; this reduces the amount of time it takes to re-run the scripts.
    1. [./vendor/](https://github.com/MonumentLab/national-monument-audit/tree/main/data/vendor) directory contains all the raw data collected from the data sources. This also contains pre-processed data as a result of custom scripts written for parsing a particular data source (see "./scripts/" description below)
    1. [corrections.csv](https://github.com/MonumentLab/national-monument-audit/blob/main/data/corrections.csv) contains manual corrections to the data
    1. [entities_add.csv](https://github.com/MonumentLab/national-monument-audit/blob/main/data/entities_add.csv) contains entities (PEOPLE or EVENTS) that should be included but were not automatically extracted from the entity recognition process
    1. [entities_aliases.csv](https://github.com/MonumentLab/national-monument-audit/blob/main/data/entities_aliases.csv) contains a list of aliases for entities (PEOPLE or EVENTS), e.g. "Cristoforo Colombo" refers to the same person as "Christopher Columbus"
1. [./lib/](https://github.com/MonumentLab/national-monument-audit/tree/main/lib) contains custom Python libraries for use in Python scripts
1. [./scripts/](https://github.com/MonumentLab/national-monument-audit/tree/main/scripts) contains custom scripts that were used to preprocess data sources. This includes scripts for downloading and parsing websites.

## For running scripts

You must be using Python 3.x for running the scripts in this repository (developed using 3.6.8). To install requirements:

```
pip install -r requirements.txt
```

If you will be doing name entity extraction, you must also download the corpus:

```
python -m spacy download en_core_web_sm
```

If you are doing entity linking, you should also unzip [./data/wikidata.zip](https://github.com/MonumentLab/national-monument-audit/tree/main/data/wikidata.zip) into `./data/wikidata/`. This contains pre-processed Wikidata used for entity linking. If you don't do this, entity linking will be done from scratch and will take a long time to process.

## Adding new data sources

1. Create a new .json file in folder [./config/ingest/](https://github.com/MonumentLab/national-monument-audit/tree/main/config/ingest). You can copy the contents of an existing .json file as a template

   1. You can view existing configuration files

1. Run `python run.py -entities`. This will re-process _all the data_ and update [the compiled data files](https://github.com/MonumentLab/national-monument-audit/tree/main/data/compiled) as well as the [data for the app](https://github.com/MonumentLab/national-monument-audit/tree/main/app/data). The `-entities` flag is added to add a step to search for new PERSON and EVENT entities in the new data. This can take a while. If you are making only minor tweaks to the data (i.e. nothing that requires reprocessing entities), you can omit that flag.
   1. Behind the scenes this runs a number of scripts sequentially:

      ```
      python ingest.py
      python extract_entities.py
      python normalize_entities.py
      python resolve_entities.py
      python visualize_entities.py
      python ingest.py
      ```

    1. `ingest.py` is the central script that contains all the logic for transforming the source data into the compiled study set and interface. The next four scripts contain the steps for doing entity recognition and entity linking (to Wikidata entries). `ingest.py` must be run again after processing entities since entities are used when determining if an object is a monument or not.

1. Next you will need to index the data for the search interface; you can do this by running:

   ```
   python index.py -out "search-index/documents-2020-01-01/"
   ```

   The output folder name can be anything; I usually use the current date. If you do not pass in a folder name, it will put it in a folder `search-index/documents-latest/` (note, the script will always create a back-up directory at `search-index/backup/YYYY-MM-DD-HH-MM/`).

   Optionally you can add the path to the previous index output to look for deletions (otherwise, no documents will ever be deleted; only updated or added). ***You should include this parameter if you made changes that would remove records***, otherwise, there will be stale/outdated records in the search index.

   ```
   python index.py -out "search-index/documents-2020-01-01/" -prev "search-index/documents-2019-12-01/"
   ```

   This will generate a number of batch json files in the output directory. ***Each individual batch file should be under 5MB; otherwise AWS will reject it***. You can adjust the batch size by increasing or decreasing the records per batch file, e.g.:

   ```
   python index.py -out "search-index/documents-2020-01-01/" -prev "search-index/documents-2019-12-01/" -batchsize 2000
   ```

1. If you received no error in the previous step, you can now upload the batch files to the AWS CloudSearch Index. Before you do this, you will need to install [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html) and set your credentials (you will need permission to post new CloudSearch documents):

   ```
   aws s3 ls --profile monumentlab
   ```

   Then follow the prompts for entering your key and secret, and use region ***us-east-1***. This will store your credentials under profile "monumentlab". Then you can run the following script to upload the records from the previous step:

   ```
   python index_upload.py -in "search-index/documents-2020-01-01/*.json"
   ```

   If no directory is passed in, `search-index/documents-latest/*.json` will be uploaded. It may take some time for re-indexing, but it should happen automatically. You can manually refresh the index through the AWS console.

1. To view the changes locally, you will need to install (only once) and run the node server:

  ```
  npm install
  npm start
  ```

1. You can now view the dashboard on [localhost:2020/app/map.html](http://localhost:2020/app/map.html)
1. Committing and pushing your changes to the main branch will _automatically_ update the [online interface](https://monumentlab.github.io/national-monument-audit/app/map.html)
1. For debugging purposes, there is also an [advanced search interface](http://localhost:2020/app/search.html) that exposes the full dataset (before filtering out non-monuments) as well as all the raw fields
