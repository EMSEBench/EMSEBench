# EMSEBench

## An Exploratory Evaluation of Large Language Models Using Empirical Software Engineering Tasks



### Content

- 1. Introduction
- 2. Leaderboard
- 3. Prompt Design
- 4. Dataset Description
- 5. Reproduce Our Work



### 1. Introduction

The auxiliary capabilities and effectiveness of large language models (LLMs) in empirical software engineering (EMSE) tasks have rarely been explored. To fill this gap, in this paper, we evaluate the performance of LLMs by using scenarios of human participation in EMSE tasks, i.e., EMSEBench. We conduct replication experiments using four LLMs (ChatGPT4.0, ERNIE Bot4.0, Gemini3.0, and ChatGLM4.0), evaluating the difference in performance across seven scenarios collected from papers published in top SE venues. In the experiments, we perform three types of prompts, i.e., zero-shot, one-shot, and optimized one-shot. Besides, we leverage the concept of multi-agent workflow to explore the performance improvement and limitations of LLMs.   



This research can facilitate the understanding of the auxiliary role and effectiveness of LLMs in EMSE research.  



### 2. Leaderboard

We list the reproduction accuracy of four LLMs using zero-shot, one-shot, and optimized one-shot prompts in single-agent workflow. For specific task content in each scenario, please refer to our paper. Note that the release date of the evaluated LLMs is before June 2024.



Among these four LLMs, ChatGPT4.0 and ChatGLM4.0 perform the best in reproducing the EMSE tasks without hallucinations. All our experiments are conducted on the official web versions of the large language models. The specific details are shown in the table below. 

**Accuracy of LLMs on EMSEBench in single-agent workflow**

|    Model     | Zero-shot | One-shot | Optimized One-shot | Average | Rank |
| :----------: | :-------: | :------: | :----------------: | :-----: | :--: |
|  ChatGPT4.0  |   62.2    |   60.8   |        64.9        |  62.6   |  1   |
|  ChatGLM4.0  |   67.6    |   62.2   |        56.8        |  62.2   |  2   |
| ERNIE Bot4.0 |   41.9    |   55.4   |        52.7        |  50.0   |  3   |
|  Gemini3.0   |   35.1    |   36.5   |        33.8        |  35.1   |  4   |
|   Average    |   51.7    |   53.7   |        52.1        |         |      |



We also conduct statistics on the LLM/Prompt combinations that achieve the highest accuracy in each scenario and find that zero-shot prompt achieves the highest accuracy the most frequently. The specific details are shown in the table below.

**Statistics of the Combination of Prompt Types and LLMs with the Highest Reproduction Accuracy**

| LLM/Prompt   | Zero-shot | One-shot | Optimized One-shot | Total |
| ------------ | --------- | -------- | ------------------ | ----- |
| ChatGPT4.0   | 2         | 2        | 3                  | 7     |
| ERNIE Bot4.0 | 1         | 2        | 0                  | 3     |
| Gemini3.0    | 0         | 0        | 0                  | 0     |
| ChatGLM4.0   | 2         | 0        | 1                  | 3     |
| Total        | 5         | 4        | 4                  | 13    |

Additionally, we select the best-performing LLMs, ChatGPT4.0 and ChatGLM4.0, with Zero-shot prompt in multi-agent workflow. We conclude that the multi-agent workflow can enhance the performance of LLMs in handling EMSE tasks.



We conduct comparative tests on the combinations of ChatGPT4.0-Single-Agent and ChatGPT3.5-Multi-Agent using zero-shot prompt. The results show that ChatGPT3.5, with the assistance of the multi-agent workflow, can achieve a similar performance as ChatGPT4.0. For more detailed information, please refer to our paper.



### 3. Prompt Design

We follow commonly accepted design specifications in prompt engineering to design corresponding single-agent workflow prompts and multi-agent workflow prompts for each scenario. Single-agent workflow prompts are divided into four parts: Role, Task, Sample, and Output Format. The Sample part only appears in one-shot prompts and optimized one-shot prompts. Multi-agent workflow prompts are based on the Single-agent workflow prompts and include additional parts: Setting and Feedback. An example of a single-agent one-shot prompt is shown below. For multi-agent workflow prompts, please refer to our paper.

```
##Role
Suppose you are a software development engineer.In community-based software development, you need to rely on live-chatting transcripts to discuss emergent bugs/errors you encounter in your daily development tasks.                                

##Task
Now you need to classify the sentences I provide you into:observed behaviors (OB), expected behaviors (EB), steps to reproduce the bug (SR) and others.      

##Sample
To help you understand these four categories, I will provide you with an example of each category.
There are examples.
"i have added all the required jars in my eclipse project but still i am getting this error. _eou_" observed behaviors (OB)
"when trying to edit or save desired capabilities, _eou_"   expected behaviors (EB)
"i have jdk version _version_  _eou_"  steps to reproduce the bug (SR)
"hi  have a problem with ios 13 device. _eou_"  Others                    

tips: "_code_" means code snippet, "_eou_" means the end of a sentence and "_version_" means the version number of a app.                                 

##Output Format
Just give your answer, no explanation required.
If you understand everything I said, please answer Understand.Then I would send the content of live-chatting transcripts.                                     
```



### 4. Dataset Description

```
EMSEBench
  |----Scenario4
  |        |...
  |----Scenario5
  |        |----Dataset
  |        |----Multi-Agent Logs
  |        |----Prompt
  |        |----Single-Agent Logs
  |        |----Evaluation.xlsx
  |        |----Original Data Collection.xlsx
  |        |----Paper.txt
  |----Scenario6...
  |        |...
```

We have collected and organized relevant data for each scenario. Each scenario's corresponding folder contains source data (Dataset), the source scenario paper (Paper), reproduction experiment prompts (Prompt), reproduction experiment logs (Logs), and statistical analysis of reproduction experiment results (Evaluation). Additionally, some scenarios contain data (Original Data Collection) separated from the source data (Dataset) for convenience in data collection and statistics.



### 5. Reproduce Our Work

Our experimental data and logs have been collected in our dataset. For specific scenarios, you can refer to our experimental logs. By inputting the experimental data and prompts in the official web versions of the large language models, you can obtain the reproduction results of the LLM. Please note that the release date of the evaluated LLMs is before June 2024.



