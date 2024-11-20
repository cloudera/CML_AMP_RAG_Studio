# Release process for the RAG Studio AMP

* Get `main` into the state to be released
* Publish a release from the `main` branch with the desired version to release using [the **Publish a release** Github Action](https://github.com/cloudera/CML_AMP_RAG_Studio/actions/workflows/publish_release.yml)
  * Use a version number incremented as appropriate from [the most recent release](https://github.com/cloudera/CML_AMP_RAG_Studio/releases)
* Verify the release in a CML workspace, deploying from `main`
* Merge main into the `release/1` branch via a pull request, keeping the version file contents from main
  * Let the PR build run, to verify no merge conflicts took place
* If desired: publish a new release with the same version from the `release/1` branch to make sure the code matches the release bundles.

