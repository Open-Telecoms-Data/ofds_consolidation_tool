---
layout: default
title: How to guide
nav_order: 2
---

1. Table of contents
{:toc}

# How to use the OFDS consolidation tool

## Install QGIS and the plugin

The consolidation tool is a [QGIS](https://qgis.org/) plugin. The tool works with QGIS version 3.28 and higher. If you have an older version of QGIS installed, you need to upgrade it.

The plugin is currently in development beta, and not yet available from the QGIS plugin libraries.

To download and install the plugin, you need an internet connection, but after that it will work offline.

1. Open the [Consolidation tool Github repository](https://github.com/Open-Telecoms-Data/ofds_consolidation_tool) ensuring you are on the main branch.
2. Click `Code` > `Download ZIP` and download a zipped version of the repository.
3. Open QGIS. Go to `Plugins > Manage and Install Plugins > Install from ZIP`.
4. Search for and select "ofds_consolidation_tool-main.zip" and click `Install Plugin`.
5. The tool can now be accessed via the `Consolidate OFDS` button that has appeared in the `Plugins` toolbar.

If any changes are made to the tool in the Github repository you will need to repeat these steps to update your installation.

## Your data

You should start with node and span data for the two networks you want to compare.

The network data need to be in [geoJSON](https://geojson.org/) format compatible with the [Open Fibre Data Standard](https://open-fibre-data-standard.readthedocs.io).

An example of this is; a node network:

```
{
    "type": "FeatureCollection",
    "features":
	[
		{
			"type": "Feature",
			"geometry": {
			    "type": "Point",
			    "coordinates": [
			        40.116275928237194,
			        -3.2187281346824963
			    ]
			},
			"properties": {
			    "id": "f787b3ce-dc40-4d09-ac8a-78ded5811578",
			    "name": "Name of a Node",
			    "status": "operational",
			    ...
			}
		},
		{
			...
		}
	]
}
```

and a span network:

```
{
    "type": "FeatureCollection",
    "features":
	[
		{
		    "type": "Feature",
		    "geometry": {
		        "type": "LineString",
		        "coordinates": [
		            [
		                36.97352465,
		                -1.44771187
		            ],
		            [
		                36.94936105,
		                -1.54839352
		            ],
		            [
		                36.85874756,
		                -1.6692115
		            ]
		        ]
		    },
		    "properties": {
		        "id": "c32e9958-daa9-4b4b-98c8-62f0d260966d",
		        "name": "Name of a Span",
		        "status": "operational",
		        ...
		    },
			{
				...
			}
		}
	]
}
```

To convert OFDS JSON data into geoJSON, [use this conversion tool](https://ofds.cove.opendataservices.coop/). To validate your data against the Open Fibre Data Standard, please [use this validation tool](https://ofds.cove.opendataservices.coop/). To convert data from kml to OFDS [this beta kml2ofds tool](https://github.com/stevesong/kml2ofds) is available.

## Consolidating networks

1. Add your two span and node data files as layers to the project by going to `Layer > Add Layer > Add Vector Layer`.
2. Navigate to your geojson files one at a time under `Source` and press `Add` for each one. Do not adjust the default options, in particular FLATTEN_NESTED_ATTRIBUTES must be set to NO.
3. All four files should now appear in the Layers panel, and appear visually on the Map view.

Tip: To view a map underneath the nodes and spans, go to the Browser panel > `XYZ tiles` and double click `Open Street Map` or other map tiles of your choice. In the Layers panel, make sure the nodes and spans are _above_ the map layer to see them. Adding the map is not necessary for using the tool, but it may make it easier to understand your data.

4. Click `Consolidate OFDS` in the toolbar.
5. Select the layers for the spans and nodes of each network using the dropdown menus in the Select Inputs tab.
6. Change any settings you need (see [settings](#settings)).
7. The tool presents data on nodes and spans which are geographically close to each other, pair by pair, along with a confidence score for how likely they are to be duplicates (see [scoring](#scoring)). The pair being compared will be highlighted in yellow in the tools map inserts. Click `Consolidate` to confirm the pair presented are duplicates and should be merged. Click `Keep Both` to confirm the pair are _not_ duplicates, and should not be merged. If you're not sure, click `Next`. You can use the `Next` and `Previous` buttons to cycle through the comparisons until you have marked them all as either `Consolidate` or `Keep Both`. If there are multiple potential matches, once you have confirmed one match all other potential matches will be automatically assigned to `Keep Both`. If you then try and consolidate one of these pairs the tool will warn you and give you the opportunity to change which of the pairs is consolidated.
8. When you've reviewed all of the nodes comparisons, click `Finish` and repeat step 7 for the spans. The results of your nodes consolidation will be used to select potential span matches, only spans with consolidated nodes will be presented.
9. Once you've reviewed all of the spans comparisons, click `Finish`.
9. Choose where you would like to save the consolidated node and span GeoJSON files.

### Settings

When two features are consolidated, for some fields the data cannot be merged or combined, and only the data from one network will be kept. The network you select for the "Primary Network" will be the one for which data is kept in this case.

You can adjust some thresholds based on the accuracy and completeness of the data you are comparing, and how much oversight you want over the consolidation.

* **Node match radius:** compare nodes within this distance of each other. For data with high precision and accuracy for geographic elements, you may wish to set this number low; for less precise or inaccurate data, a higher number means more comparisons will be made.
* **Ask above (%):** the confidence score above which the tool should prompt you to consolidate. Below this score, pairs are assumed to not be matches, and both are kept in the final output.
* **Auto consolidate above (%):** the confidence score above which the tool should automatically consolidate nodes/spans without prompting.

### Scoring

The tool first compares all pairs of nodes in the two networks which are within the [node match radius](#settings) of each other. It then updates the span data to use the consolidated nodes, and then compares all pairs of spans which have the same start and end nodes.

The **overall confidence score** of the similarity between two features is generated by comparing the values of each field of each feature. Confidence scores for each pair of fields are generated, which are then combined to generate the overall score.

The scoring is based on heuristics, which are derived from:

* the purpose of the field, according to the Open Fibre Data Standard, and
* the type of data the field holds

We use a combination of exact matching, string similarity metrics, list overlaps, and geographical distance to calculate the scores.

When doing a manual comparison, the overall confidence score, and the breakdown of the fields this was derived from, are shown in the interface, alongside the maps displaying the features being compared. You can use this information to make the final decision about whether the two features are the same (and should be consolidated into one) or not (and should both be kept).

### Output

The final output of the tool are geoJSON files saved locally to your computer.

Each feature has an additional `provenance` object, containing the following:

* `wasDerivedFrom`: an array of the ids of the two features that were consolidated.
* `generatedAtTime`: the date or datetime the network was generated.
* `confidence`: a score between 0 and 1 representing how likely the two source features are the same.
* `similarFields`: an array of field names for fields with high similarity scores between the two features.
* `manual`: a boolean value; true means the merge was confirmed manually by the user; false means it was done by the tool.

```
{
    "type": "FeatureCollection",
    "features":
	[
		{
			"type": "Feature",
			"geometry": {
			    "type": "Point",
			    "coordinates": [
			        40.116275928237194,
			        -3.2187281346824963
			    ]
			},
			"properties": {
			    "id": "f787b3ce-dc40-4d09-ac8a-78ded5811578",
			    "name": "Name of a Node",
			    "status": "operational",
			    ...
			},
			"provenance": {
				"wasDerivedFrom": ["f787b3ce-dc40-4d09-ac8a-78ded5811578", "debba101-49e9-4454-a613-f474dcc73f1c"],
				"generatedAtTime": "2024-04-04T14:34:56+00:00",
				"confidence": 0.89,
				"similarFields": ["name", "coordinates", "status"],
				"manual": "true"
			}
		},
		{
			...
		}
	]
}
```
