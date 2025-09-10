# Plant Knowledge Assistant
![Chatbot Screenshot](images/plant_knowledge_assistant.png)
## Problem Description

Houseplants are more than just decorative elements — they enhance indoor spaces by improving air quality, reducing stress, and creating a more welcoming environment. Their presence has been shown to promote emotional well-being and even boost productivity. Despite their benefits, plant owners often face several challenges:

- **Identifying care needs** – Each plant species has unique requirements for light, water, temperature, and soil, and this information isn’t always readily available.  
- **Understanding toxicity** – Many common houseplants can be harmful to pets, yet toxicity details are often missing or hard to find.  
- **Finding reliable information** – Accurate plant care advice is scattered across multiple sources, making it difficult and time-consuming to get clear answers.

My project addresses these problems through the development of an intelligent **Retrieval-Augmented Generation (RAG)** application, functioning as a **personal indoor plant assistant**. 
By combining a structured plant database with a conversational AI interface, users can ask natural-language questions such as:

- the care requirements of a specific plant,
- whether a plant is safe for pets,
- the plant’s origin and ideal growing conditions, or
- recommendations for plants that meet certain criteria (e.g., low-light plants safe for dogs).

The system then provides clear, concise, and factually grounded answers.
This ensures that plant owners have **instant access to accurate, relevant, and easy-to-understand guidance**, enabling them to care for their plants more confidently and make informed decisions that keep both their plants and pets healthy.

## Retrieval flow

The **Plant Knowledge Assistant** is built as a **RAG-powered chatbot** (both a knowledge base and an LLM are used in the flow):

- **Retrieval Step (searching in knowledge base)** – When a user asks a question (e.g., *"Which plants are safe for cats?"*), the system searches the dataset for relevant entries.  
- **Augmentation Step (building prompt)** – Retrieved information is combined into a context package for the AI model.  
- **Generation Step (LLM)** – The AI produces a conversational, accurate, and user-friendly answer.  


## Data Description

The dataset contains **197 records**, each representing a plant species with detailed information, including:  
- **`name`** – The scientific name of the plant.  
- **`summary`** – Background information, including origin, appearance, and key characteristics.  
- **`cultivation`** – Care instructions such as watering frequency, light requirements, temperature tolerance, and propagation methods. This
- **`toxicity`** – Notes on whether the plant is toxic to pets or humans.  

Example entry:
```json
{
  "name": "Monstera deliciosa",
  "summary": "Monstera deliciosa, the Swiss cheese plant or split-leaf philodendron is a species of flowering plant. The common name "Swiss cheese plant" is also used for the related species from the same genus, Monstera adansonii. The common name "split-leaf philodendron" is also used for the species Thaumatophyllum bipinnatifidum, although neither species is in the genus Philodendron. Monstera deliciosa is native to tropical forests of southern Mexico, south to Panama. It has been introduced to many tropical areas, and has become a mildly invasive species in Hawaii, Seychelles, Ascension Island and the Society Islands. It is very widely grown in temperate zones as a houseplant. Although the plant contains insoluble calcium oxalate crystals, which cause a needlelike sensation when touched, the ripe fruit is edible.",
  "cultivation": "Monstera deliciosa is commonly grown outdoors as an ornamental plant in the tropics and subtropics. The plant requires a lot of space and a rich and loose soil (ideally garden soil and compost in equal parts). If it grows in the ground it is better to plant it near a tree, where it can climb, if not against a trellis. It is a "moderately greedy plant," in that it needs to be watered just to keep the soil slightly moist. Its hardiness is 11 (that is to say the coldest at −1 °C or 30 °F). It cannot withstand these temperatures for more than a few hours, but it can live outside in certain temperate regions (Mediterranean coast, Brittany). A steady minimum temperature of at least 13–15 °C (55–59 °F) is preferable, allowing continuous growth. Growth ceases below 10 °C (50 °F) and it is killed by frost. It needs very bright exposure, but not full sun. Forcing a M. deliciosa to flower outside of its typical tropical habitat proves to be difficult. Specific conditions need to be met for the plant to flower. However, in its tropical and subtropical habitat, the plant flowers easily. In ideal conditions it flowers about three years after planting. The plant can be propagated by taking cuttings of a mature plant or by air layering.",
  "toxicity": "Monstera deliciosa is moderately toxic to both cats and dogs because it contains insoluble calcium oxalate crystals (needle-like). This crystal may cause injury to the mouth, tongue, and digestive tract. It also causes dermatitis by direct contact with cat and dog skin."
}
```

