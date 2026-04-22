# ui/components/styles.py
import streamlit as st


def inject_global_padding(padding_top_rem: float = 0.08, padding_bottom_rem: float = 0.0) -> None:
    st.markdown(
        f"""
        <style>
          .appview-container .main .block-container,
          div.block-container{{
            padding-top: {padding_top_rem}rem !important;
            padding-bottom: {padding_bottom_rem}rem !important;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_base_css() -> None:
    """
    Base CSS for the whole app (both columns).
    """
    st.markdown(
        r"""
<style>
:root{
  --bg:#ffffff;
  --text:#111827;
  --muted:#6b7280;

  --data-blue:#2563eb;
  --data-blue-soft:rgba(37,99,235,.10);

  --accent:#f59e0b;
  --btn-disabled-bg:#e5e7eb;
  --btn-disabled-text:#9ca3af;
  --btn-disabled-border:#d1d5db;

  --panel-h: 70vh; /* JS overrides */
}

html, body{ height:100% !important; overflow:hidden !important; }
.stApp{ background:var(--bg); color:var(--text); }

div.block-container{
  padding-left:0.55rem !important;
  padding-right:0.55rem !important;
  max-width:1460px !important;
}

h1,h2,h3{ margin-top:0 !important; margin-bottom:0.30rem !important; }

[data-testid="stVerticalBlockBorderWrapper"]{
  border:none !important; box-shadow:none !important; background:transparent !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div{
  border:none !important; box-shadow:none !important; background:transparent !important;
}

[data-testid="stElementContainer"]:has(.panel-marker),
[data-testid="stElementContainer"]:has(.col-marker){
  height:0 !important; min-height:0 !important; max-height:0 !important;
  overflow:hidden !important; margin:0 !important; padding:0 !important;
}

[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .left-col-marker){
  gap:0 !important;
}

[data-testid="stVerticalBlockBorderWrapper"]:has(.left-panel-marker) > div,
[data-testid="stVerticalBlockBorderWrapper"]:has(.right-panel-marker) > div{
  height:var(--panel-h) !important;
  max-height:var(--panel-h) !important;
  border:none !important;
  border-radius:0 !important;
}

[data-testid="stVerticalBlockBorderWrapper"]:has(.left-panel-marker) > div{
  height:calc(var(--panel-h) - 68px) !important;
  max-height:calc(var(--panel-h) - 68px) !important;

  overflow-y:auto !important;
  overflow-x:hidden !important;
  -webkit-overflow-scrolling:touch;
  overscroll-behavior:contain;

  padding:0 !important;
}

.left-inner-pad{
  padding:12px 14px !important;
}

[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .left-col-marker)
  > [data-testid="stElementContainer"]:last-child{
  border:none !important;
  border-radius:0 !important;
  padding:10px 14px 12px !important;
  background:transparent !important;
}

[data-testid="stVerticalBlockBorderWrapper"]:has(.right-panel-marker) > div{
  overflow-y:auto !important;
  overflow-x:hidden !important;
  -webkit-overflow-scrolling:touch;
  overscroll-behavior:contain;
  padding:12px 14px !important;
}

.section-label{
  font-size:0.78rem;
  font-weight:800;
  letter-spacing:0.08em;
  color:var(--muted);
  margin:8px 0 10px;
}
hr{
  border:0; height:1px;
  background: rgba(17,24,39,0.14);
  margin:12px 0;
}

.stButton > button[kind="primary"],
[data-testid="stBaseButton-primary"] > button{
  width:100% !important;
  height:48px !important;
  border-radius:10px !important;
  font-weight:800 !important;
  background:var(--accent) !important;
  border:1px solid var(--accent) !important;
  color:#111827 !important;
}
.stButton > button[kind="primary"]:disabled,
[data-testid="stBaseButton-primary"] > button:disabled{
  background:var(--btn-disabled-bg) !important;
  border:1px solid var(--btn-disabled-border) !important;
  color:var(--btn-disabled-text) !important;
  cursor:not-allowed !important;
  opacity:1 !important;
}

.right-placeholder{
  height:calc(var(--panel-h) - 40px);
  display:flex;
  align-items:center;
  justify-content:center;
  color:rgba(17,24,39,0.35);
  font-size:1rem;
  text-align:center;
  padding:1rem;
}

[data-testid="stDataFrame"]{
  border: 1px solid rgba(37,99,235,0.25) !important;
  border-radius: 10px !important;
}
[data-testid="stDataFrame"] [role="columnheader"]{
  background: var(--data-blue-soft) !important;
}
[data-testid="stDataFrame"] [role="gridcell"]{
  border-color: rgba(37,99,235,0.10) !important;
}

*{ scrollbar-width:thin; scrollbar-color:rgba(0,0,0,0.18) transparent; }
::-webkit-scrollbar{ width:6px; }
::-webkit-scrollbar-track{ background:transparent; }
::-webkit-scrollbar-thumb{ background:rgba(0,0,0,0.18); border-radius:3px; }

.top-title-wrap{ margin:0 !important; padding:0 !important; }
[data-testid="stMarkdownContainer"]:has(.top-title-wrap),
[data-testid="stElementContainer"]:has(.top-title-wrap){
  margin:0 !important; padding:0 !important;
}
.top-title{
  margin:0 !important;
  padding:0.15em 0 0 !important;  
  line-height:1.2 !important;    
  font-size:2.05rem;
  font-weight:900;
  letter-spacing:0.02em;
  color:var(--text);
  display:inline-block;          
}

.left-sticky-headers{
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--bg);
  padding: 12px 14px 10px;
  border-bottom: 1px solid rgba(17,24,39,0.10);
}
.left-sticky-headers .hdr-row{
  display:grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap:8px;
}
.left-sticky-headers button{
  width:100%;
  display:flex;
  align-items:center;
  justify-content:center;
  padding: 8px 10px;
  border-radius: 10px;
  font-weight: 900;
  font-size: 0.86rem;
  color: var(--text);
  background: rgba(17,24,39,0.04);
  border: 1px solid rgba(17,24,39,0.08);
  cursor:pointer;
}
.left-sticky-headers button:hover{ background: rgba(17,24,39,0.06); }
.req-star{ color:#ef4444; font-weight:900; margin-left:6px; }
.section-anchor{ scroll-margin-top: 78px; }

/* ===== Right column helpers (moved from inline) ===== */

/* Make right column stack tight */
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .right-col-marker){
  gap:0 !important;
}

/* RIGHT fixed header (outside scroller) */
.right-fixed-headers{
  position: sticky;
  top: 0;
  z-index: 140;
  background: var(--bg);
  padding: 12px 14px 10px;

  border-bottom: 1px solid rgba(17,24,39,0.10);
  box-shadow: none;
}

.right-fixed-headers .hdr-row{
  display:grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap:8px;
}

.right-fixed-headers.two-tabs .hdr-row{
  grid-template-columns: 1fr 1fr;
}

.right-fixed-headers button{
  width:100%;
  display:flex;
  align-items:center;
  justify-content:center;
  padding: 8px 10px;
  border-radius: 10px;
  font-weight: 900;
  font-size: 0.86rem;
  color: var(--text);
  background: rgba(17,24,39,0.04);
  border: 1px solid rgba(17,24,39,0.08);
  cursor:pointer;
}
.right-fixed-headers button:hover{ background: rgba(17,24,39,0.06); }

/* Anchors inside scroller */
.right-section-anchor{
  scroll-margin-top: 18px;
}
</style>
""",
        unsafe_allow_html=True,
    )
