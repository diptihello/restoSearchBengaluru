"""UI card rendering components for Streamlit frontend with Aesthetic White Theme."""

import textwrap
import streamlit as st
from src.llm.schemas import RestaurantRecommendation


def render_executive_summary(summary: str, is_fallback: bool = False, total_found: int = 0):
    """Render an executive summary card at the top of the recommendation results with an aesthetic white design."""
    badge_label = "⚡ HEURISTIC FALLBACK" if is_fallback else "✨ GEMINI AI CURATED"
    badge_bg = "#FEF3C7" if is_fallback else "#FAF5FF"
    badge_color = "#B45309" if is_fallback else "#7E22CE"
    badge_border = "#FDE68A" if is_fallback else "#E9D5FF"

    card_html = textwrap.dedent(f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid #E23744; border-radius: 16px; padding: 22px 26px; margin-bottom: 25px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="width: 34px; height: 34px; border-radius: 10px; background: #FFF1F2; border: 1px solid #FFE4E6; display: flex; align-items: center; justify-content: center; font-size: 1.1rem;">🎯</div>
                    <span style="font-weight: 700; font-size: 1.18rem; color: #0F172A; letter-spacing: -0.3px;">Concierge Executive Summary</span>
                </div>
                <span style="background: {badge_bg}; color: {badge_color}; border: 1px solid {badge_border}; font-size: 0.74rem; font-weight: 700; font-family: monospace; letter-spacing: 0.5px; padding: 4px 12px; border-radius: 20px;">{badge_label}</span>
            </div>
            <p style="color: #334155; font-size: 1.02rem; line-height: 1.65; margin: 0; font-weight: 450;">{summary}</p>
        </div>
    """).strip()

    st.markdown(card_html, unsafe_allow_html=True)


def render_restaurant_card(rec: RestaurantRecommendation, index: int = 1):
    """Render an individual ranked restaurant recommendation card matching aesthetic white theme."""
    # Rank styling
    if rec.rank == 1:
        rank_border = "#F59E0B"
        medal = "🥇"
        rank_label = "#1 TOP MATCH"
        rank_bg = "#FEF3C7"
        rank_color = "#92400E"
    elif rec.rank == 2:
        rank_border = "#94A3B8"
        medal = "🥈"
        rank_label = "#2 GREAT MATCH"
        rank_bg = "#F1F5F9"
        rank_color = "#334155"
    elif rec.rank == 3:
        rank_border = "#D97706"
        medal = "🥉"
        rank_label = "#3 LIVELY ALTERNATIVE"
        rank_bg = "#FFEDD5"
        rank_color = "#9A3412"
    else:
        rank_border = "#CBD5E1"
        medal = "⭐"
        rank_label = f"#{rec.rank}"
        rank_bg = "#F8FAFC"
        rank_color = "#475569"

    # Highlights pills
    highlight_tags = "".join(
        f'<span style="display:inline-block;background:#F8FAFC;color:#334155;border:1px solid #E2E8F0;padding:4px 12px;border-radius:20px;font-size:0.78rem;font-weight:500;margin-right:6px;margin-top:6px;box-shadow:0 1px 2px rgba(0,0,0,0.02);">✨ {hl}</span>'
        for hl in rec.highlights[:4]
    )

    card_html = textwrap.dedent(f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid {rank_border}; border-radius: 18px; padding: 24px; margin-bottom: 22px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="background: {rank_bg}; border: 1px solid {rank_border}40; color: {rank_color}; font-weight: 800; font-size: 0.84rem; padding: 5px 12px; border-radius: 10px; display: flex; align-items: center; gap: 6px;">
                        <span>{medal}</span>
                        <span>{rank_label}</span>
                    </div>
                    <div>
                        <h3 style="margin: 0; font-size: 1.35rem; font-weight: 700; color: #0F172A; letter-spacing: -0.4px;">{rec.restaurant_name}</h3>
                        <div style="color: #64748B; font-size: 0.88rem; margin-top: 2px; font-weight: 500;">📍 {rec.location}</div>
                    </div>
                </div>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <span style="background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; font-weight: 700; font-size: 0.95rem; padding: 5px 12px; border-radius: 10px;">★ {rec.rating:.1f}</span>
                </div>
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 14px; align-items: center; background: #F8FAFC; padding: 9px 14px; border-radius: 10px; border: 1px solid #E2E8F0;">
                <span style="color: #1E293B; font-size: 0.88rem; font-weight: 600;">🍲 {rec.cuisine}</span>
                <span style="color: #CBD5E1;">•</span>
                <span style="color: #92400E; background: #FEF3C7; border: 1px solid #FDE68A; padding: 2px 8px; border-radius: 6px; font-size: 0.85rem; font-weight: 700;">💰 ₹{rec.cost_for_two:,} for two</span>
            </div>
            <div style="background: #FFF7ED; border-left: 3px solid #F97316; border-radius: 10px; padding: 14px 18px; margin-bottom: 14px;">
                <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 4px;">
                    <span style="font-size: 0.95rem;">💡</span>
                    <span style="font-weight: 700; font-size: 0.82rem; color: #C2410C; text-transform: uppercase; letter-spacing: 0.5px;">Why We Recommend This • Gemini AI Reasoning</span>
                </div>
                <p style="margin: 0; color: #7C2D12; font-size: 0.95rem; line-height: 1.55; font-weight: 450;">{rec.why_recommended}</p>
            </div>
            <div style="margin-bottom: 16px;">
                {highlight_tags}
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 10px; padding-top: 12px; border-top: 1px solid #F1F5F9;">
                <a href="https://www.google.com/search?q={rec.restaurant_name}+{rec.location}+Bangalore" target="_blank" style="text-decoration: none; padding: 7px 16px; border-radius: 10px; font-size: 0.84rem; font-weight: 600; color: #E23744; background: #FFF1F2; border: 1px solid #FFE4E6; transition: all 0.2s ease;">View Details ↗</a>
            </div>
        </div>
    """).strip()

    st.markdown(card_html, unsafe_allow_html=True)


def render_empty_state():
    """Render empty state messaging when zero candidates match filters with an aesthetic white look."""
    empty_html = textwrap.dedent("""
        <div style="background: #FFFFFF; border: 2px dashed #CBD5E1; border-radius: 18px; padding: 42px 24px; text-align: center; margin-top: 20px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);">
            <div style="font-size: 3rem; margin-bottom: 12px;">🍅</div>
            <h3 style="color: #0F172A; margin-bottom: 8px; font-weight: 700; font-size: 1.3rem;">No Restaurants Found</h3>
            <p style="color: #64748B; max-width: 480px; margin: 0 auto 20px auto; font-size: 0.95rem; line-height: 1.5;">
                Tomato AI couldn't find any dining spots matching your exact filter combinations.
            </p>
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px 24px; display: inline-block; text-align: left; font-size: 0.88rem; color: #334155;">
                <strong style="color: #0F172A;">Try adjusting your search:</strong>
                <ul style="margin: 6px 0 0 0; padding-left: 20px; color: #64748B;">
                    <li>Expand your budget tier to <em>'Medium'</em> or <em>'Any'</em></li>
                    <li>Lower the minimum rating threshold (e.g., to 3.5★)</li>
                    <li>Select a broader locality or remove specific cuisine restrictions</li>
                </ul>
            </div>
        </div>
    """).strip()
    st.markdown(empty_html, unsafe_allow_html=True)
