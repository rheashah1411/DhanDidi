"""Accessible visual system for DhanDidi."""

CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;600;700&family=Nunito+Sans:wght@400;600;700;800&display=swap');
:root { --navy:#12304A; --teal:#087F7B; --turquoise:#20B8B2; --sky:#EAF7FA; --ink:#17324D; --muted:#52697C; --white:#FFFFFF; --warning:#FFF4DE; }
html, body, [class*="css"] { font-family:'Nunito Sans','Noto Sans Devanagari',sans-serif; color:var(--ink); }
.stApp { background:linear-gradient(150deg,#F8FCFD 0%,#EFFAFA 52%,#F7FBFF 100%); }
[data-testid="stHeader"] { background:transparent; }
.block-container { max-width:960px; padding:2rem 1.4rem 5rem; }
.hero { background:linear-gradient(135deg,var(--navy),#125B70 62%,var(--teal)); color:white; border-radius:28px; padding:2.2rem 2.4rem; box-shadow:0 18px 45px rgba(18,48,74,.15); margin-bottom:1.5rem; }
.brand { display:flex; align-items:center; gap:.8rem; font-weight:800; font-size:1.25rem; letter-spacing:.02em; }
.brand-mark { display:grid; place-items:center; width:46px; height:46px; border-radius:15px; background:rgba(255,255,255,.16); font-size:1.55rem; }
.hero h1 { color:white !important; font-size:clamp(2rem,6vw,3.4rem); line-height:1.06; margin:.9rem 0 .55rem; font-weight:800; }
.hero p { color:#E6FAFA; font-size:1.12rem; line-height:1.65; max-width:700px; margin:0; }
.language-panel { background:white; border:2px solid #BFE8E8; border-radius:20px; padding:.45rem 1.1rem .8rem; box-shadow:0 8px 25px rgba(18,48,74,.07); }
.language-panel-title { color:var(--navy); font-weight:800; font-size:1.2rem; margin:.25rem 0 -.1rem; }
label, [data-testid="stWidgetLabel"] p { font-size:1.05rem !important; font-weight:700 !important; color:var(--navy) !important; }
[data-baseweb="select"] > div { min-height:54px; border:2px solid #78C9C7 !important; border-radius:14px !important; background:white !important; font-size:1.1rem; }
.privacy { background:#E6F7F3; color:#174F51; border-radius:14px; padding:.8rem 1rem; margin:1rem 0 1.4rem; font-size:1rem; line-height:1.5; }
.section-card { background:white; border:1px solid #D9ECEF; border-radius:22px; padding:1.45rem 1.55rem; box-shadow:0 8px 28px rgba(18,48,74,.065); margin:.9rem 0; }
.section-card h2 { color:var(--navy); font-size:1.4rem; margin:0 0 .7rem; }
.section-card p, .section-card li { font-size:1.06rem; line-height:1.65; }
.doc-card { background:linear-gradient(135deg,#E7FAF7,#EDF6FF); border:2px solid #68CFCB; border-radius:24px; padding:1.55rem 1.7rem; margin:1.4rem 0 1rem; box-shadow:0 10px 30px rgba(8,127,123,.12); }
.doc-label { color:#326078; font-weight:700; font-size:1.05rem; }
.doc-type { color:var(--navy); font-weight:800; font-size:clamp(1.5rem,4vw,2.1rem); margin:.25rem 0 .4rem; }
.confidence { display:inline-block; background:white; color:#086B68; border:1px solid #83D8D4; border-radius:999px; padding:.32rem .75rem; font-weight:700; }
.detail-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:.8rem; }
.detail { background:#F4FAFC; border-radius:14px; padding:.85rem 1rem; border-left:4px solid var(--turquoise); }
.detail-label { color:var(--muted); font-size:.9rem; font-weight:700; }
.detail-value { color:var(--navy); font-size:1.05rem; font-weight:800; overflow-wrap:anywhere; }
.risk { background:var(--warning); border-color:#F3D18B; }
.status { color:#467080; font-size:.9rem; text-align:right; margin:.2rem .2rem .6rem; }
[data-testid="stFileUploader"] { background:white; border:2px dashed #62BFBC; border-radius:18px; padding:.65rem; }
[data-testid="stFileUploaderDropzone"] { min-height:150px; background:#F4FCFC; border-radius:14px; }
.stButton > button, .stDownloadButton > button { min-height:56px; border-radius:15px !important; font-size:1.08rem !important; font-weight:800 !important; padding:.75rem 1.35rem !important; width:100%; }
.stButton > button[kind="primary"] { background:linear-gradient(135deg,var(--teal),#0B9993) !important; border:0 !important; color:white !important; box-shadow:0 8px 20px rgba(8,127,123,.25); }
.stDownloadButton > button { border:2px solid var(--teal) !important; color:var(--teal) !important; background:white !important; }
.steps { display:grid; grid-template-columns:repeat(3,1fr); gap:.8rem; }
.step { background:#F0F9FB; color:var(--navy); border-radius:15px; padding:1rem; font-weight:700; line-height:1.45; }
.footer-note { color:#5B7181; text-align:center; margin-top:2rem; font-size:.95rem; line-height:1.55; }
@media (max-width:640px) { .block-container{padding:1rem .75rem 4rem}.hero{padding:1.6rem 1.25rem;border-radius:22px}.section-card{padding:1.15rem}.steps{grid-template-columns:1fr}.doc-card{padding:1.25rem}.status{text-align:left} }
@media (prefers-reduced-motion:reduce) { * { scroll-behavior:auto !important; transition:none !important; } }
</style>
"""
