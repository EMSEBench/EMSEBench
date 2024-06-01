# README

To obtain github data directly, run

```
chmod +x ./script.sh
script.sh
```

1. to collect related issues from tensorflow repository:

   ```
   curl >tflite-issues-1.json 'https://api.github.com/search/issues?q=type:issue+repo:tensorflow/tensorflow+label:comp:lite%20-label:type:build/install%20-label:type:bug%20-label:type:feature%20-label:type:docs-bug%20-label:type:docs-feature%20-label:stalled%20-label:%22stat:awaiting%20response%22+state:closed&sort=created&per_page=100&page=1'
   ```

2. to collect related issues from coreml-tools repository:

   ```
   curl >coreml-issues-1.json 'https://api.github.com/search/issues?q=type:issue+repo:apple/coremltools+-label:bug+state:closed&sort=created+type:issue&per_page=100&page=1'
   ```

3. to extract issue url from json file:

   ```
   python preprocess.py $json_file_path $url_file_path
   ```


