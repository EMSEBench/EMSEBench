## Commit Message Matters: Investigating Impact and Evolution of Commit Message Quality

This replication package contains data and scripts used in "Commit Message Matters: Investigating Impact and Evolution of Commit Message Quality".

**Dataset:**
  <li>TrainingData.csv</li>
    <ul>
      <li>This dataset is used for training our classifiers. </li>
      <li>It contains 1,597 labeled commit messages. </li>
      <li>label = 0 means a commit message contains "Why and What". </li>
      <li>label = 1 means a commit message contains "Neither Why nor What". </li>
      <li>label = 2 means a commit message contains "No What". </li>
      <li>label = 3 means a commit message contains "No Why".</li>
      <li>new_message1 means a message after preprocessing. </li>
    </ul>

**Hyperparameters.csv:**

This csv contains all selected hyper-parameters from our model training and validation.

**Model_training:**

It contains the necessary code for hyper-parameter tuning, training, and validating our Machine Learning models in this paper.

**Survey:**

It contains the survey results from 93 Apache developers.

**Interview:**

It contains the transcripts recorded from our interviews with 13 OSS developers.

**Preprocessors:**

It contains the preprocessing of commit messages, including the replacement of token in the message, bot commit message detection, and a web crawler for crawling the titles of issues/pull requests.

**Analysis:**

It contains scripts for our (commit-level and file-level) impact and evolution analysis.
