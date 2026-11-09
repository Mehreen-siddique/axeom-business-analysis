"""
Axeom Business & Operations Dashboard
Run locally:  streamlit run app.py

Optional data files (the app falls back to sample data if they are missing):
  data/leads.csv     -> columns: lead_id, source, status   (status: "Booked" or "Lost")
  data/invoices.csv  -> columns: invoice_id, amount, status (status: "Paid" / "Overdue" / ...)
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# --------------------------------------------------------------------------- #
# Page config
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Axeom Business & Operations Dashboard",
    page_icon="📊",
    layout="wide",
)

DATA_DIR = Path("data")
LEADS_CSV = DATA_DIR / "leads.csv"
INVOICES_CSV = DATA_DIR / "invoices.csv"

COLORS = {"Leads": "#4C78A8", "Bookings": "#54A24B", "Lost": "#E45756"}

# --------------------------------------------------------------------------- #
# Data layer
# --------------------------------------------------------------------------- #
# NOTE: The per-source split below is PLACEHOLDER data. Totals (102 / 20 / 82)
# match the analysis, but replace with data/leads.csv for real source numbers.
SAMPLE_SOURCES = {
    # source: (total_leads, bookings)
    "Email": (41, 9),
    "WhatsApp": (38, 7),
    "Instagram": (23, 4),
}


def build_sample_leads() -> pd.DataFrame:
    rows, i = [], 1
    for source, (total, booked) in SAMPLE_SOURCES.items():
        for n in range(total):
            rows.append(
                {
                    "lead_id": i,
                    "source": source,
                    "status": "Booked" if n < booked else "Lost",
                }
            )
            i += 1
    return pd.DataFrame(rows)


def build_sample_invoices() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "invoice_id": range(1, 21),
            "amount": [0.0] * 20,
            "status": ["Paid"] * 20,
        }
    )


@st.cache_data
def load_leads() -> tuple[pd.DataFrame, bool]:
    """Return (dataframe, is_sample)."""
    if LEADS_CSV.exists():
        try:
            df = pd.read_csv(LEADS_CSV)
            if {"source", "status"}.issubset(df.columns):
                return df, False
        except Exception:
            pass
    return build_sample_leads(), True


@st.cache_data
def load_invoices() -> tuple[pd.DataFrame, bool]:
    if INVOICES_CSV.exists():
        try:
            df = pd.read_csv(INVOICES_CSV)
            if {"amount", "status"}.issubset(df.columns):
                return df, False
        except Exception:
            pass
    return build_sample_invoices(), True


def compute_kpis(leads: pd.DataFrame, invoices: pd.DataFrame) -> dict:
    total = len(leads)
    booked = int((leads["status"].str.lower() == "booked").sum())
    lost = total - booked
    rate = (booked / total * 100) if total else 0.0
    overdue = float(
        invoices.loc[invoices["status"].str.lower() == "overdue", "amount"].sum()
    )
    return {
        "total": total,
        "booked": booked,
        "lost": lost,
        "rate": rate,
        "overdue": overdue,
    }


# --------------------------------------------------------------------------- #
# UI components
# --------------------------------------------------------------------------- #
def render_header() -> None:
    st.title("Axeom Business & Operations Dashboard")
    st.caption("Data-driven insights, conversion funnel, and financial reconciliation.")


def render_kpis(k: dict) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Leads", f"{k['total']:,}")
    c2.metric("Total Bookings", f"{k['booked']:,}")
    c3.metric("Conversion Rate", f"{k['rate']:.2f}%")
    if k["overdue"] == 0:
        c4.metric("Overdue Invoices", "$0.00", "Fully reconciled")
    else:
        c4.metric("Overdue Invoices", f"${k['overdue']:,.2f}", "Action needed", delta_color="inverse")


def funnel_chart(k: dict):
    df = pd.DataFrame(
        {
            "Stage": ["Leads", "Bookings", "Lost"],
            "Count": [k["total"], k["booked"], k["lost"]],
        }
    )
    fig = px.bar(
        df,
        x="Stage",
        y="Count",
        color="Stage",
        color_discrete_map=COLORS,
        text="Count",
        title="Leads vs. Bookings vs. Lost",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False, yaxis_title=None, xaxis_title=None)
    return fig


def funnel_shape_chart(k: dict):
    fig = px.funnel(
        pd.DataFrame(
            {"Stage": ["Total Leads", "Bookings"], "Count": [k["total"], k["booked"]]}
        ),
        x="Count",
        y="Stage",
        title="Conversion Funnel",
    )
    fig.update_traces(marker_color=[COLORS["Leads"], COLORS["Bookings"]])
    return fig


def source_table(leads: pd.DataFrame) -> pd.DataFrame:
    grp = leads.groupby("source")["status"].agg(
        Leads="count",
        Bookings=lambda s: int((s.str.lower() == "booked").sum()),
    )
    grp["Lost"] = grp["Leads"] - grp["Bookings"]
    grp["Conversion %"] = (grp["Bookings"] / grp["Leads"] * 100).round(2)
    return grp.reset_index().rename(columns={"source": "Source"})


def render_overview_tab(k: dict, leads: pd.DataFrame) -> None:
    left, right = st.columns(2)
    with left:
        st.plotly_chart(funnel_chart(k), use_container_width=True)
    with right:
        st.plotly_chart(funnel_shape_chart(k), use_container_width=True)

    st.subheader("Lead Sources")
    src = source_table(leads)

    pie_col, bar_col = st.columns(2)
    with pie_col:
        fig = px.pie(src, names="Source", values="Leads", hole=0.45, title="Share of Leads by Source")
        st.plotly_chart(fig, use_container_width=True)
    with bar_col:
        long = src.melt(
            id_vars="Source", value_vars=["Bookings", "Lost"], var_name="Outcome", value_name="Count"
        )
        fig = px.bar(
            long,
            x="Source",
            y="Count",
            color="Outcome",
            barmode="stack",
            color_discrete_map={"Bookings": COLORS["Bookings"], "Lost": COLORS["Lost"]},
            title="Outcome by Source",
        )
        fig.update_layout(xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(src, use_container_width=True, hide_index=True)


def render_finance_tab(k: dict, invoices: pd.DataFrame) -> None:
    st.subheader("Financial Reconciliation")
    if k["overdue"] == 0:
        st.success("Invoices and payments are reconciled. Overdue total: $0.00.")
    else:
        st.error(f"Overdue invoices total ${k['overdue']:,.2f}.")
    status_counts = invoices["status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Invoices"]
    st.dataframe(status_counts, use_container_width=True, hide_index=True)


def render_insights_tab(k: dict) -> None:
    st.subheader("Root Causes of Lost Requests")
    st.warning(
        f"{k['lost']} of {k['total']} leads ({100 - k['rate']:.2f}%) did not convert."
    )
    st.markdown(
        """
        1. **Multi-channel fragmentation** – requests arrive via WhatsApp, Instagram and Email
           with no single inbox, so messages get missed or answered late.
        2. **No centralized tracking** – there is no single source of truth for lead status,
           owner, or next follow-up date.
        """
    )

    st.divider()
    st.subheader("🗓️ Monday Top 3")
    st.caption("Proposed action items to close the communication gaps.")
    a, b, c = st.columns(3)
    with a:
        with st.container(border=True):
            st.markdown("### 1. Centralize intake")
            st.write(
                "Route WhatsApp, Instagram and Email into one shared inbox or CRM view "
                "so every request is logged in one place."
            )
    with b:
        with st.container(border=True):
            st.markdown("### 2. Assign owner + response SLA")
            st.write(
                "Every new lead gets a named owner and a first-response target "
                "(e.g. within 2 business hours)."
            )
    with c:
        with st.container(border=True):
            st.markdown("### 3. Track status & follow-ups")
            st.write(
                "Use a simple pipeline (New → Contacted → Quoted → Booked / Lost) with a "
                "reason code for every lost lead, and review it weekly."
            )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    leads, leads_sample = load_leads()
    invoices, inv_sample = load_invoices()
    kpis = compute_kpis(leads, invoices)

    render_header()

    if leads_sample or inv_sample:
        st.info(
            "Running on sample data (CSV files not found in `data/`). Headline totals match the "
            "analysis; the per-source split is illustrative until `data/leads.csv` is provided."
        )

    render_kpis(kpis)
    st.divider()

    tab1, tab2, tab3 = st.tabs(["📈 Overview", "💰 Finance", "💡 Insights & Actions"])
    with tab1:
        render_overview_tab(kpis, leads)
    with tab2:
        render_finance_tab(kpis, invoices)
    with tab3:
        render_insights_tab(kpis)


if __name__ == "__main__":
    main()