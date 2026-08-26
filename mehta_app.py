#!/usr/bin/env python3
"""
Mehta 3/3 Screener — Streamlit UI
Run:  streamlit run mehta_app.py
"""

import json
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Mehta 3/3 Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem !important;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .score-3 {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .score-2 {
        background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
        color: #333;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .stButton>button {
        width: 100%;
        height: 3.5rem;
        font-size: 1.2rem;
        font-weight: 600;
        border-radius: 0.75rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(102,126,234,0.4);
    }
    .stButton>button:disabled {
        background: #ccc;
        transform: none;
        box-shadow: none;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Helpers ─────────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent
CFG_PATH = BASE / "config.json"
OUTPUT_DIR = BASE / "output"

def load_config():
    if CFG_PATH.exists():
        return json.loads(CFG_PATH.read_text(encoding="utf-8"))
    return {}

def get_latest_excel():
    if not OUTPUT_DIR.exists():
        return None
    files = sorted(OUTPUT_DIR.glob("Mehta_Screener_*.xlsx"), reverse=True)
    return files[0] if files else None

def read_excel_filtered(path):
    """Read all sheets and return only 3/3 and 2/3 stocks."""
    xls = pd.ExcelFile(path)
    dfs = []
    for sheet in xls.sheet_names:
        if sheet in ("3-3 SUPER", "2-3 HOLD"):
            df = pd.read_excel(xls, sheet_name=sheet)
            df["Sheet"] = sheet
            dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)

def run_screener():
    """Execute the screener script and capture output."""
    script = BASE / "mehta_screener.py"
    if not script.exists():
        return False, "mehta_screener.py not found in the same directory."
    
    env = {**dict(subprocess.os.environ), "PYTHONUNBUFFERED": "1"}
    proc = subprocess.Popen(
        [sys.executable, str(script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=str(BASE),
        env=env,
    )
    logs = []
    for line in proc.stdout:
        logs.append(line)
    proc.wait()
    success = proc.returncode == 0
    return success, "".join(logs)

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/stocks.png", width=80)
    st.title("Settings")
    
    cfg = load_config()
    st.markdown("**Universe Config**")
    st.json({
        "Top N": cfg.get("universe", {}).get("top_n", 750),
        "Min Size": cfg.get("universe", {}).get("minimum_universe_size", 400),
        "Workers": cfg.get("runtime", {}).get("workers", 16),
    })
    
    st.markdown("**Rules**")
    st.json({
        "ATH Tolerance": cfg.get("rules", {}).get("ath_tolerance", 0.98),
        "PAT Tolerance": cfg.get("rules", {}).get("pat_record_tolerance", 1.0),
    })
    
    st.markdown("---")
    st.caption("Mehta 3/3 NSE Screener\nFast Mode Edition")

# ── Main Header ─────────────────────────────────────────────────────────────
st.markdown('<p class="main-header">📊 Mehta 3/3 NSE Screener</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">One-click screening for Super Performers (3/3) and Hold candidates (2/3)</p>', unsafe_allow_html=True)

# ── Top Metrics (from latest run if available) ─────────────────────────────
latest = get_latest_excel()
if latest:
    try:
        all_sheets = pd.read_excel(latest, sheet_name=None)
        counts = {
            "3/3": len(all_sheets.get("3-3 SUPER", pd.DataFrame())),
            "2/3": len(all_sheets.get("2-3 HOLD", pd.DataFrame())),
            "1/3": len(all_sheets.get("1-3", pd.DataFrame())),
            "0/3": len(all_sheets.get("0-3 EXIT", pd.DataFrame())),
        }
        total = sum(counts.values())
        
        cols = st.columns(5)
        metrics = [
            ("🎯 3/3 Super", counts["3/3"], "#11998e"),
            ("⭐ 2/3 Hold", counts["2/3"], "#f7971e"),
            ("⚠️ 1/3", counts["1/3"], "#ff6b6b"),
            ("❌ 0/3 Exit", counts["0/3"], "#ee5a6f"),
            ("📋 Total", total, "#667eea"),
        ]
        for col, (label, val, color) in zip(cols, metrics):
            with col:
                st.markdown(f"""
                <div style="background: {color}; padding: 1rem; border-radius: 0.75rem; color: white; text-align: center;">
                    <div style="font-size: 0.85rem; opacity: 0.9;">{label}</div>
                    <div style="font-size: 2rem; font-weight: 700;">{val}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.caption(f"Last run: {latest.stem.replace('Mehta_Screener_', '')}")
    except Exception as e:
        st.error(f"Error reading latest file: {e}")
else:
    st.info("👈 No previous run found. Click **Run Screener** below to start.")

st.markdown("---")

# ── Run Button ──────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    run_clicked = st.button("🚀 RUN SCREENER NOW", type="primary", use_container_width=True)

if run_clicked:
    progress_bar = st.progress(0, text="Initializing...")
    log_container = st.empty()
    status_text = st.empty()
    
    # Simulate progress while screener runs (it runs in subprocess)
    status_text.info("⏳ Downloading NSE universe & price data... This may take 2–5 minutes.")
    
    success, logs = run_screener()
    
    if success:
        progress_bar.progress(100, text="Complete!")
        status_text.success("✅ Screener completed successfully!")
        
        # Show logs in expander
        with st.expander("📜 View Full Logs"):
            st.code(logs, language="bash")
        
        # Auto-refresh to show results
        st.rerun()
    else:
        progress_bar.empty()
        status_text.error("❌ Screener failed. Check logs below.")
        with st.expander("📜 Error Logs"):
            st.code(logs, language="bash")

# ── Results Section ─────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🎯 Filtered Results: 3/3 Super Performers & 2/3 Hold Candidates")

if latest:
    try:
        filtered_df = read_excel_filtered(latest)
        
        if filtered_df.empty:
            st.warning("No 3/3 or 2/3 stocks found in the latest run.")
        else:
            # Add pretty score badges
            def badge(score):
                if score == "3/3":
                    return '<span class="score-3">3/3 SUPER</span>'
                elif score == "2/3":
                    return '<span class="score-2">2/3 HOLD</span>'
                return score
            
            display_df = filtered_df.copy()
            if "Score" in display_df.columns:
                display_df["Score"] = display_df["Score"].apply(badge)
            
            # Column order for better display
            priority_cols = ["Symbol", "Company", "Score", "Action", "Industry", 
                           "Current Price", "ATH", "52W Return", "Beats Nifty500", 
                           "Beats Sector", "Record PAT?", "Data Status"]
            existing_cols = [c for c in priority_cols if c in display_df.columns]
            other_cols = [c for c in display_df.columns if c not in priority_cols and c != "Sheet"]
            display_df = display_df[existing_cols + other_cols]
            
            # Show as interactive dataframe
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Symbol": st.column_config.TextColumn("Symbol", width="small"),
                    "Company": st.column_config.TextColumn("Company", width="medium"),
                    "Current Price": st.column_config.NumberColumn("Price (₹)", format="%.2f"),
                    "ATH": st.column_config.NumberColumn("ATH (₹)", format="%.2f"),
                    "52W Return": st.column_config.NumberColumn("52W Return", format="%.2%"),
                }
            )
            
            # Download buttons
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                with open(latest, "rb") as f:
                    st.download_button(
                        label="📥 Download Full Excel (All Sheets)",
                        data=f,
                        file_name=latest.name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
            
            with col_dl2:
                # Create filtered Excel
                filtered_excel = filtered_df.drop(columns=["Sheet"], errors="ignore")
                csv = filtered_excel.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Filtered CSV (3/3 + 2/3 only)",
                    data=csv,
                    file_name=f"Mehta_Filtered_{datetime.now().strftime('%Y-%m-%d')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            
            # Summary cards for filtered stocks
            st.markdown("---")
            st.subheader("📋 Quick Summary")
            
            if "Score" in filtered_df.columns:
                score_counts = filtered_df["Score"].value_counts()
                c1, c2, c3 = st.columns(3)
                with c1:
                    val = score_counts.get("3/3", 0)
                    st.metric("🎯 3/3 Super Performers", val)
                with c2:
                    val = score_counts.get("2/3", 0)
                    st.metric("⭐ 2/3 Hold Candidates", val)
                with c3:
                    st.metric("📊 Combined Total", len(filtered_df))
            
            # Show top picks
            if "52W Return" in filtered_df.columns:
                st.markdown("**🏆 Top 5 by 52-Week Return**")
                top5 = filtered_df.nlargest(5, "52W Return")[
                    ["Symbol", "Company", "Score", "52W Return", "Action"]
                ]
                st.dataframe(top5, use_container_width=True, hide_index=True)
                
    except Exception as e:
        st.error(f"Error loading results: {e}")
else:
    st.info("Run the screener to see 3/3 and 2/3 filtered results here.")

# ── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("""
**Mehta 3/3 Screener** • Filters: Price at/near ATH | Record PAT | Beats Nifty500 + Sector  
Built with Streamlit • Data via Yahoo Finance & Screener.in
""")