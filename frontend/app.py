"""Main Streamlit application for Tomato AI Restaurant Recommendation System."""

import sys
from pathlib import Path

# Add project root to path for direct imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from frontend.components.api_client import fetch_meta_options, fetch_recommendations
from frontend.components.cards import (
    render_empty_state,
    render_executive_summary,
    render_restaurant_card,
)
from frontend.components.sidebar import render_sidebar_controls
from src.llm.schemas import RecommendationResponse

# 1. Page Configuration
st.set_page_config(
    page_title="Tomato AI - Restaurant Concierge",
    page_icon="🍅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Custom CSS styling for Aesthetic White Theme look and feel
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: 'Outfit', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: #F8FAFC !important;
    color: #0F172A !important;
}

[data-testid="stAppViewContainer"] > .main {
    background: radial-gradient(circle at 10% 8%, rgba(255, 75, 75, 0.04) 0%, transparent 40%),
                radial-gradient(circle at 92% 92%, rgba(245, 158, 11, 0.03) 0%, transparent 35%),
                #F8FAFC !important;
}

header[data-testid="stHeader"] {
    background-color: transparent !important;
}

[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
    box-shadow: 2px 0 10px rgba(0, 0, 0, 0.02) !important;
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] span {
    color: #1E293B !important;
}

/* Hero Section */
.hero-container {
    background: linear-gradient(135deg, #FFFFFF 0%, #FFF5F5 50%, #FFF1F2 100%);
    border: 1px solid #FFE4E6;
    border-radius: 20px;
    padding: 34px 38px;
    margin-bottom: 28px;
    color: #0F172A;
    box-shadow: 0 10px 30px -5px rgba(226, 55, 68, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
    position: relative;
    overflow: hidden;
}

.hero-container::after {
    content: "";
    position: absolute;
    top: -40px;
    right: -40px;
    width: 180px;
    height: 180px;
    background: radial-gradient(circle, rgba(255, 77, 77, 0.12) 0%, transparent 70%);
    pointer-events: none;
}

.hero-badge {
    background: linear-gradient(135deg, #FF4343 0%, #E23744 100%);
    color: #FFFFFF;
    font-size: 0.74rem;
    font-weight: 800;
    letter-spacing: 1.2px;
    padding: 5px 14px;
    border-radius: 9999px;
    display: inline-block;
    margin-bottom: 12px;
    text-transform: uppercase;
    box-shadow: 0 4px 12px rgba(226, 55, 68, 0.28);
}

.hero-title {
    font-size: 2.3rem;
    font-weight: 800;
    margin: 0 0 10px 0;
    letter-spacing: -0.8px;
    line-height: 1.2;
    color: #0F172A;
}

.hero-subtitle {
    font-size: 1.05rem;
    color: #475569;
    margin: 0;
    max-width: 740px;
    line-height: 1.6;
}

/* Feature pill */
.architecture-pill {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 6px 14px;
    font-size: 0.8rem;
    font-weight: 600;
    color: #334155;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-top: 16px;
    margin-right: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
}

/* Submit CTA button */
button[kind="primary"] {
    background: linear-gradient(135deg, #FF4343 0%, #E23744 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    padding: 0.6rem 1.2rem !important;
    box-shadow: 0 4px 16px rgba(226, 55, 68, 0.32) !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

button[kind="primary"]:hover {
    box-shadow: 0 6px 22px rgba(226, 55, 68, 0.45) !important;
    transform: translateY(-1px) !important;
}

/* Custom expanders and inputs */
div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 10px !important;
    color: #0F172A !important;
}

div[data-baseweb="input"] input {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 10px !important;
    color: #0F172A !important;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def main():
    # 3. Load dynamic dropdown metadata
    meta_options = fetch_meta_options()

    # 4. Render Sidebar and capture submitted preferences
    payload, is_submitted = render_sidebar_controls(meta_options)

    # 5. Main Hero Banner
    st.markdown(
        """
        <div class="hero-container">
            <span class="hero-badge">🍅 TOMATO AI CONCIERGE • TWO-STAGE ENGINE</span>
            <h1 class="hero-title">Where Taste Meets Intelligence</h1>
            <p class="hero-subtitle">
                Hyper-personalized Bangalore dining recommendations combining sub-10ms dataset retrieval (Stage 1) 
                with Google Gemini situational reasoning and explainability (Stage 2).
            </p>
            <div>
                <span class="architecture-pill">⚡ Fast In-Memory Parquet Filtering</span>
                <span class="architecture-pill">🧠 Google Gemini 3.8 Flash Reasoning</span>
                <span class="architecture-pill">🛡️ Strict Anti-Hallucination Guardrails</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 6. Handle Form Submission
    if is_submitted and payload:
        with st.spinner("🤖 Filtering 12,000+ restaurants & consulting Gemini AI for tailored rationales..."):
            rec_response, error_msg, is_direct = fetch_recommendations(payload)

            if error_msg:
                st.error(f"⚠️ {error_msg}")
            elif rec_response:
                st.session_state["current_recommendations"] = rec_response.model_dump()
                st.session_state["last_query"] = payload
                st.toast("✨ Recommendations ready!", icon="🍅")

    # 7. Render Recommendation Results
    if "current_recommendations" in st.session_state:
        rec_data = st.session_state["current_recommendations"]
        rec_response = RecommendationResponse.model_validate(rec_data)

        if not rec_response.recommendations:
            render_empty_state()
        else:
            # Render Executive Summary
            render_executive_summary(
                summary=rec_response.executive_summary,
                is_fallback=rec_response.is_fallback,
                total_found=len(rec_response.recommendations),
            )

            st.markdown("### 🌟 Top Recommended Spots")

            # Render Ranked Restaurant Cards
            for idx, rec in enumerate(rec_response.recommendations, start=1):
                render_restaurant_card(rec, index=idx)

    else:
        # Welcome State / Feature Walkthrough
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 18px; padding: 32px 36px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02);">
                <h3 style="margin-top: 0; color: #0F172A; font-size: 1.35rem; font-weight: 700;">👋 Welcome to Tomato AI Culinary Concierge</h3>
                <p style="color: #64748B; font-size: 1rem; line-height: 1.6;">
                    Customize your dining preferences using the <strong style="color: #0F172A;">sidebar on the left</strong> to generate bespoke recommendations.
                </p>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 18px; margin-top: 22px;">
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                        <div style="font-size: 1.6rem; margin-bottom: 8px;">📍</div>
                        <strong style="color: #0F172A; font-size: 1rem;">1. Choose Locality & Budget</strong>
                        <p style="color: #64748B; font-size: 0.88rem; margin: 6px 0 0 0; line-height: 1.5;">
                            Target specific Bangalore neighborhoods like Indiranagar, Koramangala, or Whitefield.
                        </p>
                    </div>
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                        <div style="font-size: 1.6rem; margin-bottom: 8px;">🎭</div>
                        <strong style="color: #0F172A; font-size: 1rem;">2. Tell Us Your Vibe or Occasion</strong>
                        <p style="color: #64748B; font-size: 0.88rem; margin: 6px 0 0 0; line-height: 1.5;">
                            Whether it's a romantic candlelit date, quick work lunch, or family reunion dinner.
                        </p>
                    </div>
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                        <div style="font-size: 1.6rem; margin-bottom: 8px;">💡</div>
                        <strong style="color: #0F172A; font-size: 1rem;">3. Get Transparent Explanations</strong>
                        <p style="color: #64748B; font-size: 0.88rem; margin: 6px 0 0 0; line-height: 1.5;">
                            Receive bespoke "Why We Recommend This" justifications tailored to your situation.
                        </p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
