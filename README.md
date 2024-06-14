
# MTA Documentation

This repository contains the files for Migration Toolkit for Applications (MTA) documentation.

[MTA](https://github.com/migtools/mta-documentation) is an automated application migration and assessment tool.

For upstream developer-focused information, see the [Konveyor homepage](https://www.konveyor.io/).

## Contributing to MTA documentation

This project is [Apache 2.0 licensed](LICENSE) and accepts contributions via GitHub pull requests.

See the [Contributors Guide](CONTRIBUTING.adoc) for details.

## Reporting a documentation bug

To report an MTA documentation issue, submit a Jira issue on the [MTA documentation project page]](https://issues.redhat.com/projects/MTA/issues/MTA-2944?filter=allopenissues) with the *Component* field set to *Documentation*.

## Repository Structure

This repository uses the following directory structure:

```
.
├── CONTRIBUTING.adoc (Guide for how to contribute to this repository)
├── README.md (This file)
├── topics (Symbolic link to docs/topics/)
└── docs/ (Contains all the asciidoc topics and top level content spec)
    ├── GUIDE_NAME/
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
