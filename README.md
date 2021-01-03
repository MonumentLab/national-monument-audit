# National Monument Audit

_Under construction until Spring 2021_

This repository will contain:

1. Scripts that process monument data from a number of sources
2. The latest processed aggregate monument dataset
3. An interface for exploring that dataset

## For running scripts

You must be using Python 3.x for running the scripts in this repository (developed using 3.6.8). To install requirements:

```
pip install -r requirements.txt
```

If you will be doing name entity extraction, you must also download the corpus:

```
python -m spacy download en_core_web_sm
```

## Adding new data sources

1. Create a new .json file in folder [./config/ingest/](https://github.com/MonumentLab/national-monument-audit/tree/main/config/ingest). You can copy the contents of an existing .json file as a template
1. Update all the fields in this configuration file for the new data source:

   ```
   TODO: list all the fields and descriptions --beefoo
   ```

1. Run `python ingest.py`. This will re-process _all the data_ and update [the compiled data files](https://github.com/MonumentLab/national-monument-audit/tree/main/data/compiled) as well as the [data for the app](https://github.com/MonumentLab/national-monument-audit/tree/main/app/data).
1. To view the changes locally, you will need to install (only once) and run the node server:

   ```
   npm install
   npm start
   ```

1. You can now view the dashboard on [localhost:2020/app/dashboard.html](http://localhost:2020/app/dashboard.html)
1. Committing and pushing your changes to the main branch will _automatically_ update the [online dashboard](https://monumentlab.github.io/national-monument-audit/app/dashboard.html)
1. Next you will need to index the data for the search interface; you can do this by running:

   ```
   python3 index.py -out "search-index/documents-2020-01-01/"
   ```

   The output folder name can be anything; I usually use the current date. Optionally you can add the path to the previous index output to look for deletions:

   ```
   python3 index.py -out "search-index/documents-2020-01-01/" -prev "search-index/documents-2019-12-01/"
   ```

   This will generate a number of batch json files in the output directory. ***Each individual batch file should be under 5MB; otherwise AWS will reject it***. You can adjust the batch size by increasing or decreasing the records per batch file, e.g.:

   ```
   python3 index.py -out "search-index/documents-2020-01-01/" -prev "search-index/documents-2019-12-01/" -batchsize 2000
   ```

1. Next you will need to upload the batch files to the AWS CloudSearch Index. Before you do this, you will need to install [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html) and set your credentials (you will need permission to post new CloudSearch documents):

   ```
   aws s3 ls --profile monumentlab
   ```

   Then follow the prompts for entering your key and secret, and use region ***us-east-1***. This will store your credentials under profile "monumentlab". Then you can run the following script to upload the records from the previous step:

   ```
   python3 index_upload.py -in "search-index/documents-2020-01-01/*.json"
   ```

   It may take some time for re-indexing, but it should happen automatically. You can manually refresh the index through the AWS console.
