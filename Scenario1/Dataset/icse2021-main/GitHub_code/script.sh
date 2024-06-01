#!/bin/bash

#collect related issues from tensorflow repository

current_page=1

tflite_max_page=9 #depend on total_count of issues

while (($current_page < $tflite_max_page))
do
	curl >tflite-issues-${current_page}.json 'https://api.github.com/search/issues?q=type:issue+repo:tensorflow/tensorflow+label:comp:lite%20-label:type:build/install%20-label:type:bug%20-label:type:feature%20-label:type:docs-bug%20-label:type:docs-feature%20-label:stalled%20-label:%22stat:awaiting%20response%22+state:closed&sort=created&per_page=100&page='"$current_page"
	python preprocess.py tflite-issues-${current_page}.json tflite-issues.txt
	let current_page++
done

current_page=1

coreml_max_page=3 #depend on total_count of issues

while (($current_page < $coreml_max_page))
do
	curl >coreml-issues-${current_page}.json 'https://api.github.com/search/issues?q=type:issue+repo:apple/coremltools+-label:bug+state:closed&sort=created+type:issue&per_page=100&page='"$current_page"
	python preprocess.py coreml-issues-${current_page}.json coreml-issues.txt
	let current_page++
done