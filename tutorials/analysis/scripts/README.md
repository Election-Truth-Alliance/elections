# Scripts

This directory contains Python scripts to do basic visualization.

Files include:
- [utils.py](utils.py) - Contains utility code to do things like:
  - Load excel files
  - Clean data
  - Generate dynamic sized dots for charts
  - Create calculated data values based on the file data such as turn out percent, share, etc.
  - Prompt users to select a race to generate charts
- [parameters.py](parameters.py) - Define parameters for all charts for all races including:
  - Contest name
  - File containing the data
  - Map of columns in file to standard names
  - Available Charts and chart specific data
  - Styling
  - Text
- Chart generation - This section will grow. Each script will scan the parameters.py file and determine which charts are available for each contest and prompt the user to select an available one.
  - [scatter_plot.py](scatter_plot.py) - generates scatter plot chart for candidate vote share by precinct vote total
  - [turnout_scatter_plot.py](turnout_scatter_plot.py) - generates scatter plot for candidate vote share by turnout percentage
  - [turnout_histogram.py](turnout_histogram.py) - generates overlapping turnout histograms with KDE curves and skew values for each candidate
  - [vote_share_histogram.py](vote_share_histogram.py) - generates histogram of precinct counts by candidate vote share percentage
  - [turnout_heatmap.py](turnout_heatmap.py) - generates 2D kernel density heatmap of candidate vote share by turnout (matches DensityHeatmapByTurnout dashboard component)
  - [turnout_bar_chart.py](turnout_bar_chart.py) - generates grouped bar chart of candidate votes sorted by turnout percentage

## Usage

```bash
pip install -r requirements.txt
python scatter_plot.py
```

Each script will prompt you to select from the available races configured in `parameters.py`. Output PNGs are saved to `../output/`.
