"""Streamlit + Plotly monitoring dashboard.

Run from the project root:

    pip install -e ".[storage,dashboard]"
    streamlit run app/dashboard/app.py

Reads the same database the proxy writes to (DATABASE_URL / the default SQLite
file), so it shows live firewall traffic. Thin renderer over
app.dashboard.data.load_dashboard_data.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from app.dashboard.data import load_dashboard_data

VERDICT_COLORS = {"allow": "#639922", "flag": "#BA7517", "block": "#E24B4A"}

st.set_page_config(page_title="Prompt Injection Firewall", layout="wide")
st.title("Prompt injection firewall")
st.caption("Defense in depth · risk reduction, not prevention")

if st.button("↻ Refresh"):
    st.rerun()

data = load_dashboard_data()
s = data.summary

if not s or s.get("total", 0) == 0:
    st.info("No requests recorded yet. Send some through the proxy (POST /v1/chat), then refresh.")
    st.stop()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Requests", s["total"])
c2.metric("Blocked", s["blocked"])
c3.metric("Flagged", s["flagged"])
c4.metric("Block rate", f"{s['block_rate'] * 100:.1f}%")
c5.metric("Avg latency", f"{s['avg_latency_ms']} ms")

left, right = st.columns(2)

with left:
    st.subheader("Verdict distribution")
    labels = list(data.verdicts.keys())
    values = list(data.verdicts.values())
    colors = [VERDICT_COLORS.get(label, "#888888") for label in labels]
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.6, marker=dict(colors=colors))])
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Detections by category")
    if data.categories:
        cats = dict(sorted(data.categories.items(), key=lambda kv: kv[1]))
        bar = go.Figure(data=[go.Bar(x=list(cats.values()), y=list(cats.keys()), orientation="h")])
        bar.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
        st.plotly_chart(bar, use_container_width=True)
    else:
        st.write("No category-tagged detections yet.")

st.subheader("Recent inspected requests")
st.dataframe(data.recent, use_container_width=True, hide_index=True)
