# RDCP Toolbox

## Getting started

```
cd existing_repo
git remote add origin https://ci.tno.nl/gitlab/msb/automation/krane-toolbox.git
git branch -M main
git push -uf origin main
```

## API token

Create a file named `api-token.config` in the root folder of this repo and paste your API-token directly from the management portal. 

## Base URL

The base URL defined in the file `base-url.config` should point to the correct RDCP environment.

## Input and Output folders

Some scripts require input files. These files should be placed in the `input` folder. The output of the scripts will be placed in the `output` folder.
