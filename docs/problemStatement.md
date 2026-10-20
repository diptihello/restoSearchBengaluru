# AI-Powered Restaurant Recommendation System (Zomato Use Case)

## 📌 Project Overview
The objective of this project is to build an intelligent, end-to-end **AI-Powered Restaurant Recommendation Service** inspired by Zomato. 

Traditional recommendation systems on food discovery platforms often rely solely on hard database filters (e.g., exact match on cuisine and minimum star rating). While functional, this lacks human-like reasoning, contextual understanding, and personalized explanations. This project bridges that gap by combining **structured tabular restaurant data** with the cognitive and linguistic reasoning of **Large Language Models (LLMs)** to deliver personalized, explainable, and human-like dining recommendations.

---

## 🎯 Objectives
Design and implement an application that:
1. **Captures User Preferences**: Gathers multifaceted user inputs (location, budget constraints, preferred cuisines, minimum ratings, and situational requirements).
2. **Ingests Real-World Data**: Ingests, cleans, and structures real-world restaurant data from Hugging Face.
3. **Applies Hybrid Retrieval**: Employs an integration layer to filter candidate restaurants deterministically before passing them to the LLM.
4. **Leverages LLM Reasoning**: Utilizes an LLM to evaluate, rank, and synthesize personalized rationales explaining *why* each restaurant fits the user's explicit and implicit needs.
5. **Presents Rich Results**: Formats and displays recommendations in an intuitive, engaging, and clear user interface.

---

## 🔄 End-to-End System Workflow

```
[ User Input ] ──► [ Integration & Filtering Layer ] ──► [ Candidate Subset ]
                              │
[ Hugging Face Dataset ] ─────┘
                              │
                              ▼
                  [ LLM Prompt Construction ]
                              │
                              ▼
                  [ LLM Recommendation Engine ]
                  (Ranking + Reasoning + Explanations)
                              │
                              ▼
                  [ User-Facing Output Display ]
```

### 1. Data Ingestion & Preprocessing
* **Dataset Source**: Hugging Face – [`ManikaSaini/zomato-restaurant-recommendation`](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)
* **Ingestion Pipeline**:
  * Download and cache the dataset.
  * Extract and normalize essential attributes:
    * `Restaurant Name`
    * `Location / City / Address`
    * `Cuisines` (comma-separated tags)
    * `Cost / Approximate Cost for two`
    * `Aggregate Rating` & `Rating Text / Votes`
    * `Features` (e.g., Online ordering, Table booking)
  * Handle missing, invalid, or noisy data (e.g., non-numeric ratings, missing cost fields).

### 2. User Preference Input
Collect structured and conversational user inputs:
* **Location**: Target city or neighborhood (e.g., Bangalore, Delhi, Connaught Place, Indiranagar).
* **Budget**: Budget tiers (Low / Pocket-Friendly, Medium / Casual Dining, High / Fine Dining) or approximate price range for two.
* **Cuisine**: Preferred cuisines (e.g., North Indian, Italian, Chinese, Cafe, Street Food).
* **Minimum Rating**: Minimum acceptable customer rating (e.g., 3.5+, 4.0+).
* **Contextual & Situational Preferences**:
  * Dining vibe / occasion (e.g., romantic date, quick bite, family-friendly, business meeting).
  * Dietary or service features (e.g., pure vegetarian, rooftop seating, pet-friendly, late-night dining).

### 3. Integration Layer
The bridge between static data and the LLM:
* **Heuristic Filtering**: Efficiently pre-filters the dataset based on hard constraints (location, base budget range, minimum rating threshold) to narrow candidates to a high-relevance pool (e.g., top 10–25 candidates).
* **Context Serialization**: Transforms candidate records into compact, structured prompt context (JSON or Markdown tables) to minimize token consumption while preserving critical attributes.
* **Prompt Engineering**: Constructs a well-structured prompt that guides the LLM to act as an expert food concierge, preventing hallucinations and enforcing ranking rules.

### 4. Recommendation Engine (LLM Reasoning)
* **Candidate Evaluation**: The LLM evaluates the pre-filtered candidates against the user's specific context.
* **Intelligent Ranking**: Ranks the top recommendations based on alignment with user preferences.
* **Explainability ("Why this fits")**: Generates distinct, persuasive reasoning for each recommended option.
* **Executive Summary**: Generates a quick summary comparing the top picks and highlighting trade-offs (e.g., "Best for Ambiance" vs. "Best Value for Money").

### 5. Output Display
Present the recommendations cleanly with key decision-making information:
* **Restaurant Cards**:
  * **Name**: Restaurant name and overall ranking (#1, #2, #3).
  * **Quick Specs**: Rating, average cost for two, location/area, and key cuisines.
  * **Tailored Explanation**: Clear explanation of why this restaurant matches the user's request.
  * **Highlights / Tags**: Notable features (e.g., "Great outdoor seating", "Must-try pasta", "Quick service").
* **Summary & Direct Takeaway**: A quick concluding remark guiding the user's final decision.

---

## 🛠️ Technology Stack & Architecture

| Layer | Recommended Technologies |
| :--- | :--- |
| **Data Ingestion** | Python, `pandas`, Hugging Face `datasets` |
| **LLM Provider** | Google Gemini API (`gemini-2.5-flash` / `gemini-1.5-pro`) or OpenAI / Anthropic |
| **LLM Orchestration** | LangChain / LlamaIndex or native API integration with structured prompt templates |
| **Application / UI** | Streamlit, Gradio, or FastAPI backend with modern React/Vanilla web frontend |

---

## 🔗 Key References & Resources
* **Dataset**: [Hugging Face: ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)
* **Recommended Video Guide**: [Watch before starting (YouTube Playlist)](https://www.youtube.com/playlist?list=PLfq5z_tJn33A)
