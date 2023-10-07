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
                            dcc.Input(id = 'graph_name', placeholder = 'Type something..'),
                            html.P('Choose reference & maintinance lines:'),
                            html.Div([
                                dcc.Dropdown(['None', 'Dry', 'Wet'], 'None', id='demo_dropdown')
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
                dcc.Store(id = 'data_store_dfs'),
                dcc.Store(id = 'sliders_store'),
], id = 'layout')



def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')), skiprows=10)
        elif 'xls' in filename:
            df = pd.read_excel(io.BytesIO(decoded), skiprows=10)
    except Exception as e:
        print(e)
        return None, None
    return [filename, df]




@app.callback(
    Output('sliders_store', 'data'),
    Input('data_dropdown', 'value'),
    Input('start_slider', 'value'),
    Input('end_slider', 'value'),
    State('sliders_store', 'data')
)
def update_sliders(selected_data, start, end, state):
    if selected_data:
        if state != None:
            data = state
        else:
            data = {}
        data[selected_data] = [start, end]
    else:
        data = {}
    return data



@app.callback(
    [Output('start_slider', 'value'),
     Output('end_slider', 'value')],
    Input('data_dropdown', 'value'),
    State('sliders_store', 'data')
)
def update_sliders_value(selected_data, sliders):
    try:
        values = sliders[selected_data]
    except:
        values = [0, 0]
    return values




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
            result = parse_contents(c, n, d)
            if result[0] is not None and result[1] is not None:
                names.append(result[0])
                dfs.append(result[1].to_dict('records'))
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
    Input('sliders_store', 'data'),

    Input('demo_dropdown', 'value')

)
def update_graph(names, data, title, selected_data, sliders, demo_dropdown):
    if data != None and names != None:
        dataframe = pd.DataFrame()
        for j in range(len(data)):
            df = pd.DataFrame.from_dict(data[j])
            columns = df.columns
            columns = columns[2:]
            columns2 = ['Distance', 'Friction']
            for i in columns:
                columns2.append(i)
            df.columns = columns2
            if names[j] in sliders.keys():
                start = sliders[names[j]][0]
                end = sliders[names[j]][1]
                if end > 0:
                    df = df.iloc[start: (end - end * 2)]
                else:
                    df = df.iloc[start:]
                if start > 0:
                    df['Distance'] = df['Distance'].apply(lambda x: x - int(df['Distance'].iloc[0]))
            df['Files'] = names[j].split('.')[0]
            dataframe = pd.concat([dataframe, df])
        x = dataframe.columns[0]
        y = dataframe.columns[1]
        try:
            fig = px.line(dataframe, x=x, y=y, color='Files')
        except:
            fig = blank_fig()
    else:
        fig = blank_fig()

    if demo_dropdown == 'None' or demo_dropdown is None:
        fig.update_layout(
            margin=dict(t=30, b=0, l=0, r=0),
            title=title,
            plot_bgcolor="#f5f5f5",
            paper_bgcolor="#f5f5f5",
            title_x=0.5
        )
    else:
        if title == None:
            title = ""
        fig.update_layout(
            margin=dict(t=30, b=0, l=0, r=0),
            title=(title + ' /w ' + demo_dropdown),
            plot_bgcolor="#f5f5f5",
            paper_bgcolor="#f5f5f5",
            title_x=0.5
        )

    if demo_dropdown == 'None' or demo_dropdown is None:
        return fig
    elif 'Dry' in demo_dropdown:
        fig.add_hline(y=0.5, line_width=2, line_color='black')
        fig.add_hline(y=0.3, line_width=2, line_color='red')
        return fig
    elif 'Wet' in demo_dropdown:
        fig.add_hline(y=0.6, line_width=2, line_color='black')
        fig.add_hline(y=0.4, line_width=2, line_color='red')
        return fig

    return fig


if __name__ == '__main__':
    app.run_server(debug=False, port=8071)
