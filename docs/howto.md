---
title: How to guide
layout: home
---

# How to use the OFDS consolidation tool

## Install QGIS and the plugin

The consolidation tool is a [QGIS](https://qgis.org/) plugin. First, follow the [installation instructions for QGIS]() for your operating system. The tool works with QGIS version 3.28 and higher. If you have an older version of QGIS installed, you need to upgrade it.

<!--
To install the plugin, you need an internet connection, but after that it will work offline.

1. Open QGIS. Go to Plugins > Manage and Install Plugins.
2. Search for "OFDS Consolidation Tool" and click "Install Plugin".
-->

The plugin is currently in development beta, and not yet available from the QGIS plugin libraries. To install the plugin for testing, follow the instructions in [Development > Enabling and running the plugin]().

## Your data

You should start with node and span data for the two networks you want to compare.

The network data need to be in [geoJSON]() format compatible with the [Open Fibre Data Standard](https://open-fibre-data-standard.readthedocs.io).

To convert OFDS JSON data into geoJSON, [use this conversion tool](). To convert data from other formats into OFDS, or to validate your data against the Open Fibre Data Standard, please [see these other things]().

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

## Consolidating networks

1. Add your two span and node data files as layers to the project by going to Layer > Add Layer > Add Vector Layer.
2. Navigate to your geojson files one at a time under 'Source' and press 'Add' for each one. They should appear under the Layers list, and appear visually on the map window.
3. Optionally, adjust the colours and thicknesses of each layer by double clicking on each layer in the Layers list.

Tip: To view a map underneath the nodes and spans, go to the Browser window > XYZ tiles and double click Open Street Map or other map tiles of your choice. (TODO: is this the default? How to add maps if there are none?) In the Layers list, make sure the nodes and spans are _above_ the map layer to see them. Adding the map is not necessary for using the tool, but it may make it easier to understand your data.

4. Click "Consolidate OFDS" in the toolbar.
5. Select the layers for the spans and nodes of each network using the dropdown menus in the Select Inputs tab.
6. Change any settings you need (see [settings](#settings)).
7. The tool presents data on nodes and spans which are geographically close to each other, pair by pair, along with a confidence score for how likely they are to be duplicates. Click "Same" to confirm the pair presented are duplicates and should be merged. Click "Not Same" to confirm the pair are _not_ duplicates, and should not be merged. If you're not sure, click "Next". You can use the "Next" and "Previous" buttons to cycle through the comparisons until you have marked them all as either "Same" or "Not Same".
8. When you've reviewed all of the comparisons, click "Finish".
9. TODO: Choose the level of detail you would like in the additional provenance metadata generated with your output(s):
  * None: the output is OFDS conformant geoJSON nodes and spans networks, with no additional provenance metadata.
  * Basic: the output includes a reference to the source nodes/spans for any that were generated from duplicates, the overall confidence score for the match, and whether they were merged by hand or automatically.
  * Detailed: the output includes all the data for each pair of nodes/spans compared, similarity scores for each field, the overall confidence score, and whether duplicate nodes/spans were merged by hand or automatically.
  * Detailed (include non-matches): the same as "Detailed", plus data for nodes/spans which were compared but not merged.
10. Choose where you would like to save the consolidated network JSON files.

### Settings

You can adjust some thresholds based on the accuracy and completeness of the data you are comparing, and how much oversight you want over the consolidation.

* Node match radius: compare nodes within this distance of each other. On data with high precision and accuracy for geographic elements, you may wish to set this number low; for less precise or inaccurate data, a higher number means more comparisons will be made.
* TODO: Primary network: in the event of a match of two similar but not identical nodes/spans, keep the data from this network.
* Ask above (%): the confidence score above which the tool should prompt you to mark a node/span pair as "Same" or "Not Same". Below this score, pairs are assumed to not be matches, and both are kept in the final output.
* Auto consolidate above (%): the confidence score above which the tool should automatically consolidate nodes/spans without prompting.

### Scoring

### Output

The final output of the tool are geoJSON files saved to your computer locally.

If you choose "None" for your provenance data, the structure of the output will be the same as that of the input.

If you choose "Basic", each feature will have an additional `provenance` field:

* `wasDerivedFrom`: array of the ids of the two features that were consolidated.
* `generatedAtTime`: date or datetime the network was generated.
* `confidence`: a score between 0 and 1 representing how likely the two source features are the same.
* `similarFields`: array of field names for fields with high similarity scores between the two features.
* `automatic`: bool; false means the merge was confirmed manually by the user; true means it was done by the tool.

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
				"generatedAtTime": "2024-04-04",
				"confidence": 0.89,
				"similarFields": ["name", "coordinates", "status"],
				"automatic": "false"
			}
		},
		{
			...
		}
	]
}
```

If you choose "Detailed", each feature will have the additional provenance field as above, as well as the confidence scores for each field compared for each feature:

* `similarFieldScores`: an object where the properties are the field names used for comparision, and the values are the similarity scores between 0 and 1 for each. Only includes fields which scored highly.

_And_ the whole network will contain a copy of the source of both original networks for all features which were consolidated:

* `allFieldScores`: an object where the properties are the field names used for comparision, and the values are the similarity scores between 0 and 1 for each.
* `merged`: bool; false means the features were not consolidated together; true means they were.
* `automatic`: the same as this property on individual features in a consolidated network, but note that if `automatic` is `true` and `merged` is `false` it means the tool automatically did not consolidate two features without prompting the user to confirm.

If "include non-matches" is set, the source and scores of both original networks for all features which were _compared_ are included, even if they were not consolidated:

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
				"generatedAtTime": "2024-04-04",
				"confidence": 0.89,
				"similarFieldScores": {"name": 1, "coordinates": 0.8, "status": 1},
				"automatic": "false"
			}
		},
		{
			...
		}
	],
	"comparisons": [
		{
			"features": [
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
					"type": "Feature",
					"geometry": {
					    "type": "Point",
					    "coordinates": [
					        37.07134114614533,
                   			-1.0362943463841985
					    ]
					},
					"properties": {
					    "id": "a35a6d78-e7b6-4125-abb3-ae62489ab370",
					    "name": "A completely different one",
					    "status": "operational",
					    ...
					}
				}
			],
		"confidence": 0.29,
		"allFieldScores": {"name": 0.1, "coordinates": 0.4, "status": 1, "type": 0, "power": 0},
		"merged": "false",
		"automatic": "true"
	]
}
```