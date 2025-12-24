import dash
from dash.dependencies import Output, Input, State
from dash.exceptions import PreventUpdate
from dash import dcc,ALL,ctx,ClientsideFunction
import io
import base64
import pandas as pd
import band_plot_utils
import utilfuncs
import plotly.graph_objs as go
import numpy as np

mw_column_name = 'kDa'

def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif filename.endswith(('.txt','.tsv')):
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), delimiter = '\t')
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return None, None
    except:
        return None, None

    data = df.to_dict('records')
    keys = [{'name': i, 'id': i} for i in df.columns]

    return keys, data

def treat_blank_as_0(data: list[dict]) -> set:
    blank_contain_series = set()
    for i in range(len(data)):
        for key, val in data[i].items():
            if isinstance(val, str) and len(val.strip()) == 0:
                data[i][key] = 0
                blank_contain_series.add(key)
    return blank_contain_series


def callbacks(_app: dash.Dash, default_values):
    #============================================================
    #   Upload File
    #============================================================
    @_app.callback(
        Output('uploaded_filename', 'children'),
        Output('raw_data_table', 'columns'),
        Output('raw_data_table', 'data'),
        Output('store_fileinfo', 'data'),
        Input('upload_data', 'contents'),
        State('upload_data', 'filename'),
        prevent_initial_call = True
    )
    def upload_file(contents, filename):
        if contents is not None:
            keys, data = parse_contents(contents, filename)
            if keys == None or data == None:
                return "Invalid Data.", dash.no_update, dash.no_update, dash.no_update
            
            if keys[0]['id'] != 'kDa':
                message = "The first column must be 'kDa'."
                return message, dash.no_update, dash.no_update, dash.no_update

            # Blank check
            message = f"{filename}: ({len(keys) - 1} signal series * {len(data)} points)"
            #message = "{} is loaded. It conteines {} columns. The data is shown in 'Loaded Data' tab.".format(filename, len(keys))
            blank_contain_series = treat_blank_as_0(data) 
            if 0 < len(blank_contain_series):
                #message2 = " Note: {} contained blank cells. These blank cells will be treated as 0.".format(blank_contain_series)
                message2 = f"Note: The series {', '.join(blank_contain_series)} contains blank cells."
                message += "\n"
                message += message2
            return message, keys, data, {'filename': filename}
        else:
            return "Invalid Operation!", dash.no_update, dash.no_update, dash.no_update

    #============================================================
    #   Generate Image
    #============================================================
    @_app.callback(
        Output('resulted_image', 'src'),
        Output('generate_message', 'children'),
        Output("generate_log", "value"),
        Input('generate_button', 'n_clicks'),
        State('draw_type_radio', 'value'),

        State('raw_data_table', 'columns'),
        State('raw_data_table', 'data'),
        State('asis_lane_setting_table', 'data'),

        State('normalized_data_table', 'columns'),
        State('normalized_data_table', 'data'),

        State('signal_limit_slider', 'value'),
        State('marker_switch', 'value'),
        State('marker_mw_input', 'value'),
        
        State("lane_label_select", "value"),
        State("lane_label_rotate_switch", "value"),

        State('draw_mw_range_switch', 'value'),
        State('draw_mw_range_min', 'value'),
        State('draw_mw_range_max', 'value'),
        State('store_fileinfo', 'data'),

        State({'type': "detailed_settings", "key": ALL}, "value" ),

        prevent_initial_call = True,
    )
    def generate_image(n_clicks, draw_type, 
                       raw_columns, raw_data, asis_lane_setting_table_data,
                       normalized_columns, normalized_data,
                       signal_limit, marker_switch, marker_mw_input, lane_label_select, lane_label_rotate,
                       draw_mw_range_switch, draw_mw_range_min, draw_mw_range_max, fileinfo,
                       detailed_settings_value_list):
        # Process Arguments
        # XXX
        detailed_settings_id_list = [item['id']['key'] for item in ctx.states_list[-1]]
        detailed_settings = dict(zip(detailed_settings_id_list, detailed_settings_value_list))

        log_stream_details = io.StringIO()

        if draw_type == "as_is":
            data = raw_data
            columns = raw_columns
        elif draw_type == "normalized_new":
            data = normalized_data
            columns = normalized_columns

        if data == None or len(data) == 0:
            raise PreventUpdate

        column_names = [ x['name'] for x in columns ]
        dataframe = pd.DataFrame.from_records(data, columns = column_names)
        
        # set plot indices
        plot_indices = []
        if draw_type == "as_is" or draw_type == "normalized_new":
            for lane in asis_lane_setting_table_data:
                try:
                    index = column_names.index(lane['sample_name'])
                    plot_indices.append(index)
                except:
                    raise

        #XXX
        if signal_limit == 0:
            signal_limit = None
        print("Signal Limit:\t{}".format("Not specified" if signal_limit == None else signal_limit), file = log_stream_details)

        plot_obj = band_plot_utils.WesternBlotPlotUtil(dataframe, plot_indices, offset = 40)

        # Prepare labels
        plot_label_flag = False
        if lane_label_select != None:
            plot_label_flag = True
            plot_labels = []
            if lane_label_select == "lane_number":
                for i in range(len(asis_lane_setting_table_data)):
                    plot_labels.append("{}".format(i+1))
            elif lane_label_select == "user_defined":
                for record in asis_lane_setting_table_data:
                    plot_labels.append(record["label"])
            elif lane_label_select == "sample_name":
                for record in asis_lane_setting_table_data:
                    plot_labels.append(record["sample_name"])
            plot_obj.set_plot_labels(plot_labels)
        

        # Molecular Weight Range
        if draw_mw_range_switch == True:
            plot_obj.set_molecular_weight_range(draw_mw_range_min, draw_mw_range_max)
            print("Draw Range: \t Min: {} kDa, Max: {} kDa".format(draw_mw_range_min, draw_mw_range_max), file = log_stream_details)

        #MW marker
        draw_marker_line = False
        write_text = False
        marker_mw_list = []
        if isinstance(marker_switch, list):
            if "add_marker_line" in marker_switch:
                draw_marker_line = True
            if "add_mw_labels" in marker_switch:
                write_text = True

        if draw_marker_line == True or write_text == True:
            if marker_mw_input != None and isinstance(marker_mw_input, str) and 0 < len(marker_mw_input):
                try:
                    parsed = utilfuncs.parse_labeled_numbers(marker_mw_input)
                    plot_obj.set_marker_molecular_weights(parsed)
                except ValueError as e:
                    return None, "Error: Molecular Weights are invalid.", ""

        #--------------------------------------------------
        # Detailed Settings
        #--------------------------------------------------
        if "band_width_switch" in detailed_settings and detailed_settings["band_width_switch"] == True:
            band_width = detailed_settings["band_width"]
            band_spacing = detailed_settings["band_spacing"]
            plot_obj.set_band_width(band_width, band_spacing)
            print("Band Width:\t {} px".format(band_width), file = log_stream_details)
            print("Band Spacing:\t {} px".format(band_spacing), file = log_stream_details)
        else:
            plot_obj.set_band_width(default_values["band_width"], default_values["band_spacing"])
        if "offset_switch" in detailed_settings and detailed_settings["offset_switch"] == True:
            offset_top = detailed_settings["offset_top"]
            offset_bottom = detailed_settings["offset_bottom"]
            offset_left = detailed_settings["offset_left"]
            offset_right = detailed_settings["offset_right"]
            plot_obj.set_offset(offset_left = offset_left,offset_right = offset_right,
                                offset_top = offset_top, offset_bottom=offset_bottom)
            print("Margin Top:\t {} px".format(offset_top), file = log_stream_details)
            print("Margin Bottom:\t{} px".format(offset_bottom), file = log_stream_details)
            print("Margin Left:\t {} px".format(offset_left), file = log_stream_details)
            print("Margin Right:\t {} px".format(offset_right), file = log_stream_details)
        else:
            plot_obj.set_offset(
                offset_top = default_values["offset_top"], offset_bottom = default_values["offset_bottom"],
                offset_left= default_values["offset_left"],offset_right = default_values["offset_right"]
            )
        if "label_font_size_switch" in detailed_settings and detailed_settings["label_font_size_switch"] == True:
            lane_label_size = detailed_settings["lane_label_size"]
            mw_label_size = detailed_settings["mw_label_size"]
            plot_obj.set_font_size(lane_label_size, mw_label_size)
            print("Lane Label Size:\t {} pt".format(lane_label_size), file = log_stream_details)
            print("Molecular Weights Label Size:\t {} pt".format(mw_label_size), file = log_stream_details)
        else:
            plot_obj.set_font_size(label_font_size = default_values["lane_label_size"], marker_font_size = default_values["mw_label_size"])

        #--------------------------------------------------
        #   Finally, Generate Band Image
        #--------------------------------------------------
        plot_obj.draw_bands(
                signal_max = signal_limit, 
                draw_marker_line = draw_marker_line, 
                write_text = write_text, rotate_label = lane_label_rotate,
                write_label=plot_label_flag)

        img = plot_obj.get_image_obj()
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format = 'PNG')
        encoded_img = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

        log_stream = io.StringIO()
        from datetime import datetime
        now = datetime.now()
        print("DateTime: {}".format(now), file = log_stream)
        print("DataFile: {}".format(fileinfo['filename']), file = log_stream)
        print("Drawing Mode: {}".format("As Is" if draw_type == "as_is" else "Normalized"), file = log_stream)
        print("", file = log_stream)    # insert blank line
        print("Lane Order", file = log_stream)
        for lane_index, record in enumerate(asis_lane_setting_table_data):
            print("{}\t{}\t{}".format(
                lane_index+1, 
                record["sample_name"],
                record["label"] if record["label"] and 0 < len(record["label"]) else ""
            ), file = log_stream)
        print("", file = log_stream)    # insert blank line
        
        log_text = log_stream.getvalue()   
        log_stream.close()

        log_text += log_stream_details.getvalue()
        log_stream_details.close()
        return f"data:image/png;base64,{encoded_img}", "", log_text

    #================================================================================
    #   When New File is Loaded
    #================================================================================
    @_app.callback(
        Output('asis_lane_setting_table', 'data'),
        Input('raw_data_table', 'data'),
        Input('raw_data_table', 'columns'),
        Input('add_lane_button', 'n_clicks'),
        Input('lane_reset_button', 'n_clicks'),
        Input('lane_clear_button', 'n_clicks'),
        Input('lane_insert_button', 'n_clicks'),
        State('asis_lane_setting_table', 'data'),
        State('asis_lane_setting_table', 'selected_rows'),
        prevent_initial_call = True,
    )
    def update_asis_lane_setting_table(data, columns, 
                                       n_clicks_add_lane_button, n_clicks_lane_reset_button,
                                       n_clicks_lane_clear_button, n_clicks_lane_insert_button,
                                       lane_setting_data, selected_rows):
        if columns == None or isinstance(columns, list) == False:
            raise PreventUpdate
        if dash.ctx.triggered_id in {"raw_data_table", "lane_reset_button"}:
            ret = []
            for i, column in enumerate(columns):
                if not column['id'] == mw_column_name:
                    ret.append({'id': column['id'], 'sample_name': column['name'], 'label': None})
            return ret
        elif dash.ctx.triggered_id == "lane_clear_button":
            return []
        elif dash.ctx.triggered_id == "add_lane_button":
            ret = lane_setting_data
            for i, column in enumerate(columns):
                if not column['id'] == mw_column_name:
                    ret.append({'id': column['id'], 'sample_name': column['name'], 'label': None})
                    break
            return ret
        elif dash.ctx.triggered_id == "lane_insert_button":
            if isinstance(selected_rows, list) and 0 < len(selected_rows):
                index = selected_rows[0]
                ret = lane_setting_data
                for i, column in enumerate(columns):
                    if not column['id'] == mw_column_name:
                        ret.insert(index, {'id': column['id'], 'sample_name': column['name'], 'label': None})
                        break
                return ret
            else:
                return dash.no_update
        else:
            return dash.no_update

    @_app.callback(
        Output('asis_lane_setting_table', 'dropdown'),
        Input('raw_data_table', 'columns'),
        prevent_initial_call = True
    )
    def update_asis_lane_setting_dropdown(columns):
        if columns == None or isinstance(columns, list) == False:
            raise PreventUpdate
        options = []

        for column in columns:
            if not column['id'] == mw_column_name:
                options.append({'value': column['id'], 'label': column['name']})
        dropdown = {
            'sample_name': {
                'options': options,
                'clearable': False,
            }
        }       
        return dropdown

    @_app.callback(
        Output('download_image', 'data'),
        Input('download_button', 'n_clicks'),
        State('resulted_image', 'src'),
        State('store_fileinfo', 'data'),
        prevent_initial_call = True
    )
    def update_download(n_clicks, image_src, fileinfo):
        if n_clicks and image_src:
            from pathlib import Path
            filename_stem = Path(fileinfo['filename']).stem
            return dict(content=image_src.split(",")[1], filename="image_{}.png".format(filename_stem), base64=True)
        return dash.no_update

    @_app.callback(
        Output('download_log', 'data'),
        Input('download_log_button', 'n_clicks'),
        State("generate_log", "value"),
        State('store_fileinfo', 'data'),
        prevent_initial_call = True
    )
    def download_log(n_clicks, text_value, fileinfo):
        if n_clicks and text_value:
            from pathlib import Path
            filename_stem = Path(fileinfo['filename']).stem
            return dcc.send_string(text_value, filename = "log_{}.txt".format(filename_stem))

    @_app.callback(
        Output('download_all', 'data'),
        Input('download_all_button', 'n_clicks'),
        State('resulted_image', 'src'),
        State('generate_log', 'value'),
        State('store_fileinfo', 'data'),
        prevent_initial_call = True
    )
    def download_all_in_zip(n_clicks, base64_image_src, log_text, fileinfo):
        import zipfile
        zip_buffer = io.BytesIO()

        from pathlib import Path
        filename_stem = Path(fileinfo['filename']).stem

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            if base64_image_src:
                if ',' in base64_image_src:
                    base64_data = base64_image_src.split(',')[1]
                else:
                    base64_data = base64_image_src
                image_bytes = base64.b64decode(base64_data)
                zf.writestr('image_{}.png'.format(filename_stem), image_bytes)
            zf.writestr('log_{}.txt'.format(filename_stem), log_text or '')
        zip_buffer.seek(0)
        return dcc.send_bytes(zip_buffer.getvalue(), '{}.zip'.format(filename_stem))
        

    @_app.callback(
        Output('graph', 'figure'),
        Input('raw_data_table', 'data'),
        Input('raw_data_table', 'columns'),
        prevent_initial_call = True
    )
    def update_graph(raw_data, raw_data_columns):
        if isinstance(raw_data_columns, list) != True:
            raise PreventUpdate
        if raw_data == None or len(raw_data) == 0:
            raise PreventUpdate
        column_names = [ x['name'] for x in raw_data_columns ]
        if mw_column_name in column_names == False:
            raise PreventUpdate
        
        df = pd.DataFrame.from_records(raw_data, columns = column_names)
        x_uniform = np.linspace(0, 1, len(raw_data))
        fig = go.Figure()
        for column in column_names:
            if column == mw_column_name:
                continue
            fig.add_trace(go.Scatter(
                x = x_uniform, y = df[column], name = column, showlegend=True, 
                text=df[mw_column_name],
                hovertemplate= column + '<br>x: %{text}<br>y: %{y}<extra></extra>' )
            )
        fig.update_layout(
            xaxis=dict(
                tickvals = x_uniform[::10],
                ticktext = df[mw_column_name][::10],
            )
        )
        return fig
            
    @_app.callback(
        Output('graph_normalized', 'figure'),
        Input('normalized_data_table', 'data'),
        Input('normalized_data_table', 'columns'),
        prevent_initial_call = True
    )
    def update_calculated_graph(calculated_data, calculated_data_columns):
        if isinstance(calculated_data_columns, list) != True:
            raise PreventUpdate
        if calculated_data == None or len(calculated_data) == 0:
            raise PreventUpdate
        column_names = [ x['name'] for x in calculated_data_columns ]
        if mw_column_name in column_names == False:
            raise PreventUpdate
        
        df = pd.DataFrame.from_records(calculated_data, columns = column_names)
        x_uniform = np.linspace(0, 1, len(calculated_data))
        fig = go.Figure()
        for column in column_names:
            if column == mw_column_name:
                continue
            fig.add_trace(go.Scatter(
                x = x_uniform, y = df[column], name = column, showlegend=True, 
                text=df[mw_column_name],
                hovertemplate= column + '<br>x: %{text}<br>y: %{y}<extra></extra>' )
            )
        fig.update_layout(
            xaxis=dict(
                tickvals = x_uniform[::10],
                ticktext = df[mw_column_name][::10],
            )
        )
        return fig

    #================================================================================
    #   Switch the Enable/Disable Interfaces
    #================================================================================
    #------------------------------------------------------------
    #   Draw Range
    #------------------------------------------------------------
    _app.clientside_callback(
        ClientsideFunction(namespace="common", function_name="negate"),
        Output('draw_mw_range_min', 'disabled'),
        Input('draw_mw_range_switch', 'value'),
    )
    _app.clientside_callback(
        ClientsideFunction(namespace="common", function_name="negate"),
        Output('draw_mw_range_max', 'disabled'),
        Input('draw_mw_range_switch', 'value'),
    )

    #------------------------------------------------------------
    #   Download Button
    #------------------------------------------------------------
    _app.clientside_callback(
        ClientsideFunction(namespace = "ui_disable", function_name="download_button_disable"),
        Output('download_button', 'disabled'),
        Input('resulted_image', 'src')
    )
    _app.clientside_callback(
        ClientsideFunction(namespace = "ui_disable", function_name="download_button_disable"),
        Output('download_log_button', 'disabled'),
        Input('resulted_image', 'src')
    )
    _app.clientside_callback(
        ClientsideFunction(namespace = "ui_disable", function_name="download_button_disable"),
        Output('download_all_button', 'disabled'),
        Input('resulted_image', 'src')
    )

    #------------------------------------------------------------
    #   Collapse of Settings
    #------------------------------------------------------------
    @_app.callback(
        Output("asis_collapse", "is_open"),
        Input("draw_type_radio", "value"),
    )
    def update_asis_collapse(draw_type):
        if draw_type == "as_is":
            return True
        elif draw_type == "normalized_new":
            return True
        else:
            return False

    #------------------------------------------------------------
    #   Add Lane Button
    #------------------------------------------------------------
    lane_order_handle_buttons =  ['add_lane_button', 'lane_reset_button', 'lane_clear_button', 'lane_insert_button']
    for button_id in lane_order_handle_buttons:
        _app.clientside_callback(
            ClientsideFunction(namespace="common", function_name="false_if_value_is_not_empty_list"),
            Output(button_id, "disabled"),
            Input('raw_data_table', 'data'),
        )

    #------------------------------------------------------------
    #   Generate Button
    #------------------------------------------------------------
    _app.clientside_callback(
        ClientsideFunction(namespace="ui_disable", function_name="generate_button_disable"),
        Output("generate_button", "disabled"),
        Input("draw_type_radio", "value"),
        Input("raw_data_table", "data"),
        Input("normalized_data_table", "data"),
        Input("draw_mw_range_switch", "value"),
        Input("draw_mw_range_min", "value"),
        Input("draw_mw_range_max", "value"),
    )

    #------------------------------------------------------------
    #   Marker Input
    #------------------------------------------------------------
    _app.clientside_callback(
        ClientsideFunction(namespace="ui_disable", function_name="marker_mw_input_disable"),
        Output('marker_mw_input', 'disabled'),
        Input('marker_switch', 'value'),
    )

    @_app.callback(
        Output('marker_mw_input', 'invalid'),
        Input('marker_mw_input', 'value'),

        prevent_initial_call = True,
    )
    def update_marker_mw_input_valid(value):
        if value == None:
            return False
        elif len(value) == 0:
            return False
        else:
            try:
                ret = utilfuncs.parse_labeled_numbers(value)
                return False
            except ValueError as e:
                return True

    #------------------------------------------------------------
    #   Marker Input
    #------------------------------------------------------------
    def disable_detailed_setting_inputs(detailed_setting_switch, input_keys, restore_button_id):
        @_app.callback(
            (
                [ Output({"type": "detailed_settings", "key": x}, "disabled") for x in input_keys] 
                + [Output(restore_button_id, "disabled")]
            ),
            Input({"type": "detailed_settings", "key": detailed_setting_switch}, "value"),
        )
        def update_disable(value):
            ret_val = True
            if value == True:
                ret_val = False
            else:
                ret_val = True
            ret = [ret_val for x in input_keys] + [ret_val]
            return ret
    disable_detailed_setting_inputs("label_font_size_switch", ["lane_label_size", "mw_label_size"], "label_size_default_button")
    disable_detailed_setting_inputs("band_width_switch", ["band_width", "band_spacing"], "band_width_default_button")
    disable_detailed_setting_inputs("offset_switch", ["offset_top", "offset_bottom", "offset_left", "offset_right"], "offset_default_button")

    def restore_detailed_setting_default_values(button_id, input_keys):
        @_app.callback(
            [ Output({"type": "detailed_settings", "key": x}, "value") for x in input_keys],
            Input(button_id, "n_clicks"), prevent_initial_call = True,
        )
        def restore_default_value(n_clicks):
            return [default_values[x] for x in input_keys]

    restore_detailed_setting_default_values(
        button_id = "offset_default_button", 
        input_keys = ["offset_top", "offset_bottom", "offset_left", "offset_right"], 
    )
    restore_detailed_setting_default_values(
        button_id = "band_width_default_button", 
        input_keys = ["band_width", "band_spacing"], 
    )
    restore_detailed_setting_default_values(
        button_id = "label_size_default_button", 
        input_keys = ["lane_label_size", "mw_label_size"], 
    )

