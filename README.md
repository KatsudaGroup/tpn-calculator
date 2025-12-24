# TPN Calculator

[![DOI](https://zenodo.org/badge/1121737054.svg)](https://doi.org/10.5281/zenodo.18048351)

A web-based tool for total protein normalization and virtual lane visualization of Simple Western (capillary-based Western blot) data.

- Documentation: https://katsudagroup.github.io/tpn-calculator-docs
- Web application: https://tpn-calculator.katsudagroup-biotool.com

## 1. Preparation

### 1.1 Make the Separated Environment
This is optional. 
However, using a separate environment is strongly recommended.

```sh
python -m venv env
source env/bin/activate
```

### 1.2 Install Dependencies

```sh
pip install -r requirements.txt
```

## 2. Run 

You can draw the image by using the class or web-tool.

### Use as a Python script

Python class for plot is available.
An example code snippet is shown below.

```python
from band_plot_utils import *
import pandas as pd

if __name__ == '__main__':
    filename = "example/example.txt"
    raw_data = pd.read_excel(filename)

    plot_obj = WesternBlotPlotUtil(raw_data, plot_sample_indices = [1,2,3,4,5,6,7,8], mw_column_index = 0, offset = 30, marker_molecular_weights = [230, 180, 116, 66, 40, 12])
    plot_obj.draw_bands(signal_max = 10000)
    plot_obj.save_png('image.png')
```

### Use Web Tool (in debug mode)

Run the server as follows.

```sh
python app.py
```

The program will be available at http://localhost:8050


### Use Web Tool (deploying)

```sh
gunicorn -b 0.0.0.0:8000 app:server
```
Program will be available at http://localhost:8000


## About Source Code

Note: For historical reasons, variable names still use "lane"
internally, although the user interface refers to them as "series".

<!-- For reproducibility, the current version of the source code is archived at:
[Zenodo DOI: 10.xxxx/zenodo.xxxxxx](https://doi.org/10.xxxx/zenodo.xxxxxx) -->
