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

  --panel-h: 76vh; /* JS overrides */
  --left-panel-h: calc(var(--panel-h) - 61px);
}

html, body{ height:100% !important; overflow:hidden !important; }
.stApp{ background:var(--bg); color:var(--text); }

header[data-testid="stHeader"]{
  display:none !important;
  height:0 !important;
}

[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"]{
  display:none !important;
  height:0 !important;
}

[data-testid="stAppViewContainer"]{
  padding-top:0 !important;
  margin-top:0 !important;
  top:0 !important;
  height:100dvh !important;
  min-height:100dvh !important;
  max-height:100dvh !important;
  overflow:hidden !important;
}

[data-testid="stMain"]{
  padding-top:0 !important;
  margin-top:0 !important;
  height:100dvh !important;
  min-height:100dvh !important;
  max-height:100dvh !important;
  overflow:hidden !important;
}

[data-testid="stMainBlockContainer"]{
  padding-top:0 !important;
  padding-bottom:0 !important;
  margin-top:0 !important;
  margin-bottom:0 !important;
  min-height:100dvh !important;
  height:100dvh !important;
  max-height:100dvh !important;
  display:flex !important;
  flex-direction:column !important;
  overflow:hidden !important;
}

div.block-container{
  padding-top:0 !important;
  padding-bottom:0 !important;
  padding-left:0.55rem !important;
  padding-right:0.55rem !important;
  margin-top:-18px !important;
  margin-bottom:0 !important;
  max-width:1460px !important;
  min-height:100dvh !important;
  height:100dvh !important;
  max-height:100dvh !important;
  display:flex !important;
  flex-direction:column !important;
  overflow:hidden !important;
}

