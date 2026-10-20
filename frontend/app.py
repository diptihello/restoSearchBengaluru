"""Main Streamlit application for AI-Powered Restaurant Recommendation System."""

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
    page_title="Zomato AI - Restaurant Concierge",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Custom CSS styling for Stitch dark theme look and feel
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: 'Outfit', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: #0B0F19 !important;
    color: #F8FAFC !important;
}

[data-testid="stSidebar"] {
    background-color: #0F1523 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
}

/* Hero Section */
.hero-container {
    background: linear-gradient(135deg, rgba(19, 28, 46, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 30px 36px;
    margin-bottom: 28px;
    color: white;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.45);
    position: relative;
    overflow: hidden;
}

.hero-badge {
    background: linear-gradient(to right, #B8232F, #FF4757);
    color: white;
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 1px;
    padding: 4px 12px;
    border-radius: 20px;
    display: inline-block;
    margin-bottom: 12px;
    text-transform: uppercase;
    box-shadow: 0 0 15px rgba(226, 55, 68, 0.4);
}

.hero-title {
    font-size: 2.2rem;
    font-weight: 800;
    margin: 0 0 10px 0;
    letter-spacing: -0.5px;
    line-height: 1.2;
    color: #FFFFFF;
}

.hero-subtitle {
    font-size: 1.05rem;
    color: #94A3B8;
    margin: 0;
    max-width: 720px;
    line-height: 1.5;
}

/* Feature pill */
.architecture-pill {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 0.8rem;
    color: #CBD5E1;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-top: 14px;
    margin-right: 8px;
}

/* Quick preset buttons */
div[data-testid="stHorizontalBlock"] button {
    border-radius: 12px;
    background-color: #131C2E !important;
    color: #CBD5E1 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}
div[data-testid="stHorizontalBlock"] button:hover {
    border-color: #E23744 !important;
    color: #FFFFFF !important;
}

/* Submit button */
button[kind="primary"] {
    background: linear-gradient(to right, #E23744, #FF4757) !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    box-shadow: 0 0 20px rgba(226, 55, 68, 0.4) !important;
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
            <span class="hero-badge">AI CONCIERGE 2.0 • TWO-STAGE ENGINE</span>
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
                st.toast("✨ Recommendations ready!", icon="🍽️")

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
            <div style="background: rgba(19, 28, 46, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 30px; box-shadow: 0 12px 36px rgba(0, 0, 0, 0.35);">
                <h3 style="margin-top: 0; color: #FFFFFF; font-size: 1.35rem; font-weight: 700;">👋 Welcome to Zomato AI Culinary Concierge</h3>
                <p style="color: #94A3B8; font-size: 1rem; line-height: 1.6;">
                    Customize your dining preferences using the <strong style="color: #F8FAFC;">sidebar on the left</strong> to generate bespoke recommendations.
                </p>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 18px; margin-top: 20px;">
                    <div style="background: rgba(11, 15, 25, 0.75); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px; padding: 18px;">
                        <div style="font-size: 1.5rem; margin-bottom: 8px;">📍</div>
                        <strong style="color: #F8FAFC;">1. Choose Locality & Budget</strong>
                        <p style="color: #94A3B8; font-size: 0.88rem; margin: 6px 0 0 0;">
                            Target specific Bangalore neighborhoods like Indiranagar, Koramangala, or Whitefield.
                        </p>
                    </div>
                    <div style="background: rgba(11, 15, 25, 0.75); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px; padding: 18px;">
                        <div style="font-size: 1.5rem; margin-bottom: 8px;">🎭</div>
                        <strong style="color: #F8FAFC;">2. Tell Us Your Vibe or Occasion</strong>
                        <p style="color: #94A3B8; font-size: 0.88rem; margin: 6px 0 0 0;">
                            Whether it's a romantic candlelit date, quick work lunch, or family reunion dinner.
                        </p>
                    </div>
                    <div style="background: rgba(11, 15, 25, 0.75); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px; padding: 18px;">
                        <div style="font-size: 1.5rem; margin-bottom: 8px;">💡</div>
                        <strong style="color: #F8FAFC;">3. Get Transparent Explanations</strong>
                        <p style="color: #94A3B8; font-size: 0.88rem; margin: 6px 0 0 0;">
                            Receive bespoke "Why Gemini Picked This" justifications tailored to your situation.
                        </p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
