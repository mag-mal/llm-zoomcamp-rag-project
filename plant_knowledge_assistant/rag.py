import json
from time import time
import ingest
from qdrant_client import QdrantClient, models
from groq import Groq
from dotenv import load_dotenv
import os

# Load environment variables first
load_dotenv()
groq_api_key = os.getenv('GROQ_API_KEY')
client = ingest.main()

def multi_stage_search(query, limit = 5):
    """
    Perform a hybrid multi-stage search combining BM25 keyword search 
    with semantic prefetch using Jina embeddings. 
    Prefetch retrieves 10× the requested results for improved reranking, 
    then returns the top matches with payloads.

    Args:
        query (str): Search query text.
        limit (int, optional): Number of final results to return. Defaults to 5.

    Returns:
        list[models.ScoredPoint]: Ranked search results with payload data.
    """
    # Only ingest if collection doesn't exist or is empty
    results = client.query_points(
        collection_name=ingest.COLLECTION_NAME,
        prefetch=[
            models.Prefetch(
                query=models.Document(
                    text=query,
                    model="jinaai/jina-embeddings-v2-small-en",
                ),
                using="jina-small",
                # Prefetch ten times more results, then
                # expected to return, so we can really rerank
                limit=(10 * limit),
            ),
        ],
        query=models.Document(
            text=query,
            model="Qdrant/bm25", 
        ),
        using="bm25",
        limit=limit,
        with_payload=True,
    )

    return results


prompt_template1 = """
You are a knowledgeable and friendly plant specialist.
Your expertise covers house plants, their care and toxicity.
Answer the QUESTION based on the CONTEXT from our plants database.
Use only the facts from the CONTEXT when answering the QUESTION.

QUESTION: {question}

CONTEXT:
{context}
""".strip()

entry_template1 = """
plant name: {name}
summary: {summary}
cultivation: {cultivation}
toxicity: {toxicity}
""".strip()

def build_prompt(query, search_results, prompt_template, entry_template):
    context = ""
    
    for doc in search_results:
        context = context + entry_template.format(**doc) + "\n\n"

    prompt = prompt_template.format(question=query, context=context).strip()
    return prompt


def gpt_oss_answer(content, model="openai/gpt-oss-20b"):
  """
    Generate GPT-OSS model response from Groq Api.

    Args:
        content (str): Prompt for the model.
        model (str, optional): Model name. Defaults to "openai/gpt-oss-20b".

    Returns:
        str: Concatenated response text.
  """
  client = Groq(api_key=groq_api_key)
  completion = client.chat.completions.create(
      model=model,
      messages=[
        {
          "role": "system",
          "content": content
        }
      ],
      temperature=1,
      max_completion_tokens=8192,
      top_p=1,
      reasoning_effort="medium",
      stream=True,
      stop=None
  )
  joined_answer = ''
  
  for chunk in completion:

      chunk_answer = chunk.choices[0].delta.content or ""
      joined_answer = joined_answer + chunk_answer
    
  return joined_answer



llm_judge_prompt = """
You are an expert evaluator for a RAG system.
Your task is to analyze the relevance of the generated answer to the given question.
Based on the relevance of the generated answer, you will classify it
as "NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT".

Here is the data for evaluation:

Question: {question}
Generated Answer: {answer_llm}

Please analyze the content and context of the generated answer in relation to the question
and provide your evaluation in parsable JSON without using code blocks:

{{
  "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
  "Explanation": "[Provide a brief explanation for your evaluation]"
}}
""".strip()


def evaluate_relevance(question, answer):
    prompt = llm_judge_prompt.format(question=question, answer_llm=answer)
    evaluation = gpt_oss_answer(prompt)
    try:
        json_eval = json.loads(evaluation)
        return json_eval
    except json.JSONDecodeError:
        result = {"Relevance": "UNKNOWN", "Explanation": "Failed to parse evaluation"}
        return result


def rag_groq(query, prompt_template, entry_template):
    """
    Run RAG with Groq GPT-OSS model.

    Args:
        query (str): User query to answer.
        prompt_template (str): Template for constructing the full prompt.
        entry_template (str): Template for formatting retrieved entries.

    Returns:
        str: Model-generated answer.
    """
    t0 = time()
    search_results = multi_stage_search(query)
    search_results_list = []

    for i in search_results.points:

        search_results_list.append(i.payload)

    prompt = build_prompt(query, search_results_list, prompt_template, entry_template)
    answer = gpt_oss_answer(prompt)

    relevance = evaluate_relevance(query, answer)
    t1 = time()
    took = t1 - t0

    answer_data = {
        "answer": answer,
        #"model_used": model,
        "response_time": took,
        "relevance": relevance.get("Relevance", "UNKNOWN"),
        "relevance_explanation": relevance.get(
            "Explanation", "Failed to parse evaluation"
        ),
    }
    return answer_data