### Data generation
I gathered structured information about house plants from Wikipedia webpage: https://en.wikipedia.org/wiki/Category:House_plants. 
The results are here:

* Dataset: data/plants_data.csv
* Notebook: notebooks/getting_data.ipynb

My code is divided into two main stages:

**1. Collecting Plant Names from the Category Page**

* The code sends a request to the Wikipedia category “House plants” page.

* It uses BeautifulSoup to parse the HTML and extract the titles of all pages (plant names) listed under that category.


**2. Retrieving Detailed Plant Information**

* For each plant name, the wikipedia Python library is used to fetch the plant’s Wikipedia page.

* The code retrieves a short summary of the plant and searches the full page content for sections on Cultivation (if available) and Toxicity (if available) using regular expressions.


## Retrieval evaluation
To evaluate search results I created ground truth retrieval.
* Dataset: data/ground-truth-retrieval-5q.csv
* Notebook: notebooks/generating_ground_truth_dataset.ipynb

Using plant records as input, it creates five relevant, self-contained questions per plant (skipping missing data), then flattens results into a pandas DataFrame of `(id, question)` pairs for training or evaluation.


The table below shows the evaluation results of different search methods based on **Hit Rate**, **Recall at First Position**, and **Mean Reciprocal Rank (MRR)**.  
Higher values indicate better performance across these metrics. The **hybrid search approach** achieves the best overall results.  

| Method                      | Hit Rate | Recall @ First Pos | MRR     |
|-----------------------------|----------|--------------------|---------|
| minsearch                   | 0.895 | 0.822           | 0.848|
| vector_search_tfidf_svd     | 0.922 | 0.801           | 0.853|
| vector_search_jina_emb_metrics | 0.928 | 0.861        | 0.887|
| hybrid_search_metrics       | 0.941 | 0.871           | 0.900|


## LLM evaluation
To evaluate LLM answer I chceck 2 models: 
* openai/gpt-oss-20b with groq api https://console.groq.com with 1000 free requests for this model
* gemini-2.5-flash-lite with gemini api

For the first one I used groq api with 1000 free requests for this model: https://console.groq.com

The table below shows the proportion of responses judged as **RELEVANT**, **PARTLY_RELEVANT**, or **NON_RELEVANT** for different models and prompts (200 samples, 7-shot).  The best results were obtained with GPT-OSS and prompt1.

| Model / Prompt                  | RELEVANT | PARTLY_RELEVANT | NON_RELEVANT |
|---------------------------------|----------|-----------------|--------------|
| GPT OSS PROMPT1 (200, 7)        | 0.905    | 0.085           | 0.010        |
| GPT OSS PROMPT2 (200, 7)        | 0.830    | 0.130           | 0.040        |
| GEMINI FLASH 2.5 LITE PROMPT1 (200, 7) | 0.705    | 0.255           | 0.040        |
| GEMINI FLASH 2.5 LITE PROMPT2 (200, 7) | 0.670    | 0.230           | 0.100        |


## Inference

I used Flask app provides for interacting with the RAG system:

- **`POST /ask`** – Submit a question and receive an answer from the RAG pipeline.  
  Returns a unique `conversation_id` along with the question, answer and timestamp.  

- **`POST /feedback`** – Submit feedback (`+1` or `-1`) for a given `conversation_id`.  
  Useful for tracking performance and improving the system over time.  

- **`GET /health`** – Simple health check endpoint to verify the service is running.  

Conversations are stored in database with fields for `conversation_id`, `question`, `answer`, `response_time`, `relevance`, `relevance_explanation`, `timestamp`, and optional `feedback`. 
Feedback is stored in database with fields for `conversation_id` and  `feedback`.

## Ingestion pipeline
I built python script [ingest.py](ingest.py) which prepares the plant dataset for use in the RAG pipeline. 
It connects to Qdrant, creates a collection with both dense embeddings (Jina) for semantic search and sparse embeddings (BM25) for keyword matching, and converts each row of the dataset into a vector point with metadata. Once ingested, the data can be efficiently retrieved and combined with a language model during question answering.


