
import dash
from dash import html
import dash_cytoscape as cyto
import pandas as pd

file_path = "Proyectos MM.xlsx"
df_oscs = pd.read_excel(file_path, sheet_name="OSCs")
df_fundaciones = pd.read_excel(file_path, sheet_name="Fundaciones")
df_rel = pd.read_excel(file_path, sheet_name="Proyectos Financiados")

df_aristas = df_rel[['Id de la organización financiera', 'Ids OSC', 'Fondos concedidos']].copy()
df_aristas.columns = ['source', 'target', 'weight']
df_aristas['source'] = df_aristas['source'].astype(str)
df_aristas['target'] = df_aristas['target'].astype(str)

df_oscs = df_oscs.copy()
df_fundaciones = df_fundaciones.copy()
df_oscs['Organización_Id'] = df_oscs['Organización_Id'].astype(str)
df_fundaciones['Organización_Id'] = df_fundaciones['Organización_Id'].astype(str)
df_oscs['tipo'] = 'Donataria'
df_fundaciones['tipo'] = 'Donante'

df_nodos = pd.concat([
    df_oscs[['Organización_Id', 'Organización_Nombre', 'tipo']],
    df_fundaciones[['Organización_Id', 'Organización_Nombre', 'tipo']]
], ignore_index=True)
df_nodos.columns = ['id', 'label', 'tipo']

monto_donado = df_aristas.groupby('source')['weight'].sum().reset_index()
monto_donado.columns = ['id', 'monto_donado']
monto_donado['id'] = monto_donado['id'].astype(str)

monto_recibido = df_aristas.groupby('target')['weight'].sum().reset_index()
monto_recibido.columns = ['id', 'monto_recibido']
monto_recibido['id'] = monto_recibido['id'].astype(str)

df_nodos = df_nodos.merge(monto_donado, on='id', how='left')
df_nodos = df_nodos.merge(monto_recibido, on='id', how='left')
df_nodos['monto_donado'] = df_nodos['monto_donado'].fillna(0)
df_nodos['monto_recibido'] = df_nodos['monto_recibido'].fillna(0)

nodos_validos = df_nodos[
    (df_nodos['monto_donado'] > 0) | (df_nodos['monto_recibido'] > 0)
].copy()

conexiones = df_aristas.groupby('target').size().reset_index(name='conexiones_recibidas')
conexiones['target'] = conexiones['target'].astype(str)

nodos_validos = nodos_validos.merge(conexiones, left_on='id', right_on='target', how='left')
nodos_validos['conexiones_recibidas'] = nodos_validos['conexiones_recibidas'].fillna(0)

nodos_validos['destacada'] = False
mask = (nodos_validos['tipo'] == 'Donataria') & (nodos_validos['conexiones_recibidas'] >= 2)
nodos_validos.loc[mask, 'destacada'] = True

ids_validos = set(nodos_validos['id'])
aristas_validas = df_aristas[
    df_aristas['source'].isin(ids_validos) &
    df_aristas['target'].isin(ids_validos)
]

nodes = []
for _, row in nodos_validos.iterrows():
    size = 30
    if row['tipo'] == 'Donante':
        size = max(30, min(80, row['monto_donado'] / 1e6))

    classes = row['tipo'].lower()
    if row['destacada']:
        classes += ' destacada'

    nodes.append({
        'data': {
            'id': str(row['id']),
            'label': row['label']
        },
        'classes': classes,
        'style': {'width': size, 'height': size}
    })

edges = [
    {
        'data': {
            'source': row['source'],
            'target': row['target'],
            'weight': row['weight']
        }
    }
    for _, row in aristas_validas.iterrows()
]

elements = nodes + edges

app = dash.Dash(__name__)
app.layout = html.Div([
    cyto.Cytoscape(
        id='red-donaciones',
        elements=elements,
        layout={'name': 'cose'},
        style={'position': 'fixed', 'top': 0, 'left': 0, 'right': 0, 'bottom': 0},
        stylesheet=[
            {
                'selector': 'node',
                'style': {
                    'label': 'data(label)',
                    'color': 'white',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'font-size': 10
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

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))
    app.run(debug=False, host='0.0.0.0', port=port)