div.block-container > div:last-child,
[data-testid="stMainBlockContainer"] > div:last-child,
[data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:last-child{
  margin-bottom:0 !important;
  padding-bottom:0 !important;
}

div.block-container > [data-testid="stHorizontalBlock"],
[data-testid="stMainBlockContainer"] > [data-testid="stHorizontalBlock"]{
  flex:1 1 auto !important;
  min-height:0 !important;
  overflow:hidden !important;
}

h1,h2,h3{ margin-top:0 !important; margin-bottom:0.30rem !important; }

[data-testid="stHorizontalBlock"]{
  align-items:flex-start !important;
}

[data-testid="stHorizontalBlock"]:has(.left-col-marker):has(.right-col-marker){
  align-items:stretch !important;
  min-height:0 !important;
  height:100% !important;
  flex:1 1 auto !important;
}

[data-testid="stHorizontalBlock"]:has(.left-col-marker):has(.right-col-marker) > [data-testid="column"]{
  display:flex !important;
  flex-direction:column !important;
  min-height:0 !important;
}

[data-testid="stHorizontalBlock"]:has(.left-col-marker):has(.right-col-marker) > [data-testid="column"] > [data-testid="stVerticalBlock"]{
  display:flex !important;
  flex-direction:column !important;
  flex:1 1 auto !important;
  min-height:0 !important;
  height:100% !important;
}

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

[data-testid="stElementContainer"]:has(iframe[height="0"]){
  height:0 !important;
  min-height:0 !important;
  max-height:0 !important;
  margin:0 !important;
  padding:0 !important;
  overflow:hidden !important;
}

[data-testid="stElementContainer"]:has(iframe[height="0"]) iframe{
  height:0 !important;
  min-height:0 !important;
  max-height:0 !important;
  border:0 !important;
  display:block !important;
}

[data-testid="stElementContainer"]:has(iframe){
  margin:0 !important;
  padding:0 !important;
}

[data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:last-child:has(iframe){
  height:0 !important;
  min-height:0 !important;
  max-height:0 !important;
  margin:0 !important;
  padding:0 !important;
  overflow:hidden !important;
}

[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .left-col-marker){
  display:flex !important;
  flex-direction:column !important;
  min-height:100% !important;
  height:100% !important;
  gap:0 !important;
}

[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .right-col-marker){
  display:flex !important;
  flex-direction:column !important;
  min-height:100% !important;
  height:100% !important;
  gap:0 !important;
}

[data-testid="stVerticalBlockBorderWrapper"]:has(.right-panel-marker) > div{
  min-height:0 !important;
  border:none !important;
  border-radius:0 !important;
  box-sizing:border-box !important;
}

[data-testid="stVerticalBlockBorderWrapper"]:has(.left-panel-marker) > div{
  height:var(--left-panel-h) !important;
  max-height:var(--left-panel-h) !important;
  overflow-y:auto !important;
  overflow-x:hidden !important;
  -webkit-overflow-scrolling:touch;
  overscroll-behavior:contain;
  padding:0 !important;
}

.left-inner-pad{
  padding:4px 14px 10px !important;
}

[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .left-col-marker)
  > [data-testid="stElementContainer"]:has(.left-analyze-dock-marker){
  margin-top:auto !important;
  padding:8px 14px 30px !important;
  background:transparent !important;
  flex:0 0 auto !important;
}

[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .left-col-marker)
  > [data-testid="stElementContainer"]:has(.left-analyze-dock-marker) [data-testid="stVerticalBlock"]{
  gap:0 !important;
}

[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .left-col-marker)
  > [data-testid="stElementContainer"]:has(.left-analyze-dock-marker) [data-testid="stElementContainer"]:has(.left-analyze-dock-marker){
  height:0 !important;
  min-height:0 !important;
  max-height:0 !important;
  overflow:hidden !important;
  margin:0 !important;
  padding:0 !important;
}

[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .left-col-marker)
  > [data-testid="stElementContainer"]:last-child:not(:has(.left-analyze-dock-marker)){
  margin:0 !important;
  padding:0 !important;
  background:transparent !important;
}

.left-analyze-spacer{
  height:0 !important;
}

[data-testid="stVerticalBlockBorderWrapper"]:has(.right-panel-marker) > div{
  overflow-y:auto !important;
  overflow-x:hidden !important;
  -webkit-overflow-scrolling:touch;
  overscroll-behavior:contain;
  padding:8px 14px 8px !important;
  scroll-padding-bottom:8px !important;
}

.stButton{
  margin:0 !important;
  padding:0 !important;
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

.placeholder-guide{
  max-width:420px;
  text-align:left;
  color:#374151;
}

.placeholder-title{
  font-size:1.05rem;
  font-weight:900;
  color:#111827;
  margin-bottom:0.8rem;
}

.placeholder-step{
  display:grid;
  grid-template-columns:auto 1fr;
  gap:0 0.45rem;
  font-size:0.95rem;
  line-height:1.5;
  margin-bottom:0.55rem;
}

.step-label{
  font-weight:900;
  color:#111827;
  white-space:nowrap;
}

.step-optional{
  display:inline-block;
  padding:0.04rem 0.38rem;
  border-radius:999px;
  background:#e5e7eb;
  color:#6b7280;
  font-size:0.75rem;
  font-weight:700;
  vertical-align:middle;
  margin-right:0.2rem;
}

.placeholder-action{
  display:inline-block;
  padding:0.06rem 0.42rem;
  border-radius:999px;
  background:#f59e0b;
  color:#111827;
  font-weight:900;
}

.placeholder-example{
  margin-top:0.85rem;
  font-size:0.9rem;
  color:#6b7280;
  line-height:1.45;
}

.running-state{
  min-height:calc(var(--panel-h) - 80px);
  display:flex;
  flex-direction:column;
  justify-content:center;
  gap:0.7rem;
  padding:1rem 0.2rem;
}

.running-badge{
  display:inline-block;
  width:fit-content;
  padding:0.18rem 0.55rem;
  border-radius:999px;
  background:#f59e0b;
  color:#111827;
  font-size:0.8rem;
  font-weight:900;
}

.running-title{
  font-size:1.15rem;
  font-weight:900;
  color:#111827;
}

.running-copy{
  font-size:0.95rem;
  line-height:1.45;
  color:#4b5563;
  max-width:560px;
}

.running-steps{
  display:grid;
  gap:0.45rem;
}

.running-step{
  padding:0.65rem 0.8rem;
  border:1px solid #dde2e8;
  border-radius:10px;
  background:#f8f9fb;
  color:#374151;
  font-size:0.92rem;
  font-weight:700;
}

.running-step-label{
  font-size:0.88rem;
  font-weight:600;
  color:#4b5563;
}
.running-progress-track{
  width:100%;
  height:10px;
  background:#e5e7eb;
  border-radius:999px;
  overflow:hidden;
}
.running-progress-bar{
  height:100%;
  background:var(--data-blue);
  border-radius:999px;
  transition:width 1s linear;
}
.running-progress-pct{
  font-size:0.82rem;
  font-weight:700;
  color:var(--muted);
  text-align:right;
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
  margin:0 !important;
  padding:0 !important;
  line-height:1 !important;
  overflow:visible !important;
}
/* Title row columns: collapse vertical gaps */
[data-testid="stHorizontalBlock"]:has(.top-title-wrap){
  margin:0 !important; padding:0 !important;
  gap:0 !important;
  flex:0 0 auto !important;
  height:auto !important;
  min-height:0 !important;
  max-height:none !important;
  overflow:visible !important;
}

[data-testid="stElementContainer"]:has(.top-title-wrap){
  flex:0 0 auto !important;
  height:auto !important;
  min-height:0 !important;
  max-height:none !important;
}
.top-title{
  margin:0 !important;
  padding:0 0 0.08rem !important;
  line-height:1 !important;
  font-size:1.95rem;
  font-weight:900;
  letter-spacing:0.02em;
  color:var(--text);
  display:inline-block;
  overflow:visible !important;
}

/* Restart button: same row as title */
[data-testid="column"]:has(.top-key-marker),
[data-testid="stColumn"]:has(.top-key-marker){
  display:flex !important;
  align-items:center !important;
  min-width:0 !important;
}

[data-testid="stElementContainer"]:has(.top-key-marker){
  height:0 !important;
  min-height:0 !important;
  max-height:0 !important;
  margin:0 !important;
  padding:0 !important;
  overflow:hidden !important;
}

[data-testid="column"]:has(.top-key-marker) [data-testid="stTextInput"],
[data-testid="stColumn"]:has(.top-key-marker) [data-testid="stTextInput"]{
  width:100% !important;
}

[data-testid="column"]:has(.top-key-marker) [data-testid="stTextInput"] input,
[data-testid="stColumn"]:has(.top-key-marker) [data-testid="stTextInput"] input{
  height:34px !important;
  min-height:34px !important;
  border-radius:10px !important;
  border:1px solid #d7dbe1 !important;
  background:#ffffff !important;
  font-size:0.84rem !important;
  font-weight:700 !important;
}

[data-testid="column"]:has(.restart-action-marker),
[data-testid="stColumn"]:has(.restart-action-marker){
  display:flex !important;
  justify-content:flex-end !important;
  align-items:center !important;
  min-width:0 !important;
}

[data-testid="stElementContainer"]:has(.restart-action-marker){
  height:0 !important;
  min-height:0 !important;
  max-height:0 !important;
  margin:0 !important;
  padding:0 !important;
  overflow:hidden !important;
}

[data-testid="column"]:has(.restart-action-marker) [data-testid="stButton"],
[data-testid="stColumn"]:has(.restart-action-marker) [data-testid="stButton"]{
  width:100% !important;
}

[data-testid="column"]:has(.restart-action-marker) [data-testid="stBaseButton-secondary"],
[data-testid="stColumn"]:has(.restart-action-marker) [data-testid="stBaseButton-secondary"]{
  width:100% !important;
}

[data-testid="column"]:has(.restart-action-marker) [data-testid="stBaseButton-secondary"] button,
[data-testid="stColumn"]:has(.restart-action-marker) [data-testid="stBaseButton-secondary"] button{
  width:100% !important;
  min-width:140px !important;
  height:34px !important;
  padding:0.28rem 0.95rem !important;
  border-radius:10px !important;
  border:1px solid #d7dbe1 !important;
  background:linear-gradient(180deg, #ffffff 0%, #f3f5f8 100%) !important;
  color:#1f2937 !important;
  font-size:0.84rem !important;
  font-weight:900 !important;
  white-space:nowrap !important;
  box-shadow:0 1px 2px rgba(17,24,39,0.06) !important;
}

[data-testid="column"]:has(.restart-action-marker) [data-testid="stBaseButton-secondary"] button:hover,
[data-testid="stColumn"]:has(.restart-action-marker) [data-testid="stBaseButton-secondary"] button:hover{
  border-color:#c5ccd6 !important;
  background:linear-gradient(180deg, #f8fafc 0%, #e9edf3 100%) !important;
}

[data-testid="stTabs"]{
  margin:0 !important;
}

[data-testid="stTabs"] > div{
  margin:0 !important;
}

[data-testid="stTabs"] [data-baseweb="tab-list"]{
  display:flex !important;
  gap:6px !important;
  flex-wrap:nowrap !important;
  align-items:stretch !important;
  margin:-6px 0 2px !important;
  padding:0 !important;
  border-bottom:none !important;
  width:100% !important;
  background:transparent !important;
}

[data-testid="stTabs"] [data-baseweb="tab"]{
  margin:0 !important;
  height:32px !important;
  min-height:32px !important;
  padding:4px 12px !important;
  border-radius:8px !important;
  border:1px solid #d7dbe1 !important;
  background:linear-gradient(180deg, #f7f8fa 0%, #eff2f6 100%) !important;
  cursor:pointer !important;
  color:#2b3442 !important;
  font-size:0.84rem !important;
  font-weight:800 !important;
  white-space:nowrap !important;
  flex:1 1 0 !important;
  justify-content:center !important;
  box-shadow:0 1px 0 rgba(17,24,39,0.03) !important;
}

[data-testid="stTabs"] [data-baseweb="tab"]:hover{
  background:linear-gradient(180deg, #f0f3f7 0%, #e7ebf0 100%) !important;
  border-color:#cfd6de !important;
}

[data-testid="stTabs"] [aria-selected="true"]{
  background:linear-gradient(180deg, #e1e5ea 0%, #d4dae2 100%) !important;
  border-color:#c4ccd6 !important;
  color:#1f2937 !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,0.55) !important;
}

[data-testid="stTabs"] [data-baseweb="tab-highlight"]{
  display:none !important;
}

[data-testid="stTabs"] [data-baseweb="tab-panel"]{
  padding:0 !important;
  margin:0 !important;
  overflow:visible !important;
}

[data-testid="stTabs"] [data-baseweb="tab-panel"] > div{
  padding-top:0 !important;
  margin-top:0 !important;
  overflow:visible !important;
}

/* Left input tabs: equal widths + red required star on Map tab */
[data-testid="stTabs"]:first-of-type [data-baseweb="tab-list"] [data-baseweb="tab"]{
  flex:1 1 0 !important;
}

[data-testid="stTabs"]:first-of-type [data-baseweb="tab-list"] [data-baseweb="tab"]:first-child{
  color:transparent !important;
  position:relative !important;
}

[data-testid="stTabs"]:first-of-type [data-baseweb="tab-list"] [data-baseweb="tab"]:first-child::before{
  content:"Map";
  color:#2b3442;
  font-weight:800;
}

[data-testid="stTabs"]:first-of-type [data-baseweb="tab-list"] [data-baseweb="tab"]:first-child::after{
  content:"*";
  color:#ef4444;
  font-weight:900;
  margin-left:2px;
  vertical-align:top;
}

[data-testid="stTabs"]:first-of-type [data-baseweb="tab-list"] [aria-selected="true"]:first-child::before{
  color:#1f2937;
}

[data-testid="stPlotlyChart"]{
  margin:0 !important;
}

[data-testid="stPlotlyChart"] > div{
  margin:0 !important;
}

[data-testid="stElementContainer"]:has(> [data-testid="stPlotlyChart"]){
  margin:0 !important;
  padding:0 !important;
  margin-bottom:-0.45rem !important;
}

.binning-heading{
  font-size:0.96rem;
  font-weight:900;
  color:#111827;
  margin:0 0 0.2rem 0;
}

.binning-heading.uploaded-heading{
  font-size:1.08rem;
}

.binning-heading.tight-top{
  margin:-0.9rem 0 0.05rem 0;
}

.binning-heading.tight-top.larger{
  font-size:1.08rem;
}

.binning-method-name{
  font-size:0.96rem;
  font-weight:900;
  color:#1f2937;
  line-height:1.25;
  margin:0 0 0.12rem 0;
}

.binning-method-name.uploaded{
  color:#111827;
}

.binning-gap-collapser{
  height:0;
  margin-top:-1.35rem;
}

.binning-method-list-top{
  height:0;
  margin-top:-0.4rem;
}

.binning-method-divider{
  height:1px;
  background:rgba(17,24,39,0.08);
  margin:0.16rem 0 0.35rem;
}

.similarity-metric-row{
  display:flex;
  align-items:center;
  gap:0.32rem;
  color:#1f2937;
  font-size:0.92rem;
  line-height:1.35;
  margin:0.12rem 0;
}

.similarity-metric-label{
  font-weight:700;
}

.similarity-tooltip{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  width:16px;
  height:16px;
  border-radius:50%;
  background:#eef2f7;
  border:1px solid #cbd5e1;
  color:#475569;
  font-size:0.72rem;
  font-weight:900;
  cursor:help;
  flex:0 0 auto;
}

.similarity-metric-value{
  color:#374151;
}

.overview-card{
  border:1px solid #dde2e8;
  border-radius:12px;
  background:linear-gradient(180deg, #fcfcfd 0%, #f7f9fc 100%);
  padding:0.95rem 1rem;
  margin-bottom:0.7rem;
}

.overview-score-card{
  border:1px solid #f6d08b;
  border-radius:12px;
  background:linear-gradient(180deg, #fffaf0 0%, #fff4db 100%);
  padding:0.85rem 1rem;
  margin-bottom:0.7rem;
}

.overview-score-copy{
  color:#7c4a03;
  font-size:0.98rem;
  font-weight:900;
}

.overview-score-note{
  color:#7c4a03;
  font-size:0.82rem;
  line-height:1.4;
  margin-top:0.28rem;
}

.overview-score-note-wrap{
  display:flex;
  flex-wrap:wrap;
  gap:0.45rem;
  margin-top:0.42rem;
}

.overview-score-pill{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  padding:0.28rem 0.62rem;
  border-radius:999px;
  font-size:0.82rem;
  font-weight:900;
  letter-spacing:0.01em;
}

.overview-score-pill.good{
  background:#dcfce7;
  color:#166534;
}

.overview-score-pill.bad{
  background:#fee2e2;
  color:#991b1b;
}

.overview-score-value{
  color:#c2410c;
}

.overview-section-title{
  font-size:1rem;
  font-weight:900;
  color:#111827;
  margin:0 0 0.38rem 0;
}

.overview-copy{
  font-size:0.97rem;
  line-height:1.55;
  color:#1f2937;
}

.overview-highlight{
  display:inline;
  padding:0.05rem 0.26rem;
  border-radius:6px;
  background:#fff0b8;
  color:#6b4f00;
  font-weight:900;
}

.criterion-card{
  border:1px solid #dde2e8;
  border-radius:12px;
  background:#fbfcfd;
  padding:1rem 1.05rem;
  margin-bottom:0.7rem;
  box-shadow:0 1px 2px rgba(17,24,39,0.04);
  min-height:208px;
}

.criterion-head{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:0.8rem;
  margin-bottom:0.7rem;
}

.criterion-head-left{
  display:flex;
  align-items:center;
  gap:0.45rem;
  flex-wrap:wrap;
}

.criterion-title{
  font-size:1rem;
  font-weight:900;
  color:#111827;
}

.criterion-chip-wrap{
  flex:0 0 auto;
}

.criterion-chip{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  padding:0.18rem 0.55rem;
  border-radius:999px;
  font-size:0.74rem;
  font-weight:900;
  letter-spacing:0.02em;
}

.criterion-chip.good{
  background:#dcfce7;
  color:#166534;
}

.criterion-chip.bad{
  background:#fee2e2;
  color:#991b1b;
}

.criterion-chip.neutral{
  background:#eef2f7;
  color:#475569;
}

.criterion-chip.meta{
  background:#e0f2fe;
  color:#075985;
}

.criterion-topic-chip{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  padding:0.16rem 0.5rem;
  border-radius:999px;
  background:#eef2f7;
  color:#475569;
  font-size:0.72rem;
  font-weight:900;
  letter-spacing:0.02em;
}

.criterion-row{
  margin-bottom:0.68rem;
}

.criterion-row:last-child{
  margin-bottom:0;
}

.criterion-key{
  font-size:0.73rem;
  font-weight:900;
  color:#6b7280;
  letter-spacing:0.05em;
  text-transform:uppercase;
  margin-bottom:0.18rem;
}

.criterion-body{
  font-size:0.94rem;
  line-height:1.52;
  color:#374151;
}

[data-testid="stMultiSelect"] [data-baseweb="tag"]{
  background:#eef2f7 !important;
  color:#374151 !important;
}
</style>
""",
        unsafe_allow_html=True,
    )
