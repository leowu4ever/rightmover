import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
import locale 
import plotly.graph_objects as go
import pydeck as pdk
import numpy as np

locale.setlocale(locale.LC_ALL, 'en_GB')
st.set_page_config(layout='wide')

@st.experimental_memo(show_spinner=False)
def query_db(query):
    connection = psycopg2.connect(dbname='postgres',
                        user='leowu',
                        password='wuliqun123',
                        host='rightmove.ci3wcic7jnj4.eu-west-2.rds.amazonaws.com',
                        port='5432')
    df = pd.read_sql(query, connection)
    connection.close()
    return df

def search_region(region):
    pass
    
def search_pc(pc):
    pc = pc.upper()
    query = f"""
            SELECT
                CASE
                    WHEN paon='' THEN saon || ', ' || INITCAP(street) || ', ' || INITCAP(town) || ', ' || INITCAP(county)
                    WHEN paon!='' THEN paon || ', ' || saon || ', ' || INITCAP(street) || ', ' || INITCAP(town) || ', ' || INITCAP(county)
                END AS address,
                deed_date as date, price_paid, latitude as lat, longitude as lon
            FROM price_paid JOIN postcode on price_paid.postcode=postcode.postcode
            WHERE price_paid.postcode='{pc}'
            ORDER BY date DESC, address
            """
    df = query_db(query)
    if df.shape[0] != 0:
        st.header(f'What we know about {pc}')
        st.pydeck_chart(
                pdk.Deck(
                    map_style='light',
                    initial_view_state=pdk.ViewState(
                        latitude=df.loc[0,'lat'],
                        longitude=df.loc[0,'lon'],
                        zoom=15.5,
                        height=200),
                    layers=[
                        pdk.Layer(
                            'ScatterplotLayer',
                            data=df.head(1)[['lat','lon']],
                            get_position=['lon', 'lat'],
                            auto_highlight=True,
                            get_radius=40,
                            opacity=0.1,
                            get_color='[107, 122, 241]',
                            stroked=True),
                    ],))
        with st.expander('History of property transaction'):
            
            df['price'] = df.price_paid.apply(lambda x: (locale.currency(x, grouping=True)).split('.')[0])
            df['year'] = df.date.apply(lambda x: x.year)
            
            fig = px.line(df.groupby('year', as_index=False)['price_paid'].mean().rename(columns={'year':'Year', 'price_paid':'Price'}), 
                          x='Year', 
                          y='Price',
                          markers=True,
                          line_shape='spline',
                          height=400,
                          title='Average sold price of each year')
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown(f"Totally there are **{df.shape[0]}** property transaction records from {df.date.min()}.\
                          The property sold most recently is **{df.sort_values('date').loc[0, 'address']}**,\
                          it was sold on **{df.sort_values('date').loc[0, 'date']}** at **{locale.currency(df.sort_values('date').loc[0, 'price_paid'], grouping=True).split('.')[0]}**. \
                          The average sold price of properties at this postcode is **{locale.currency(df.price_paid.mean(), grouping=True).split('.')[0]}**.\
                          The highest sold price of properties at this postcode is **{locale.currency(df.price_paid.max(), grouping=True).split('.')[0]}**,\
                          it is achieved by **{df.sort_values('price_paid', ascending=False, ignore_index=True).loc[0, 'address']}**\
                          on **{df.sort_values('price_paid', ascending=False, ignore_index=True).loc[0, 'date']}**.\
                          All transaction records from {df.date.min().year} are shown below.")
            
            hide_table_row_index = """
                        <style>
                        tbody th {display:none}
                        .blank {display:none}
                        </style>
                        """
            st.markdown(hide_table_row_index, unsafe_allow_html=True)
            st.table(df[['date', 'address', 'price']].rename(columns={'address':'Address', 'price':'Price', 'date':'Date'}))
        
        with st.expander('Property insights of nearby area', expanded=True):
            st.markdown(f"{pc.split(' ')[0]}")
            query = f"""
                    SELECT postcode, deed_date as date, price_paid
                    FROM price_paid
                    GROUP BY 
                    WHERE postcode like '{pc.split(' ')[0]}%'
                    """
            df = query_db(query)
            st.table(df)
            
    else:
        st.text(f'There is no information of {pc}, try again.')

        
st.sidebar.header('Rightmover')
pc = st.sidebar.text_input('Please enter a postcode or ask a question', placeholder='e.g. W1, highest sold price in London ')
st.sidebar.button('search', on_click=search_pc, kwargs={'pc': pc})