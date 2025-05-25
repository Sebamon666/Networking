#!/usr/bin/env python
# coding: utf-8

# In[1]:


import dash
from dash import html, dcc, Input, Output
import dash_cytoscape as cyto
import pandas as pd
import networkx as nx


# In[2]:


file_path = "C:\\Users\\Sebamon\\Desktop\\Proyectos MM.xlsx"
df_oscs = pd.read_excel(file_path, sheet_name="OSCs")
df_fundaciones = pd.read_excel(file_path, sheet_name="Fundaciones")
df_rel = pd.read_excel(file_path, sheet_name="Proyectos Financiados")


# In[3]:


# Eliminar Misión Multiplica y Fundación con ID 3 antes de cualquier construcción
df_oscs = df_oscs[df_oscs['Organización_Id'] != 1529]
df_fundaciones = df_fundaciones[~df_fundaciones['Organización_Id'].isin([1529, 3])]
df_rel = df_rel[df_rel['Ids OSC'] != 1529]


# In[16]:


# === App Dash con búsqueda y filtros ===
app = dash.Dash(__name__)
app.layout = html.Div([
    html.Div([
        dcc.Input(
            id='busqueda-nodo',
            type='text',
            placeholder='Buscar nodo...',
            style={'marginRight': '10px'}
        ),
        dcc.Dropdown(
            id='filtro-tipo',
            options=[
                {'label': 'Todas', 'value': 'todos'},
                {'label': 'Destacadas', 'value': 'destacada'}
            ],
            value='todos',
            clearable=False,
            style={'width': '200px'}
        )
    ], style={'padding': '10px', 'display': 'flex'}),

    cyto.Cytoscape(
        id='red-donaciones',
        elements=elements,
        layout={'name': 'cose'},
        style={'width': '100vw', 'height': '90vh'},
        stylesheet=[
            {
                'selector': 'node',
                'style': {
                    'label': 'data(label)',
                    'color': 'white',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'font-size': 8
                }
            },
            {
                'selector': '.donante',
                'style': {'background-color': '#0074D9'}
            },
            {
                'selector': '.donataria',
                'style': {'background-color': '#FF4136'}
            },
            {
                'selector': '.destacada',
                'style': {'background-color': '#B10DC9'}
            },
            {
                'selector': 'edge',
                'style': {
                    'curve-style': 'bezier',
                    'target-arrow-shape': 'triangle',
                    'width': 'mapData(weight, 100000, 10000000, 1, 10)',
                    'line-color': '#ccc',
                    'target-arrow-color': '#ccc'
                }
            }
        ]
    )
])

@app.callback(
    Output('red-donaciones', 'elements'),
    Input('busqueda-nodo', 'value'),
    Input('filtro-tipo', 'value')
)
def actualizar_red(busqueda, tipo):
    busqueda = (busqueda or "").strip().lower()
    tipo = tipo.lower()

    # 1. Filtrar nodos por búsqueda y tipo
    nodos_base = []
    for nodo in nodes:
        label = nodo['data']['label'].lower()
        clases = nodo['classes']
        incluir = True

        if busqueda and busqueda not in label:
            incluir = False
        if tipo != 'todos' and tipo not in clases:
            incluir = False

        if incluir:
            nodos_base.append(nodo['data']['id'])

    # 2. Encontrar nodos conectados a los nodos filtrados
    nodos_relacionados = set(nodos_base)
    for edge in edges:
        src = edge['data']['source']
        tgt = edge['data']['target']
        if src in nodos_base or tgt in nodos_base:
            nodos_relacionados.update([src, tgt])

    # 3. Filtrar nodos y edges finales
    nuevos_nodos = [n for n in nodes if n['data']['id'] in nodos_relacionados]
    nuevos_edges = [
        e for e in edges if e['data']['source'] in nodos_relacionados and e['data']['target'] in nodos_relacionados
    ]
    return nuevos_nodos + nuevos_edges

if __name__ == '__main__':
    app.run(debug=True, port=8051)


# In[14]:


# === TABLA 1: Grado de los Donantes (Top 15) ===
donantes = nodos_validos[nodos_validos['tipo'] == 'Donante'].copy()

grado_donantes = aristas_validas.groupby('source')['target'].nunique().reset_index()
grado_donantes.columns = ['id', 'grado']
grado_donantes['id'] = grado_donantes['id'].astype(str)

tabla_donantes = (
    donantes.merge(grado_donantes, on='id', how='left')[['label', 'grado']]
    .fillna(0)
    .sort_values(by='grado', ascending=False)
    .head(15)
)

# === TABLA 2: PageRank de las Donatarias (Top 15) ===
import networkx as nx
G = nx.DiGraph()
G.add_weighted_edges_from([
    (row['source'], row['target'], row['weight'])
    for _, row in aristas_validas.iterrows()
])

pagerank_scores = nx.pagerank(G, weight='weight')

donatarias = nodos_validos[nodos_validos['tipo'] == 'Donataria'].copy()
donatarias['pagerank'] = donatarias['id'].map(pagerank_scores).fillna(0)

tabla_donatarias = (
    donatarias[['label', 'pagerank']]
    .sort_values(by='pagerank', ascending=False)
    .head(15)
)

# === MOSTRAR TABLAS EN JUPYTER (sin índice) ===
from IPython.display import display

print("📌 Top 15 Donantes por Grado:")
display(tabla_donantes.reset_index(drop=True))

print("📌 Top 15 Donatarias por PageRank:")
display(tabla_donatarias.reset_index(drop=True))

from IPython.display import display, HTML

# Convertir tablas a HTML
html_donantes = tabla_donantes.reset_index(drop=True).to_html(index=False)
html_donatarias = tabla_donatarias.reset_index(drop=True).to_html(index=False)

# Mostrar lado a lado con estilo
display(HTML(f"""
<div style="display: flex; gap: 40px;">
  <div>
    <h4>📌 Top 15 Donantes por Grado</h4>
    {html_donantes}
  </div>
  <div>
    <h4>📌 Top 15 Donatarias por PageRank</h4>
    {html_donatarias}
  </div>
</div>
"""))


# In[ ]:


get_ipython().system('jupyter nbconvert --to script tu_nombre_de_archivo.ipynb')

