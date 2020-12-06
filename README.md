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
