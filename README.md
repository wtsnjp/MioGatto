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

In case you don't want to install the dependencies into your system, please
consider utilizing [venv](https://docs.python.org/3/library/venv.html).

## Project structure

### Files in this repository

All the components of MioGatto is included in this repository:

* `lib/` contains the project library.
* `server/` contains the implementation of the server.
* `client/` contains the implementation of the client.
* `tools/` contains our utility Python scripts.

### Files not in this repository

On the other hand, the annotation data is not included in this repository due
to the NDA constrain for the arXMLiv dataset. The data is licensed to
[SIGMathLing members](https://sigmathling.kwarc.info/member/) as [Dataset for
Grounding of Formulae](https://sigmathling.kwarc.info/resources/grounding-dataset/).
Please consider joining [SIGMathLing](https://sigmathling.kwarc.info/member/)
to acquire the dataset.

* `arxmliv/` contains the original documents from the arXMLiv dataset
* `data/` contains the annotation data
* `sources/` contains the preprocessed documents

## Annotator's guide

For the guide with GIF animation, please refer to our Wiki:

* <https://github.com/wtsnjp/MioGatto/wiki/Annotator's-Guide>

## Using tools

The Python scripts under the `tools` directory are mostly for the developers
for this dataset. The `--help` (`-h`) option is available for all scripts.
Detailed documents have not yet prepared.


### Preprocess

The basic usage will be shown with:

```
$ python -m tools.preprocess -h
```

### Analysing the annotation results

For the basic analyses for annotation data, execute:

```
$ python -m tools.analyzer <paper id>
```

Some supplemental files including graph images will be saved in the `results`
directory as default.

To calculate agreements between data by two annotators, execute:

```
$ python -m tools.agreement --target=<path to annotator's data dir> <paper id>
```

## Developing client

The client is developed with TypeScript. All development tools will be
installed with:

```
$ cd client
$ npm install
```

To compile the client source `client/index.ts`, execute the following in the
client directory:

```
$ npx tsc
```

## Publications

* Takuto Asakura, André Greiner-Petter, Akiko Aizawa, Yusuke Miyao. **Towards Grounding of Formulae**. In Proceedings of [First Workshop on Scholarly Document Processing (SDP 2020)](https://ornlcda.github.io/SDProc/). pp. 138―147, 2020.  
	[[paper](https://www.aclweb.org/anthology/2020.sdp-1.16/)] [[bib](https://www.aclweb.org/anthology/2020.sdp-1.16.bib)] [[poster](https://wtsnjp.com/posters/sdp2020-asakura-poster.pdf)]  [[resource](https://sigmathling.kwarc.info/resources/grounding-dataset/)]
* Takuto Asakura, André Greiner-Petter, Akiko Aizawa, Yusuke Miyao. **Dataset Creation for Grounding of Formulae**. In [SCIDOCA 2020](http://research.nii.ac.jp/SCIDOCA2020/).  
	[[slides](https://speakerdeck.com/wtsnjp/scidoca2020)] [[resource](https://sigmathling.kwarc.info/resources/grounding-dataset/)]

## License

Copyright 2021 Takuto ASAKURA ([wtsnjp](https://wtsnjp.com))

This software is licensed under [the MIT license](./LICENSE).

### Third-party software

* [jQuery](https://jquery.org/): Copyright JS Foundation and other contributors. Licensed under [the MIT license](https://jquery.org/license).
* [jQuery UI](https://jqueryui.com/): Copyright jQuery Foundation and other contributors. Licensed under [the MIT license](https://github.com/jquery/jquery-ui/blob/HEAD/LICENSE.txt).

---

Takuto ASAKURA ([wtsnjp](https://wtsnjp.com))
