"""Sidebar control panel component for Streamlit frontend."""

from typing import Any, Dict, Optional, Tuple
import streamlit as st


def render_sidebar_controls(meta_options: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], bool]:
    """
    Render sidebar preference controls and return the assembled preferences payload.

    Returns:
        Tuple of (preferences_dict, is_submitted_boolean)
    """
    with st.sidebar:
        # Branding Header
        st.markdown(
            """
            <div style="text-align: center; padding: 10px 0 20px 0;">
                <div style="
                    display: inline-block;
                    background: linear-gradient(135deg, #E23744 0%, #CB202D 100%);
                    color: white;
                    font-size: 1.5rem;
                    font-weight: 900;
                    letter-spacing: -0.5px;
                    padding: 8px 18px;
                    border-radius: 12px;
                    margin-bottom: 8px;
                    box-shadow: 0 4px 12px rgba(226, 55, 68, 0.3);
                ">zomato <span style="font-weight: 300; font-size: 1.2rem;">AI</span></div>
                <div style="font-size: 0.85rem; color: #64748B; font-weight: 500;">
                    Culinary Reasoning Concierge
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.subheader("🎯 Dining Preferences")

        # 1. Location
        locations = meta_options.get("locations", ["Indiranagar", "Koramangala", "Whitefield", "Jayanagar"])
        default_loc_idx = locations.index("Indiranagar") if "Indiranagar" in locations else 0
        selected_location = st.selectbox(
            "📍 Locality / Area",
            options=locations,
            index=default_loc_idx,
            help="Select the neighborhood or city area in Bangalore you want to dine in.",
        )

        # 2. Budget Tier
        budget_options = ["Medium (₹500 - ₹1500)", "Low (≤ ₹500)", "High (> ₹1500)", "Any Budget"]
        selected_budget_str = st.radio(
            "💰 Budget (for two people)",
            options=budget_options,
            index=0,
            help="Select your approximate cost for two range.",
        )

        tier_map = {
            "Low (≤ ₹500)": "Low",
            "Medium (₹500 - ₹1500)": "Medium",
            "High (> ₹1500)": "High",
            "Any Budget": "Any",
        }
        selected_budget_tier = tier_map.get(selected_budget_str, "Medium")

        # Optional Custom Max Budget
        with st.expander("⚙️ Explicit Max Budget (Optional)"):
            custom_max = st.number_input(
                "Max Cost for Two (INR)",
                min_value=0,
                max_value=10000,
                value=0,
                step=100,
                help="Set an optional hard ceiling on cost for two.",
            )
            max_budget_val = custom_max if custom_max > 0 else None

        # 3. Cuisines
        available_cuisines = meta_options.get("cuisines", [
            "North Indian", "Chinese", "South Indian", "Italian", "Continental",
            "Biryani", "Fast Food", "Cafe", "Desserts", "Mughlai"
        ])
        selected_cuisines = st.multiselect(
            "🍲 Preferred Cuisines",
            options=available_cuisines,
            default=[],
            help="Select one or more cuisines, or leave empty for all cuisines.",
        )

        # 4. Minimum Rating Slider
        min_rating = st.slider(
            "⭐ Minimum Rating",
            min_value=3.0,
            max_value=5.0,
            value=3.8,
            step=0.1,
            format="%.1f★",
            help="Filter out restaurants below this rating.",
        )

        # 5. Occasion / Vibe
        st.markdown("🎉 **Occasion / Dining Vibe**")
        occasion_presets = [
            "Any Occasion",
            "Romantic Date Night",
            "Casual Family Dinner",
            "Catching up with Friends",
            "Quick Weekday Lunch",
            "Celebration / Birthday",
            "Quiet Work / Reading Cafe",
        ]
        selected_preset = st.selectbox(
            "Preset Vibe",
            options=occasion_presets,
            index=0,
            label_visibility="collapsed",
        )

        custom_occasion = st.text_input(
            "Custom Occasion or Details",
            placeholder="e.g., Anniversary with craft cocktails and live music",
            help="Tell Gemini what kind of vibe or specific situation you are planning for.",
        )

        final_occasion = custom_occasion.strip() if custom_occasion.strip() else (
            selected_preset if selected_preset != "Any Occasion" else None
        )

        # 6. Dining Type
        dining_types = ["Any"] + meta_options.get("dining_types", ["Dine-out", "Delivery", "Cafes", "Buffet", "Pubs and Bars"])
        selected_dining_type = st.selectbox(
            "🍽️ Dining Mode",
            options=dining_types,
            index=0,
        )

        st.markdown("---")

        # Submit CTA
        submitted = st.button(
            "✨ Find Restaurants",
            type="primary",
            use_container_width=True,
        )

        # Dataset / System Status Footer
        total_restaurants = meta_options.get("total_restaurants", 12126)
        st.caption(f"📊 Indexed Database: **{total_restaurants:,}** Bangalore restaurants")

    if submitted:
        payload = {
            "location": selected_location,
            "budget_tier": selected_budget_tier,
            "max_budget": max_budget_val,
            "cuisines": selected_cuisines,
            "min_rating": min_rating,
            "occasion": final_occasion,
            "dining_type": None if selected_dining_type == "Any" else selected_dining_type,
            "candidate_limit": 15,
        }
        return payload, True

    return None, False
