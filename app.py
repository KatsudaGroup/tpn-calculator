import dash
import dash_bootstrap_components as dbc

from layout import app_layout
from callback import callbacks
from callback_normalization import callback_normalization

############################################################
#  Default Value Set up
############################################################
default_values = {
    "offset_top":   40,
    "offset_bottom":    40,
    "offset_left":  40,
    "offset_right": 40,
    "band_width": 20,
    "band_spacing": 10,
    "lane_label_size": 16,
    "mw_label_size": 16
}

############################################################
# Set up
############################################################
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP], title = "TPN Calculator")
app.layout = app_layout(default_value=default_values)
callbacks(app, default_values)
callback_normalization(app, default_values)

############################################################
# Run on server
############################################################
server=app.server
if __name__ == '__main__':
    # For debug Run.
    app.run(debug=True)
