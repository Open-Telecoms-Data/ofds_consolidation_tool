---
layout: default
title: Introduction
nav_order: 1
---

1. Table of contents
{:toc}

# OFDS Consolidation Tool

This is a [QGIS](https://qgis.org/) plugin to consolidate (deduplicate, combine) data from two networks of spans and nodes represented in the [Open Fibre Data Standard](https://open-fibre-data-standard.readthedocs.io/en/latest/index.html) (OFDS).

## Using the tool - quickstart guide

For more detail on any of these steps, see the [how to guide](howto).

1. Add your nodes and spans geoJSON files as Vector Layers in QGIS (optionally add map tiles; make sure the map is at the bottom of the layers).
2. Start and configure the consolidation tool. Click through each presented pair of nodes and spans, and "Consolidate" or "Keep Both". Click "Finish" when you've compared them all.
3. Configure how much provenance metadata you want to keep with the output, then save the output.

Both the input and the output of the tool should be OFDS conformant geoJSON.

## Who is this tool for?

This tool is for anyone who works with data representing networks of fibre infrastructure. You might be:

* A national network regulator
* A network operator
* A public official
* A policy maker
* A fibre infrastructure engineer
* A civil engineer
* Someone with another interest in fibre infrastructure!

## What can this tool do?

This tool can take 2 datasets that each represent a fibre network, and help you to consolidate them.

* Where the datasets contained features that could be the same, for example a span of fibre being used by both networks, the tool presents you with the information needed to decide if these coincident features are actually the same piece of infrastructure.
* The tool generates confidence scores based on the data fields present. You can use these to assess how likely it is that a feature from the primary dataset is a duplicate of a nearby feature from the second dataset.
* Where a duplication is confirmed the tool retains the details of both network operators for that feature.

The end result will be a single OFDS dataset representing both networks with no duplicate features. This output can be downloaded for further analysis outside of QGIS if required.

Once the tool has been downloaded it can run offline.

The tool allows you to configure:

* the maximum distance between pairs of features that could be duplicates
* the confidence scores above and below which the tool will make automatic decisions about duplication without you needing to confirm
* the amount of provenance metadata you want to retain in the final output.

## What can this tool not do?

This tool cannot consolidate datasets that do not conform to the [Open Fibre Data Standard](https://open-fibre-data-standard.readthedocs.io/en/latest/index.html).

## Security and privacy

* The tool does not collect any personal or usage data.
* The tool does not store copies of any input or output data.
* No data is sent or retrieved over the web from the tool.
