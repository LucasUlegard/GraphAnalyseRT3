import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import base64
import io
import pandas as pd


app = dash.Dash(__name__) #, suppress_callback_exceptions=True)
server = app.server


def blank_fig():
    fig = go.Figure(go.Scatter(x=[], y = []))
    fig.update_layout(template = None,
                     plot_bgcolor="rgba( 0, 0, 0, 0)",
                     paper_bgcolor="rgba( 0, 0, 0, 0)",)
    fig.update_xaxes(showgrid = False, showticklabels = False, zeroline=False)
    fig.update_yaxes(showgrid = False, showticklabels = False, zeroline=False)

    return fig


config = {'displaylogo': False,
         'modeBarButtonsToAdd':['drawrect',
                                'eraseshape'
                               ]}



app.layout = html.Div([
                html.Div([
                    dcc.Upload(
                        id='uploadData',
                        children=html.Div([
                        html.Img(id = 'Upload_Icon', src = app.get_asset_url('upload.png')),
                        html.P(['Drag and Drop or ',html.A('Select a file to upload', id = 'Upload_Link')], id = 'Upload_Text'),
                        ], id = 'upload_section_content'),
                        multiple=True
                        ),
                ]),
                html.Div([
                    html.Div([
                        dcc.Graph(id = 'graph', figure = blank_fig(), config = config)
                    ], id = 'graph-container'),
                    html.Div([
                        html.Div([
                            html.P('Enter name of graph:'),
                            dcc.Input(id = 'graph_name', placeholder = 'Type sometihng..'),
                            html.P('Enable reference line:'),
                            html.Div([
                                dcc.Checklist(id = 'reference_toggle', options = ['Enabled']),
                                dcc.Slider(id = 'reference_slider', min = 0, max = 10, marks = None, tooltip={"placement": "bottom", "always_visible": True})
                            ])
                        ], id = 'thrd1', className = 'thrd'),
                        html.Div([
                            html.P('Select data:'),
                            dcc.Dropdown(id = 'data_dropdown', multi = False)
                        ], id = 'thrd2', className = 'thrd'),
                        html.Div([
                            html.P('Remove values from start:'),
                            dcc.Slider(
                                id = 'start_slider',
                                 min = 0,
                                 max = 10,
                                 marks = None,
                                 tooltip={"placement": "bottom", "always_visible": True},
                                 step = 1,
                                 value = 0),
                            html.P('Remove values from end:'),
                            dcc.Slider(
                                id = 'end_slider',
                                min = 0,
                                max = 10,
                                marks = None,
                                tooltip={"placement": "bottom", "always_visible": True},
                                 step = 1,
                                 value = 0),
                        ], id = 'thrd3', className = 'thrd')
                    ], id = 'inputs')
                ],id = 'graph-and-inputs'),
                dcc.Store(id = 'data_store_names'),
                dcc.Store(id = 'data_store_dfs')
], id = 'layout')



def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    return [filename, df]






@app.callback(Output('data_store_names', 'data'),
              Output('data_store_dfs', 'data'),
              Input('uploadData', 'contents'),
              State('uploadData', 'filename'),
              State('uploadData', 'last_modified'))
def update_graph(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        names = []
        dfs = []
        zipped = zip(list_of_contents, list_of_names, list_of_dates)
        for c, n, d in zipped:
            names.append(parse_contents(c, n, d)[0])
            dfs.append(parse_contents(c, n, d)[1].to_dict('records'))
        return names, dfs
    else:
        return None, None


@app.callback(
    Output('data_dropdown', 'options'),
    Input('data_store_names', 'data')
)
def update_options(data):
    if data:
        return data
    else:
        return []

@app.callback(
    [Output('reference_slider', 'min'),
     Output('reference_slider', 'max')],
    [Input('data_store_dfs', 'data'),
     Input('data_store_names', 'data'),
     Input('data_dropdown', 'value')]
)
def update_reference_min_max(data, names, selected_names):
    if data != None and names != None:
        mins = []
        maxs = []
        for i in data:
            mins.append(pd.DataFrame.from_dict(i)['y'].min())
            maxs.append(pd.DataFrame.from_dict(i)['y'].max())
        if len(mins) != 0 and len(maxs) != 0:
            min_val = min(mins)
            max_val = max(maxs)
            return [min_val, max_val]
        else:
            return [0, 10]
    else:
        return [0, 1]


@app.callback(
    Output('start_slider', 'min'),
    Output('start_slider', 'max'),
    Output('end_slider', 'min'),
    Output('end_slider', 'max'),
    Input('data_dropdown', 'value'),
    Input('data_store_dfs', 'data'),
    Input('data_store_names', 'data')
)
def update_slider_ranges(dropdown, data, names):
    if names != None and dropdown != None:
        index = names.index(dropdown)
        data = pd.DataFrame.from_dict(data[index])
        max_val = len(data)
        min_val = 0
        return min_val, max_val, min_val, max_val
    else:
        return 0, 1, 0, 1


@app.callback(
    Output('graph', 'figure'),
    Input('data_store_names', 'data'),
    Input('data_store_dfs', 'data'),
    Input('graph_name', 'value'),
    Input('data_dropdown', 'value'),
    Input('reference_toggle', 'value'),
    Input('reference_slider', 'value'),
    Input('start_slider', 'value'),
    Input('end_slider', 'value')
)
def update_graph(names, data, title, selected_data, toggle, reference_line, start, end):
    if data != None and names != None:
        dataframe = pd.DataFrame()
        for i in range(len(data)):
            df = pd.DataFrame.from_dict(data[i])
            if names[i] == selected_data:
                if end > 0:
                    df = df.iloc[start : (end-end*2)]
                else:
                    df = df.iloc[start :]
            df['name'] = names[i].split('.')[0]
            dataframe = pd.concat([dataframe, df])
        try:
            fig = px.line(dataframe, x = 'x', y = 'y', color = 'name')
        except:
            fig = blank_fig()
    else:
        fig = blank_fig()

    fig.update_layout(
        margin = dict(t = 30, b = 0, l = 0, r = 0),
        title = title,
        font = dict(color = 'white'),
        plot_bgcolor="#1e1e1e",
        paper_bgcolor="#1e1e1e",
        )
    fig.update_xaxes(gridcolor = 'grey')
    fig.update_yaxes(gridcolor = 'grey')
    if toggle == ['Enabled']:
        fig.add_hline(y = reference_line, line_width = 2, line_color = 'white')
    return fig




if __name__ == '__main__':
    app.run_server(debug=False)