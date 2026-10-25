# Graph Report - NextLeap_Zomato_project  (2026-10-25)

## Corpus Check
- 42 files · ~56,266 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .example 1, .parquet 1)

## Summary
- 471 nodes · 952 edges · 21 communities (15 shown, 6 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 90 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `633042b0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- CandidateRestaurant
- get_settings
- pandas
- Phase-Wise Implementation Plan: AI-Powered Restaurant Recommendation System
- Edge Cases & Corner Scenarios: AI-Powered Restaurant Recommendation System
- UserPreferences
- System Architecture: AI-Powered Restaurant Recommendation System
- main.py
- AI-Powered Restaurant Recommendation System (Zomato Use Case)
- AGENTS.md
- app.py
- INSTRUCTIONS.md
- RecommendationService
- 🚀 Deployment Plan: Zomato AI Restaurant Recommendation System
- 🍽️ Zomato AI Restaurant Recommendation System
- deploy
- vercel.json

## God Nodes (most connected - your core abstractions)
1. `UserPreferences` - 55 edges
2. `CandidateRestaurant` - 35 edges
3. `RecommendationResponse` - 31 edges
4. `RecommendationService` - 29 edges
5. `FilterEngine` - 25 edges
6. `GeminiLLMClient` - 19 edges
7. `RestaurantRecommendation` - 19 edges
8. `validate_recommendation_grounding()` - 17 edges
9. `generate_fallback_recommendations()` - 16 edges
10. `CandidateSelector` - 16 edges

## Surprising Connections (you probably didn't know these)
- `Verification & Deliverables` --references--> `RecommendationResponse`  [INFERRED]
  docs/implementation-plan.md → src/llm/schemas.py
- `Action Items` --references--> `UserPreferencesPayload`  [INFERRED]
  docs/implementation-plan.md → src/api/routes.py
- `Action Items` --references--> `RecommendationResponse`  [INFERRED]
  docs/implementation-plan.md → src/llm/schemas.py
- `main()` --uses--> `RecommendationResponse`  [INFERRED]
  frontend/app.py → src/llm/schemas.py
- `fetch_recommendations()` --uses--> `RecommendationResponse`  [INFERRED]
  frontend/components/api_client.py → src/llm/schemas.py

## Import Cycles
- None detected.

## Communities (21 total, 6 thin omitted)

### Community 0 - "CandidateRestaurant"
Cohesion: 0.08
Nodes (18): _extract_candidate_names(), GeminiLLMClient, generate_fallback_recommendations(), _normalize_candidates_to_dicts(), _normalize_name(), validate_recommendation_grounding(), build_recommendation_prompt(), serialize_candidates() (+10 more)

### Community 1 - "get_settings"
Cohesion: 0.29
Nodes (4): main(), get_settings(), Settings, test_settings_loaded()

### Community 2 - "pandas"
Cohesion: 0.08
Nodes (19): fetch_raw_dataset(), get_processed_dataset(), run_pipeline(), clean_boolean(), clean_cost(), clean_cuisines(), clean_location(), clean_rating() (+11 more)

### Community 3 - "Phase-Wise Implementation Plan: AI-Powered Restaurant Recommendation System"
Cohesion: 0.06
Nodes (31): Action Items, Action Items, Action Items, Action Items, Action Items, Action Items, Action Items, Objective (+23 more)

### Community 4 - "Edge Cases & Corner Scenarios: AI-Powered Restaurant Recommendation System"
Cohesion: 0.07
Nodes (26): 1.1 Messy, Incomplete, or Non-Numeric Ratings, 1.2 Erratic Cost Formats & Currency Strings, 1.3 Duplicate Listings and Multi-Branch Outlets, 1.4 Cuisine Inconsistencies & Long Tails, 1. Data Ingestion & Cleaning Edge Cases, 2.1 Impossible / Contradictory Constraints, 2.2 Incomplete or Empty Inputs, 2.3 Adversarial Inputs & Prompt Injections (+18 more)

### Community 5 - "UserPreferences"
Cohesion: 0.09
Nodes (8): CandidateSelector, format_candidate_markdown_table(), compute_cuisine_overlap_vectorized(), FilterEngine, get_budget_range(), TestCandidateSelector, TestFilterEngine, TestPerformanceBenchmark

### Community 6 - "System Architecture: AI-Powered Restaurant Recommendation System"
Cohesion: 0.15
Nodes (12): 1. Executive Summary & Architectural Vision, 2. High-Level System Architecture, 3. End-to-End Sequence Diagram, 4.1. Data Ingestion & Preprocessing Subsystem, 4.2. Deterministic Filtering Subsystem (Stage 1), 4.3. Prompt Engineering & LLM Reasoning Engine (Stage 2), 4. Architectural Layers & Subsystems, 5. Recommended Project Directory Structure (+4 more)

### Community 7 - "main.py"
Cohesion: 0.05
Nodes (8): add_process_time_and_log(), global_exception_handler(), root(), serve_ui(), validation_exception_handler(), TestMetadataEndpoints, TestRecommendationEndpoint, TestSystemEndpoints

### Community 8 - "AI-Powered Restaurant Recommendation System (Zomato Use Case)"
Cohesion: 0.17
Nodes (11): 1. Data Ingestion & Preprocessing, 2. User Preference Input, 3. Integration Layer, 4. Recommendation Engine (LLM Reasoning), 5. Output Display, AI-Powered Restaurant Recommendation System (Zomato Use Case), 🔄 End-to-End System Workflow, 🔗 Key References & Resources (+3 more)

### Community 11 - "app.py"
Cohesion: 0.08
Nodes (11): main(), fetch_meta_options(), fetch_recommendations(), render_empty_state(), render_executive_summary(), render_restaurant_card(), render_sidebar_controls(), get_recommendation_service() (+3 more)

### Community 15 - "RecommendationService"
Cohesion: 0.08
Nodes (10): create_recommendations(), get_health(), get_meta_options(), HealthResponse, MetaOptionsResponse, UserPreferencesPayload, RecommendationService, rec_service() (+2 more)

### Community 16 - "🚀 Deployment Plan: Zomato AI Restaurant Recommendation System"
Cohesion: 0.07
Nodes (26): 1.1 Railway Configuration Files, Approach A: Deploying the Modern Web Client (`stitch_zomato_ai_culinary_concierge`) [Recommended for Vercel], Approach B: Deploying the Streamlit Interface (`frontend/app.py`), 🏗️ Architecture & Deployment Topology, Create `Procfile` (in repository root), Create `railway.json` (in repository root), 🚀 Deployment Plan: Zomato AI Restaurant Recommendation System, Ensure Dataset is Included in Git (+18 more)

### Community 18 - "🍽️ Zomato AI Restaurant Recommendation System"
Cohesion: 0.11
Nodes (17): 1. Prerequisites, 2. Environment Setup, 3. Configure Secrets (.env), 📡 API Endpoints Overview, 🌟 Architectural Vision & Key Features, 🚀 Getting Started, Performance Benchmarks, 🧪 Persona Testing & Benchmarks (Phase 6) (+9 more)

### Community 19 - "deploy"
Cohesion: 0.20
Nodes (9): build, builder, deploy, healthcheckPath, healthcheckTimeout, restartPolicyMaxRetries, restartPolicyType, startCommand (+1 more)

### Community 20 - "vercel.json"
Cohesion: 0.40
Nodes (4): cleanUrls, framework, outputDirectory, rewrites

## Knowledge Gaps
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RecommendationResponse` connect `CandidateRestaurant` to `pandas`, `Phase-Wise Implementation Plan: AI-Powered Restaurant Recommendation System`, `main.py`, `app.py`, `RecommendationService`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `UserPreferences` (e.g. with `GeminiLLMClient` and `generate_fallback_recommendations()`) actually correct?**
  _`UserPreferences` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Should `CandidateRestaurant` be split into smaller, more focused modules?**
  _Cohesion score 0.08105022831050228 - nodes in this community are weakly interconnected._
- **Why does `UserPreferences` connect `CandidateRestaurant` to `pandas`, `app.py`, `UserPreferences`, `RecommendationService`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `CandidateRestaurant` (e.g. with `_extract_candidate_names()` and `GeminiLLMClient`) actually correct?**
  _`CandidateRestaurant` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Should `pandas` be split into smaller, more focused modules?**
  _Cohesion score 0.07831677381648158 - nodes in this community are weakly interconnected._
- **Are the 12 inferred relationships involving `RecommendationResponse` (e.g. with `Action Items` and `Verification & Deliverables`) actually correct?**
  _`RecommendationResponse` has 12 INFERRED edges - model-reasoned connections that need verification._