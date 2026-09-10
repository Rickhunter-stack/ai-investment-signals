from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st

DB = Path('data/veille.db')

st.set_page_config(page_title='AI Investment Signals', layout='wide')
st.title('AI Investment Signals')
st.caption('Radar prospectif IA - robotique - biotech. Aucun signal n’est une recommandation d’achat.')

if not DB.exists():
    st.warning('Base absente. Lancez `python run.py --step all`.')
    st.stop()

conn = sqlite3.connect(DB)
companies = pd.read_sql_query('SELECT * FROM companies ORDER BY theme, role, priority, ticker', conn)
market = pd.read_sql_query('SELECT * FROM market ORDER BY date', conn)

latest = market.sort_values('date').groupby('ticker').tail(1)[['ticker','date','close','volume']]
view = companies.merge(latest, on='ticker', how='left')

c1,c2,c3 = st.columns(3)
c1.metric('Sociétés suivies', len(view))
c2.metric('Anchors', int((view.role=='anchor').sum()))
c3.metric('Enablers / emerging', int((view.role!='anchor').sum()))

st.subheader('Radar')
theme = st.multiselect('Thème', sorted(view.theme.unique()), default=sorted(view.theme.unique()))
role = st.multiselect('Rôle', sorted(view.role.unique()), default=sorted(view.role.unique()))
filtered = view[view.theme.isin(theme) & view.role.isin(role)].copy()
st.dataframe(filtered[['ticker','company','theme','role','subtheme','priority','date','close']], use_container_width=True, hide_index=True)

st.subheader('Chaînes de valeur')
for t, label in [('ai_semi','IA / semi-conducteurs'),('robotics','Robotique'),('biotech_medtech','Biotech / medtech')]:
    st.markdown(f'### {label}')
    tdf = filtered[filtered.theme==t]
    if not tdf.empty:
        st.dataframe(tdf[['ticker','company','role','subtheme','close']], use_container_width=True, hide_index=True)

st.subheader('Évolution des cours')
selected = st.multiselect('Tickers', filtered.ticker.tolist(), default=filtered.ticker.tolist()[:5])
if selected:
    chart = market[market.ticker.isin(selected)].pivot(index='date', columns='ticker', values='close')
    st.line_chart(chart)

conn.close()
