"""UI card rendering components for Streamlit frontend with Stitch Dark Theme."""

import textwrap
import streamlit as st
from src.llm.schemas import RestaurantRecommendation


def render_executive_summary(summary: str, is_fallback: bool = False, total_found: int = 0):
    """Render an executive summary card at the top of the recommendation results."""
    badge_label = "⚡ HEURISTIC FALLBACK" if is_fallback else "✨ GEMINI AI CURATED"
    badge_bg = "rgba(245, 158, 11, 0.2)" if is_fallback else "rgba(139, 92, 246, 0.25)"
    badge_color = "#FBBF24" if is_fallback else "#C084FC"
    badge_border = "rgba(245, 158, 11, 0.4)" if is_fallback else "rgba(168, 85, 247, 0.4)"

    card_html = textwrap.dedent(f"""
        <div style="background: rgba(19, 28, 46, 0.85); border: 1px solid rgba(255, 255, 255, 0.1); border-left: 4px solid #E23744; border-radius: 14px; padding: 22px 26px; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4); backdrop-filter: blur(12px);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="width: 32px; height: 32px; border-radius: 8px; background: rgba(226, 55, 68, 0.2); border: 1px solid rgba(226, 55, 68, 0.4); display: flex; align-items: center; justify-content: center; font-size: 1rem;">🎯</div>
                    <span style="font-weight: 700; font-size: 1.18rem; color: #FFFFFF; letter-spacing: -0.3px;">Concierge Executive Summary</span>
                </div>
                <span style="background: {badge_bg}; color: {badge_color}; border: 1px solid {badge_border}; font-size: 0.74rem; font-weight: 700; font-family: monospace; letter-spacing: 0.5px; padding: 4px 12px; border-radius: 20px;">{badge_label}</span>
            </div>
            <p style="color: #CBD5E1; font-size: 1.02rem; line-height: 1.65; margin: 0;">{summary}</p>
        </div>
    """).strip()

    st.markdown(card_html, unsafe_allow_html=True)


def render_restaurant_card(rec: RestaurantRecommendation, index: int = 1):
    """Render an individual ranked restaurant recommendation card matching Stitch dark theme."""
    # Rank styling
    if rec.rank == 1:
        rank_border = "#F59E0B"
        medal = "🥇"
        rank_label = "#1 TOP MATCH"
    elif rec.rank == 2:
        rank_border = "#94A3B8"
        medal = "🥈"
        rank_label = "#2 GREAT MATCH"
    elif rec.rank == 3:
        rank_border = "#B45309"
        medal = "🥉"
        rank_label = "#3 LIVELY ALTERNATIVE"
    else:
        rank_border = "#64748B"
        medal = "⭐"
        rank_label = f"#{rec.rank}"

    # Highlights pills
    highlight_tags = "".join(
        f'<span style="display:inline-block;background:rgba(255,255,255,0.05);color:#E2E8F0;border:1px solid rgba(255,255,255,0.1);padding:4px 11px;border-radius:10px;font-size:0.78rem;font-weight:500;margin-right:6px;margin-top:6px;">✨ {hl}</span>'
        for hl in rec.highlights[:4]
    )

    card_html = textwrap.dedent(f"""
        <div style="background: rgba(30, 41, 59, 0.65); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 4px solid {rank_border}; border-radius: 16px; padding: 22px; margin-bottom: 22px; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3); backdrop-filter: blur(12px);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="background: rgba(11, 15, 25, 0.8); border: 1px solid rgba(255, 255, 255, 0.12); color: #F59E0B; font-weight: 800; font-size: 0.85rem; padding: 5px 12px; border-radius: 10px; display: flex; align-items: center; gap: 6px;">
                        <span>{medal}</span>
                        <span>{rank_label}</span>
                    </div>
                    <div>
                        <h3 style="margin: 0; font-size: 1.35rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.3px;">{rec.restaurant_name}</h3>
                        <div style="color: #94A3B8; font-size: 0.88rem; margin-top: 2px;">📍 {rec.location}</div>
                    </div>
                </div>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <span style="background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.35); font-weight: 700; font-size: 0.95rem; padding: 5px 12px; border-radius: 10px;">★ {rec.rating:.1f}</span>
                </div>
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 14px; align-items: center; background: rgba(11, 15, 25, 0.6); padding: 8px 12px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.05);">
                <span style="color: #F8FAFC; font-size: 0.88rem; font-weight: 600;">🍲 {rec.cuisine}</span>
                <span style="color: #64748B;">•</span>
                <span style="color: #FDE68A; font-size: 0.88rem; font-weight: 600;">💰 ₹{rec.cost_for_two:,} for two</span>
            </div>
            <div style="background: rgba(245, 158, 11, 0.07); border-left: 3px solid #F59E0B; border-radius: 10px; padding: 12px 16px; margin-bottom: 14px;">
                <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 4px;">
                    <span style="font-size: 0.95rem;">💡</span>
                    <span style="font-weight: 700; font-size: 0.82rem; color: #FCD34D; text-transform: uppercase; letter-spacing: 0.5px;">Why Gemini Picked This</span>
                </div>
                <p style="margin: 0; color: #FEF3C7; font-size: 0.95rem; line-height: 1.55;">{rec.why_recommended}</p>
            </div>
            <div style="margin-bottom: 16px;">
                {highlight_tags}
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 10px; pt-3; border-top: 1px solid rgba(255, 255, 255, 0.07);">
                <a href="https://www.google.com/search?q={rec.restaurant_name}+{rec.location}+Bangalore+Zomato" target="_blank" style="text-decoration: none; padding: 6px 14px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; color: #CBD5E1; background: rgba(19, 28, 46, 0.9); border: 1px solid rgba(255, 255, 255, 0.1);">View Details</a>
            </div>
        </div>
    """).strip()

    st.markdown(card_html, unsafe_allow_html=True)


def render_empty_state():
    """Render empty state messaging when zero candidates match filters."""
    empty_html = textwrap.dedent("""
        <div style="background: rgba(19, 28, 46, 0.7); border: 2px dashed rgba(139, 92, 246, 0.35); border-radius: 16px; padding: 40px 20px; text-align: center; margin-top: 20px;">
            <div style="font-size: 3rem; margin-bottom: 12px;">🔍</div>
            <h3 style="color: #FFFFFF; margin-bottom: 8px; font-weight: 700;">No Restaurants Found</h3>
            <p style="color: #94A3B8; max-width: 480px; margin: 0 auto 20px auto; font-size: 0.95rem; line-height: 1.5;">
                We couldn't find any dining spots matching your exact filter combinations.
            </p>
            <div style="background: rgba(11, 15, 25, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 14px 20px; display: inline-block; text-align: left; font-size: 0.88rem; color: #CBD5E1;">
                <strong style="color: #F8FAFC;">Try adjusting your search:</strong>
                <ul style="margin: 6px 0 0 0; padding-left: 20px; color: #94A3B8;">
                    <li>Expand your budget tier to <em>'Medium'</em> or <em>'Any'</em></li>
                    <li>Lower the minimum rating threshold (e.g., to 3.5★)</li>
                    <li>Select a broader locality or remove specific cuisine restrictions</li>
                </ul>
            </div>
        </div>
    """).strip()
    st.markdown(empty_html, unsafe_allow_html=True)
