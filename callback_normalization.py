import dash
from dash.dependencies import Output, Input, State
from dash.exceptions import PreventUpdate
from dash import html,ALL,ctx,ClientsideFunction
import pandas as pd
import utilfuncs

mw_column_name = 'kDa'
def callback_normalization(_app: dash.Dash, default_values):
    #================================================================================
    #   Normalization Panel
    #================================================================================
    @_app.callback(
        Output("lane_relationship_table", "data"),
        Output("expand_display_p", "children"),
        Input('raw_data_table', 'data'),
        Input('raw_data_table', 'columns'),
        Input('set_relationship_by_specifier_button', 'n_clicks'),
        Input('lane_relationship_table_reset_button', 'n_clicks'),

        State("lane_relationship_table", "data"),
        State("total_lane_specifier", "value"),
        State("target_lane_specifier", "value"),
    )
    def update_normalization_table(raw_data, raw_data_columns, 
                                   n_clicks_set_specifier, n_clicks_lane_relationship_table_reset,
                                   current_data, total_lane_specifier, target_lane_specifier):
        if isinstance(raw_data, list) == False or len(raw_data) == 0:
            raise PreventUpdate
        if dash.ctx.triggered_id == "raw_data_table" or dash.ctx.triggered_id == "lane_relationship_table_reset_button":
            ret = [{"index": i+1, "sample_name": column["name"], "type": "Target", "associated_lane": None} for (i, column) in enumerate(filter(lambda x: x["name"] != mw_column_name, raw_data_columns))]
            return ret, None

        if dash.ctx.triggered_id == 'set_relationship_by_specifier_button':
            error_style = {'color': 'red'}
            error_msg = lambda s: [html.Br(), html.Span("Error: {}".format(s), style = error_style)]

            ret_str = []
            expanded_total_indexes = utilfuncs.expand_range(total_lane_specifier)
            if expanded_total_indexes == None or len(expanded_total_indexes) == 0:
                ret_str.append(html.Span("Error: Total proteins: Invalid value!", style=error_style))
                return dash.no_update, ret_str
            ret_str.append("Selected Total Series: {}".format(expanded_total_indexes))
            if len(current_data) < max(expanded_total_indexes):
                ret_str.extend(error_msg("Total lane index: out of range!"))
                return dash.no_update, ret_str
            for i in expanded_total_indexes:
                current_data[i-1]["type"] = "Total"
                current_data[i-1]["associated_lane"] = None

            if isinstance(target_lane_specifier, str) and 0 < len(target_lane_specifier):
                expanded_target_indexes = utilfuncs.expand_range(target_lane_specifier)
                if expanded_target_indexes == None or len(expanded_target_indexes) == 0:
                    ret_str.extend(error_msg("Error: Target proteins: Invalid value!"))
                    return dash.no_update, ret_str
                ret_str.extend([html.Br(), "Selected Target Series: {}".format(expanded_target_indexes)])
                if expanded_target_indexes == None:
                    ret_str.extend(error_msg("Error: Target proteins: Invalid value!") )
                    return dash.no_update, ret_str
                if min(expanded_target_indexes) < 1 or len(current_data) < max(expanded_target_indexes):
                    ret_str.extend(error_msg("Target series index: out of range!"))
                    return dash.no_update, ret_str
                if len(expanded_total_indexes) != len(expanded_target_indexes):
                    ret_str.extend(error_msg("Number of selected total protein series and target protein series does not match!"))
                    return dash.no_update, ret_str
                if len(set(expanded_target_indexes) & set(expanded_total_indexes)) != 0:
                    duplicated = set(expanded_target_indexes) & set(expanded_total_indexes)
                    ret_str.extend(error_msg("{} is selected as both Total and Target series.".format(duplicated)) )
                for (i_total, i_target) in zip(expanded_total_indexes, expanded_target_indexes):
                    current_data[i_target-1]["type"] = "Target"
                    current_data[i_target-1]["associated_lane"] = current_data[i_total-1]["sample_name"]
            return current_data, ret_str
                
        else:
            # Never get here
            return dash.no_update, None


    @_app.callback(
        Output("lane_relationship_table", "dropdown_conditional"),
        Input("lane_relationship_table", "data"),
    )
    def update_relationship_table_dropdown(current_data):
        total_lane_records = filter(lambda x: x['type'] == 'Total', current_data)
        dropdown_conditional = [{
            'if': {'column_id': "associated_lane", 'filter_query': '{type} eq "Target"' },
            'options': [{'label': x['sample_name'], 'value': x['sample_name']} for x in total_lane_records ]
        }]
        return dropdown_conditional

    @_app.callback(
        Output("normalization_target_dropdown", "options"),
        Input("lane_relationship_table", "data")
    )
    def update_normalization_target_dropdown(lane_relationship_data):
            total_protein_list = [x for x in filter(lambda x: x["type"] == "Total", lane_relationship_data)]
            options = [{"label": x["sample_name"], "value": x["sample_name"]} for x in total_protein_list]
            return options

    @_app.callback(
        Output("normalization_target_dropdown", "value"),
        Input('raw_data_table', 'data'),
    )
    def update_normalization_target_dropdown(data):
        return None

    @_app.callback(
        Output("normalized_data_table", "data"),
        Output("normalized_data_table", "columns"),
        Output("normalization_result_table", "data"),
        Input("calculate_normalized_signal_button", "n_clicks"),
        Input('raw_data_table', 'data'),
        Input('raw_data_table', 'columns'),
        State("normalization_target_dropdown", "value"),
        State("lane_relationship_table", "data"),
        State("signal_calculation_range_switch", "value"),
        State("signal_calculation_range_min", "value"),
        State("signal_calculation_range_max", "value"),
        State("stop_summation_negative_value", "value"),
    )
    def calculate_normalization(n_clicks, raw_data, raw_data_columns, normalization_target, lane_relationship,
                                signal_calculation_range_switch, signal_range_min, signal_range_max, stop_summation_negative):
        if dash.ctx.triggered_id == "raw_data_table":
            # Clear
            raise PreventUpdate
        if raw_data == None or raw_data_columns == None:
            raise PreventUpdate
        if normalization_target == None:
            raise PreventUpdate

        column_names = [x['name'] for x in raw_data_columns]
        #----------------------------------------
        # If signal calculation range is set, extract the dataframe between the region
        #----------------------------------------
        if signal_calculation_range_switch == True:
            extracted_data = filter(lambda x: signal_range_min <= x[mw_column_name] <= signal_range_max, raw_data)
            dataframe = pd.DataFrame.from_records(extracted_data, columns = column_names)
        else:
            dataframe = pd.DataFrame.from_records(raw_data, columns = column_names)

        #----------------------------------------
        # First, calculate the signal sums
        #----------------------------------------
        signal_sums = {}
        if stop_summation_negative == True:
            signal_sums = utilfuncs.calc_signal_sum_positive_region(dataframe)
        else:
            signal_sums = utilfuncs.calc_signal_sum(dataframe)

        #----------------------------------------
        # Second, calculate the normalize factors
        #----------------------------------------
        total_protein_columns = [x["sample_name"] for x in filter(lambda x: x["type"] == "Total",lane_relationship)]
        ref_signal = signal_sums[normalization_target]
        factors = {x: ref_signal/signal_sums[x] if float(signal_sums[x]) != float(0) else 0 for x in total_protein_columns}

        used_factors = {}
        #----------------------------------------
        # Finally, calculate the resulted signal
        #----------------------------------------
        result_df = pd.DataFrame()
        result_df[mw_column_name] = dataframe[mw_column_name]
        for record in lane_relationship:
            sample_name = record["sample_name"]
            factor = 1.0;
            if record['type'] == "Total":
                factor = factors[sample_name]
            elif record['type'] == "Target":
                if "associated_lane" in record:
                    associated_lane = record["associated_lane"]
                    if associated_lane != None and associated_lane in factors:
                        factor = factors[associated_lane]
            scaled_signal = factor * dataframe.loc[:,sample_name]
            result_df[sample_name] = scaled_signal
            used_factors[sample_name] = factor
        
        # Pack for Data Table
        result_data = result_df.to_dict('records')
        result_columns = [{'name': i, 'id': i} for i in result_df.columns]
        #========================================
        # Normalization Summary
        #========================================
        is_reference = lambda x: True if (x["type"] == "Total" and x["sample_name"] == normalization_target) or (x["type"] == "Target" and x["associated_lane"] == normalization_target) else None
        msg_func = lambda x: "Reference" if is_reference(x) else ("Not Normalized" if float(used_factors[x["sample_name"]]) == float(1) else "Blank" if signal_sums[x["sample_name"]] == 0 else "")
        ret = [{"sample_name": x["sample_name"], 
                "raw_total_signal": signal_sums[x["sample_name"]],
                "factor": used_factors[x["sample_name"]],
                "note": msg_func(x) } for x in lane_relationship]

        return result_data, result_columns, ret


    _app.clientside_callback(
        ClientsideFunction(namespace="common", function_name="negate"),
        Output("signal_calculation_range_min", "disabled"),
        Input("signal_calculation_range_switch", "value"),
    )
    _app.clientside_callback(
        ClientsideFunction(namespace="common", function_name="negate"),
        Output("signal_calculation_range_max", "disabled"),
        Input("signal_calculation_range_switch", "value"),
    )

    _app.clientside_callback(
        ClientsideFunction(namespace = "normalization_ui_disable",
                           function_name="calculate_normalized_signal_button_disable"),
        Output("calculate_normalized_signal_button", "disabled"),
        Input("normalization_target_dropdown", "value"),
        Input("signal_calculation_range_switch", "value"),
        Input("signal_calculation_range_min", "value"),
        Input("signal_calculation_range_max", "value"),
    )
