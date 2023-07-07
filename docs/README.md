[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8084759.svg)](https://doi.org/10.5281/zenodo.8084759)

# mr_proc 

A workflow manager for curating MRI and tabular data and standardized processing. 

*Process long and prosper.*

**Note: This is a template branch which is typically customized for a specific dataset**

## Documentation

### mr_proc modules

- [mr_proc](https://www.neurobagel.org/documentation/mr_proc/overview/)

### Individual containerized pipelines:

- [Heudionv](https://heudiconv.readthedocs.io/en/latest/installation.html#singularity) 
- [MRIQC](https://mriqc.readthedocs.io/en/stable/)
- [fMRIPrep](https://fmriprep.org/en/1.5.5/singularity.html) 
- [TractoFlow](https://github.com/scilus/tractoflow)
- [MAGeT Brain](https://github.com/CoBrALab/MAGeTbrain)

### GH workflow for contributing to template and dataset-specific forks

![mr_proc_gh_contribution_workflow](https://user-images.githubusercontent.com/29051929/236941655-f7dcc981-a2f4-4f3f-b1fc-8c2afdfcc8cf.png)

### Organization
* Under the `neurodatascience` GitHub organization:
  * The `mr_proc(*)` ("template") repository contains all common code-base: `neurodatascience/mr_proc`
  * Make a fork for each dataset: `neurodatascience/mr_proc-[dataset]`
* Under the `user` GitHub account:
  * Make a fork of `mr_proc(*)` ("template") repository: `<user>/mr_proc`
* Local machine
  * Clone all the `neurodatascience/mr_proc-[dataset]` and the `<user>/mr_proc` repos. 
  
### Basic principles 
* `mr_proc(*)` is the code-base common across all dataset forks
* `mr_proc-[dataset]` will have additional files but there **should not be** different versions of the same file (including `README.md`) between `mr_proc(*)` and `mr_proc-[dataset]`
* Branch-protection are set to avoid direct commits to all main branches. Contributions should be done through PRs only
* Updates to `mr_proc(*)` and `mr_proc-[dataset]` will follow separate paths requiring different repo-clones on the local machine
* GH-Actions are used to distribute common changes from `mr_proc(*)` to `mr_proc-[dataset]`
* Nothing is pushed from `neurodatascience/mr_proc-[dataset]` to `neurodatascience/mr_proc`

### Contribution steps:
  * Changes that apply to all datasets (e.g. bids conversion, pipeline run scripts, tracker scripts):
    * Make a user fork of `neurodatascience/mr_proc`: `[gh-username]/mr_proc`
    * Clone `[gh-username]/mr_proc` locally
    * Push to `[gh-username]/mr_proc` on GitHub
    * PR from `[gh-username]/mr_proc` to `neurodatascience/mr_proc`
    * Any time a PR is merged to `neurodatascience/mr_proc:main`, the newly added changes (common across dataset) will propagate automatically to **all** `neurodatascience/mr_proc-[dataset]` forks through a GitHub Actions workflow
      * In each dataset fork, the `main-upstream` branch is created/updated automatically to match `neurodatascience/mr_proc:main`
      * A PR labelled "automerge" is automatically created to incorporate changes from `main-upstream` to `main`
      * "Automerge" PRs are approved and merged automatically if there are no merge conflicts
        * If merge conflicts exist, they must be resolved manually. Then the PR needs to be **merged**, without squashing or rebasing
  * Changes that apply to individual datasets (e.g. dicom wrangling, statistical analysis) 
    * Clone `neurodatascience/mr_proc-[dataset]` locally
    * Make a new branch when working on a new feature
      * `main` is protected on these forks as well - all contributions have to be made through dev branches.
      * ***IMPORTANT***: need to be careful with branch names, they should be unique
    * PR from `neurodatascience/mr_proc-[dataset]:[feature_branch]` to `neurodatascience/mr_proc-[dataset]:main`
    * Delete branch when done
  * Adding a new dataset
    * Make a new fork of the template repo (`neurodatascience/mr_proc`) called `neurodatascience/mr_proc-[dataset]`
    * Update the GitHub Actions workflow file to add the new fork to the job matrix
    * Add dataset-specific files to the fork and begin processing (see the [`mr_proc` documentation](https://www.neurobagel.org/documentation/mr_proc/workflow/dicom_org/) for more information)
