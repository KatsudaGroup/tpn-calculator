
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    ui_disable: {
        /* Main Panels */
        download_button_disable: function(image_src) {
            if (image_src != null) {
                return false;   // not disable
            } else {
                return true;    // disable
            }
        },

        marker_mw_input_disable: function(switch_value) {
            if (Array.isArray(switch_value) && 0 < switch_value.length) {
                return false;   // not disable
            } else {
                return true;    // disable
            }
        },

        generate_button_disable: function(
            draw_type, raw_data_table, normalized_data_table,
            draw_mw_range_switch, draw_mw_range_min, draw_mw_range_max) 
        {
            // Data Empty Check
            if (draw_type === "as_is") {
                if (!Array.isArray(raw_data_table) || raw_data_table.length === 0) {
                    return true;    // disable
                }
            } else if (draw_type === "normalized_new") {
                if (!Array.isArray(normalized_data_table) || normalized_data_table.length === 0) {
                    return true;    // disable
                }
            }
            // Molecular Range
            if (draw_mw_range_switch === true) {
                if (draw_mw_range_min != null && draw_mw_range_max != null &&
                    Number.isNaN(draw_mw_range_min) === false && Number.isNaN(draw_mw_range_max) === false) {
                    if (draw_mw_range_max < draw_mw_range_min) {
                        return true;    // disable
                    }
                }
            }
            return false;   // ok!
        }
    },

    normalization_ui_disable: {
        calculate_normalized_signal_button_disable: function(
            normlization_target_dropdown, 
            signal_calculation_range_switch, 
            min_mw, max_mw) 
        {
            if (normlization_target_dropdown == null) {
                return true;    // disable
            }
            if (signal_calculation_range_switch === true) {
                if (min_mw == null || max_mw == null) {
                    return true;    // disable
                }
                if (Number.isNaN(min_mw) || Number.isNaN(max_mw)) {
                    return true;    // disable;
                }
                if (max_mw < min_mw) {
                    return true;    // disable
                }
            }
            return false;   // ok!
        },

        set_normalization_target_dropdown_none: function(data) {
            return null;
        }
    },
    common: {
        negate: function(switch_value) {
            if (switch_value == null)  {return true;}
            if (switch_value === true) {
                return false;
            } else {
                return true;
            }
        },
        false_if_value_is_not_empty_list: function(value) {
            if (!Array.isArray(value)) {
                return true;
            }
            if (value.length === 0) {
                return true;
            } 
            return false;
        }
    }
});
