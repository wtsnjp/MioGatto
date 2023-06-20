# Contributing to MioGatto

Thanks for considering contributing to MioGatto: feedback, fixes, and ideas are all useful.

## Creating pull request

* At least one approve from a reviewer except yourself before merging a pull request
* A branch name should be `<category>/<name>` (e.g., `feature/sog_labeling`)
    * `<category>` is one of `feature`, `fix`, `hotfix`

## Coding rules

### Python

We use `flake8` for linter and `black` for code formatting.

Our settings for `flake8` is in `.flake8`, so you can simply run:

```shell
flake8 <target file>
```

For formatting python codes, some options should be specified:

```shell
black --line-length 119 --skip-magic-trailing-comma --skip-string-normalization <target file>
```

### Type Script

Currently we don't have particular coding rules for Type Script.
