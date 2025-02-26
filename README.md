TODO:

- pass embed model into vector db indexer
- use sentence splitter, define overlap, chunk size
- use low level index by creating node, parsers and node id and have response include th node id and text
- use low level retriever, query engine by defining similarity score, etc
- use llama indexer evalution and ragas together, retriever evaluation will use sythentic dataset to generate offline eval dataset, and for online we will use faithfullness and query/ sythentic generation for generate online evaluation,
- create seperate script for online and offline eval; for offline eval, create a report,
- for online, append and add to a csv or other file to save and report online eval, and add a dashbaord to include it later, if time allowes,
- if time further allows, look into the eval part to use localhost arize and other dashboard to allow for human feedback and other dashborad to be seen, see llamaindex document
- manually use open ai to interprete chart tables into text and append them into text embedding
- use open source multi modal llm e.g. qwen vl model?  to do the above step