## Containerization & Reproducibility

### Starting database

Before the application starts for the first time, the database needs to be initialized.

```bash
docker-compose up postgres
```
```bash
pipenv shell

cd plant_knowledge_assistant

export POSTGRES_HOST=localhost
python db_prep.py
````
To check the content of the database, use pgcli (already installed with pipenv):
```bash
pipenv run pgcli -h localhost -U your_username -d course_assistant -W
```

And select from this table:
```bash
select * from conversations;
```

### Environment
For dependency management, we use pipenv, so you need to install it:

```bash
pip install pipenv
```
Once installed, you can install the app dependencies:

```bash
pipenv install --dev
```

Then run application:

### Running with docker
The easiest way to run application is using docker-compose:

```bash
docker-compose up 
````

### Running the application locally

If you want to run the application locally, start only postres, grafana and qdrant:

```bash
docker-compose up postgres grafana qdrant
````
If you previously started all applications with docker-compose up, you need to stop the app:

```bash
docker-compose stop app
```

```bash
pipenv shell
cd plant_knowledge_assistant
export POSTGRES_HOST=localhost
export QDRANT_URL=http://localhost:6333
python app.py
```

### Running with docker without Compose

```bash
docker-compose up postgres grafana qdrant
````
If you previously started all applications with docker-compose up, you need to stop the app:

```bash
docker-compose stop app
```
Build an image:
```bash
docker build -t plant-knowledge-assistant .
```
```bash
docker run -it --rm \
    --network project_plant-knowledge-assistant \
    --env-file=".env" \
    -e DATA_PATH="data/plants_data.csv" \
    -e GROQ_API_KEY=your_api_key \
    -e QDRANT_URL="http://qdrant:6333" \
    -p 5000:5000 \
    plant-knowledge-assistant
```

## Sending requests:

### Using requests
When the application is running, you can use requests to send questions—use test.py for testing it:
```bash
pipenv run python test.py
```
It will pick a random question from the ground truth dataset and send it to the app.

### Using curl

If you want to ask question to THE Plant knowledge assistant you can just put below command in your terminal. 

```bash
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What plants are safe for cats?"}'
```
Answer:
```json
{
  "answer": "**Answer**\n\nYes\u2014Monstera plants can be toxic to pets.  \n- **Monstera deliciosa** (the Swiss\u2011cheese plant) is **moderately toxic to cats and dogs** because it contains insoluble calcium oxalate crystals that can irritate the mouth, tongue, digestive tract, and skin.  \n- For **Monstera adansonii** and other Monstera species, the database does not provide toxicity information, so no definitive statement can be made about those specific species.  \n\nIf you have pets that might chew on or lick a Monstera, it\u2019s safest to keep the plant out of reach.",
  "conversation_id": "dc27df41-5cba-4be3-a2b5-0a979460d99b",
  "question": "Is monstera toxic for pets?",
  "timestamp": "2025-08-25T09:07:01.084322"
}
```

Sending feedback:
```bash
  curl -X POST http://localhost:5000/feedback \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "dc27df41-5cba-4be3-a2b5-0a979460d99b", "feedback": 1}'
```

```json
Answer:
{
  "conversation_id": "dc27df41-5cba-4be3-a2b5-0a979460d99b",
  "feedback": 1,
  "message": "Feedback received successfully"
}
```

## 📊 Monitoring

The app is monitored with **Grafana** connected to **PostgreSQL**, which stores conversation logs and feedback.  

### 🔍 Dashboard Details

- **Last 10 Questions (Table)** – recent user queries with answers and relevance.  
- **Questions Over Time (Time Series)** – query volume trend.  
- **Questions per Relevance per Hour (Bar Chart)** – relevance distribution by time.  
- **Questions per Feedback per Hour (Bar Chart)** – positive vs. negative feedback per hour.  
- **Feedback Counts (%) (Pie Chart)** – overall thumbs up/down ratio.  
- **Relevance Counts (%) (Pie Chart)** – share of relevant vs. non-relevant answers.  
- **Response Time (Time Series)** – AI latency monitoring.  

⏱ Dashboard refreshes every **30s** for near real-time monitoring.  
![Chatbot Screenshot](images/image1.png)
![Chatbot Screenshot](images/image2.png)
![Chatbot Screenshot](images/image3.png)

