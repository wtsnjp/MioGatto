# MioGatto: Math Identifier-oriented Grounding Annotation Tool

## System requirements

* Python3 (3.5 or later)
* A Web Browser with MathML support (for the GUI annotation system)
    * [Firefox](https://www.mozilla.org/firefox/) is recommended

## Installation

The dependencies will be all installed with one shot:

```
$ python -m pip install -r requirements.txt
```

In case you don't want to install the dependencies into your system, please consider utilizing [venv](https://docs.python.org/3/library/venv.html).

## Project structure

### Files in this repository

All the components of MioGatto is included in this repository:

* `lib/` contains the project library.
* `server/` contains the implementation of the server.
* `static/` contains the implementation of the client.
* `tools/` contains our utility Python scripts.

### Files not in this repository

On the other hand, the annotation data is not included in this repository due to the NDA constrain for the arXMLiv dataset. The data is licensed to [SIGMathLing members](https://sigmathling.kwarc.info/member/) as [Dataset for Grounding of Formulae](https://sigmathling.kwarc.info/resources/grounding-dataset/). Please consider joining [SIGMathLing](https://sigmathling.kwarc.info/member/) to acquire the dataset.

* `arxmliv/` contains the original documents from the arXMLiv dataset
* `data/` contains the annotation data
* `sources/` contains the preprocessed documents

## A short guide for annotators

### Getting started

Herein, `<paper id>` denotes the arXiv ID of the paper to annotate.

1. Start the server: `python -m server <paper id>`
2. Access to <http://localhost:4100/> with your browser.
3. Annotation with the Web interface.

### Annotation procedure

1. Select a math identifier. The identifiers which has not yet annotated are shown with gray background.
2. The annotation box will appear in the right side. Choose the most suitable candidate in the list.
3. Select a span of a source of grounding and click the "Add Source" button (if any)

### Some notes

* Strongly recommended to manage your progress (in the `data/` directory) with VCS such as Git
* You may feel the dictionary (the mcdict list) is inappropriate, but please choose the best candidate in the list at this point
* Any suggestion about this annotation tool is welcome

## Using tools

The Python scripts under the `tools` directory are mostly for the developers for this dataset. Detailed documents have not yet prepared.

### The preprocess

The basic usage will be shown with:

```
$ python -m tools.preprocess -h
```

### The analyser

To calculate agreements between the gold data and data by annotators, execute:

```
$ python -m tools.analyzer --agreement=./annotators/<annotator>/<paper id>_anno.json <paper id>
```

For the basic analyses for gold data, execute:

```
$ python -m tools.analyzer <paper id>
```

Some supplemental files including graph images will be saved in the `results` directory as default. All available options will be shown with:

```
$ python -m tools.analyzer -h
```

## License

Copyright 2021 Takuto ASAKURA ([wtsnjp](https://wtsnjp.com))

This software is licensed under [the MIT license](./LICENSE).

### Third-party software

* [jQuery](https://jquery.org/): Copyright JS Foundation and other contributors. Licensed under [the MIT license](https://jquery.org/license).
* [jQuery UI](https://jqueryui.com/): Copyright jQuery Foundation and other contributors. Licensed under [the MIT license](https://github.com/jquery/jquery-ui/blob/HEAD/LICENSE.txt).

---

Takuto ASAKURA ([wtsnjp](https://wtsnjp.com))
