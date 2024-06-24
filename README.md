
# MTA documentation

Migration Toolkit for Applications (MTA) is a set of tools that can be used to accelerate large-scale application modernization efforts across hybrid cloud environments on Red Hat OpenShift.

This repository contains the files for Windup documentation.

## Contributing to MTA documentation

This project is [Apache 2.0 licensed](LICENSE) and accepts contributions via GitHub pull requests.

See the [Contributors Guide](CONTRIBUTING.adoc) for details.

## Reporting a documentation bug

To report a Windup documentation issue, submit a Jira issue on the [Windup project page]]{JiraWindupURL} with the *Component* field set to *Documentation*.

## Repository structure

This repository has the following directory structure:

```
.
├── CONTRIBUTING.adoc (Instructions on how to contribute to this repository)
├── README.md (This file)
├── topics (Symbolic link to docs/topics/)
└── docs/ (Contains all the asciidoc topics and top level content spec)
    ├── guide_name/
    │   ├── master.adoc (Base AsciiDoc file for this guide)
    │   ├── master-docinfo.xml (Metadata about this guide)
    │   └── topics (Symbolic link to docs/topics/)
    └── topics/
            ├── images/ (Contains all images)
            │   ├── *.png
            ├── templates/ (AsciiDoc templates to be used across guides)
            │   ├── document-attributes.adoc (Stores attributes used across guides)
            │   ├── revision-info.adoc (Revision timestamp to be added to all guides)
            └── *.adoc (AsciiDoc files used across guides)
``` 

## Code of conduct

[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.0-4baaaa.svg)](CODE_OF_CONDUCT.md)

## PR preview rendering

[![](https://www.netlify.com/img/global/badges/netlify-light.svg)](https://www.netlify.com)
