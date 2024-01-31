# MioGatto: Math Identifier-oriented Grounding Annotation Tool

## System requirements

* Python3 (3.9 or later)
* A Web Browser with MathML support (for the GUI annotation system)
    * [Firefox](https://www.mozilla.org/firefox/) is recommended

## Installation

The dependencies will be all installed with one shot:

```shell
python -m pip install -r requirements.txt
```

In case you don't want to install the dependencies into your system, please
consider using [venv](https://docs.python.org/3/library/venv.html).

## Project structure

### Files in this repository

All the components of MioGatto is included in this repository:

* `lib/` contains the project library.
* `server/` contains the implementation of the server.
* `client/` contains the implementation of the client.
* `tools/` contains our utility Python scripts.

### Files not in this repository

On the other hand, the annotation data is not included in this repository due
to the NDA constrain for [the arXMLiv dataset](https://sigmathling.kwarc.info/resources/arxmliv-dataset-2020/). The data is licensed to
[SIGMathLing members](https://sigmathling.kwarc.info/member/) as [Dataset for
Grounding of Formulae](https://sigmathling.kwarc.info/resources/grounding-dataset/).
Please consider joining [SIGMathLing](https://sigmathling.kwarc.info/member/)
to acquire the dataset.

* `arxmliv/` contains the original documents from the arXMLiv dataset
* `templates/` contains the empty annotation data
* `data/` contains the annotation data
* `sources/` contains the preprocessed documents

## Quick start with Docker

Here's how to quickly start MioGatto without preparing the local environment:

```shell
(in local env)$ docker build ./ -t miogatto
(in local env)$ docker run -it --rm -p 4100:4100 -v ${path to arxmliv dir}:/MioGatto/arxmliv -v ${path to templates dir}:/MioGatto/templates -v ${path to data dir}:/MioGatto/data -v ${path to sources dir}:/MioGatto/sources miogatto
```

The scond command above launches an interactive bash terminal in the container, and you can use MioGatto in it. Note that you need to prepare `arxmliv`, `templates`, `data`, `sources` directories beforehand and pass them to `docker run` to mount. Otherwise some scripts do not run with the default settings.

### Run MioGatto on existing annotation data files

```shell
(in container)$ python -m server --host 0.0.0.0 ${paper id}
```

Note that you need to set the host address to `0.0.0.0` to access the server from outside the container.

### Run MioGatto on papers whose annotation data files do not exists

The following command prepare necessary annotation files via [ar5iv](https://ar5iv.labs.arxiv.org/) and directly lauches the MioGatto server.

```shell
(in container)$ bash ./tools/fetch_and_run.sh ${arxiv id}
```

Note that arxiv id might be different from paper id, e.g., arxiv id: `math/0303074` and paper id: `math0303074`. For more information about arxiv id, please refer to [the official page](https://info.arxiv.org/help/arxiv_identifier.html).
Also note that, the `tools/fetch_and_run.sh` script fails when there are existing annotation data files. Please directly launch the MioGatto server when you want to continue the annotation (see the previous section).

Importantly, the `tools/fetch_and_run.sh` script does not apply paper-specific preprocess, and the obtained annotation files might be different from the released ones.

## Annotator's guide

For the guide with GIF animation, please refer to our Wiki:

* <https://github.com/wtsnjp/MioGatto/wiki/Annotator's-Guide>

## Prepare the input and analyze the annotated data (Advanced)

The Python scripts under the `tools` directory are mostly for the developers
for the grounding dataset. The `--help` (`-h`) option is available for all
scripts and should provide guides to their basic usages.

### Preparing data

As mentioned above, the HTML5 files in [the arXMLiv dataset](https://sigmathling.kwarc.info/resources/arxmliv-dataset-2020/)
are suitable as the input document for MioGatto. Alternatively, you can provide
the equivalent HTML5 files from LaTeX sources by using
[LaTeXML](https://dlmf.nist.gov/LaTeXML/):

```shell
latexmlc --preload=[nobibtex,ids,mathlexemes,localrawstyles]latexml.sty --format=html5 --pmml --cmml --mathtex --nodefaultresources --dest=<output HTML file> <input TeX file>
```

Then you can give the HTML5 files to our preprocess script:

```shell
python -m tools.preprocess <HTML file>
```

This will output the preprocessed HTML file to the `sources/` and generate the
initialized JSON files for the annotation to the `data/` by default. Please
refer to the help message for the options.

```shell
python -m tools.preprocess -h
```

### Analysing the annotation results

For the basic analyses for annotation data, execute:

```shell
python -m tools.analyzer <paper id>
```

Some supplemental files including graph images will be saved in the `results`
directory as default.

Similarly, analyses for the sources of grounding annotation can be performed
with the `tools.sog` script.

```shell
python -m tools.sog <paper id>
```

To calculate agreements between data by two annotators, execute:

```shell
python -m tools.agreement --target=<path to annotator's data dir> <paper id>
```

## Developing client

The client is developed with TypeScript. All development tools will be
installed with:

```shell
cd client
npm install
```

To compile the client source `client/index.ts`, execute the following in the
client directory:

```shell
npm run build
```

## Publications

* Takuto Asakura, Yusuke Miyao, Akiko Aizawa. **Building Dataset for Grounding of Formulae — Annotating Coreference Relations Among Math Identifiers**. In Proceedings of [13th Conference on Language Resources and Evaluation (LREC 2022)](https://lrec2022.lrec-conf.org). pp. 4851―4858, 2022.  
  [[paper](https://aclanthology.org/2022.lrec-1.519/)] [[bib](http://www.lrec-conf.org/proceedings/lrec2022/bib/2022.lrec-1.519.bib)] [[slides](https://speakerdeck.com/wtsnjp/lrec2022)] [[video](http://www.lrec-conf.org/proceedings/lrec2022/media/sessions/935.mp4)] [[resource](https://sigmathling.kwarc.info/resources/grounding-dataset/)]
* Takuto Asakura, Yusuke Miyao, Akiko Aizawa, Michael Kohlhase. **MioGatto: A Math Identifier-oriented Grounding Annotation Tool**. In [13th MathUI Workshop at 14th Conference on Intelligent Computer Mathematics (MathUI 2021)](https://cicm-conference.org/2021/cicm.php?event=MathUI).  
  [[preprint](https://easychair.org/publications/preprint/FSSk)] [[paper](https://kwarc.info/teaching/CICM21WS/mathui5.pdf)] [[slides](https://speakerdeck.com/wtsnjp/mathui2021)] [[code](https://github.com/wtsnjp/MioGatto)]
* Takuto Asakura, André Greiner-Petter, Akiko Aizawa, Yusuke Miyao. **Towards Grounding of Formulae**. In Proceedings of [First Workshop on Scholarly Document Processing (SDP 2020)](https://ornlcda.github.io/SDProc/). pp. 138―147, 2020.  
	[[paper](https://www.aclweb.org/anthology/2020.sdp-1.16/)] [[bib](https://www.aclweb.org/anthology/2020.sdp-1.16.bib)] [[poster](https://wtsnjp.com/posters/sdp2020-asakura-poster.pdf)]  [[resource](https://sigmathling.kwarc.info/resources/grounding-dataset/)]
* Takuto Asakura, André Greiner-Petter, Akiko Aizawa, Yusuke Miyao. **Dataset Creation for Grounding of Formulae**. In [SCIDOCA 2020](http://research.nii.ac.jp/SCIDOCA2020/).  
	[[slides](https://speakerdeck.com/wtsnjp/scidoca2020)] [[resource](https://sigmathling.kwarc.info/resources/grounding-dataset/)]

## Acknowledgements

This project has been supported by JST, ACT-X Grant Number JPMJAX2002, Japan.

## License

Copyright 2021 Takuto Asakura ([wtsnjp](https://wtsnjp.com))

This software is licensed under [the MIT license](./LICENSE).

### Third-party software

* [jQuery](https://jquery.org/): Copyright JS Foundation and other contributors. Licensed under [the MIT license](https://jquery.org/license).
* [jQuery UI](https://jqueryui.com/): Copyright jQuery Foundation and other contributors. Licensed under [the MIT license](https://github.com/jquery/jquery-ui/blob/HEAD/LICENSE.txt).

---

Takuto Asakura ([wtsnjp](https://wtsnjp.com))
