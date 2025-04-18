import solara
from model import SchellingModel
from mesa.visualization import (
    SolaraViz,
    make_space_component,
    make_plot_component,
)

import matplotlib
import matplotlib.cm as cm
import matplotlib.colors as mcolors

# Normalize income values from [1, 100] to [0, 1] for colormap
norm = mcolors.Normalize(vmin=1, vmax=100)
cmap = cm.get_cmap("coolwarm")  # Or "viridis", "plasma", etc.

## Define agent portrayal: color mapped to income
def agent_portrayal(agent):
    # Since agent.type (income class) is already normalized to [0, 1]
    norm = mcolors.Normalize(vmin=0, vmax=1)
    cmap = cm.get_cmap("viridis")  # A color map that works well for income gradation
    
    rgba = cmap(agent.type)  # Maps income directly to color
    hex_color = mcolors.to_hex(rgba)
    
    return {
        "color": hex_color,
        "marker": "s",
        "size": 40,
    }
## Define model parameters that can be adjusted in the Solara UI
model_params = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "width": {
        "type": "SliderInt",
        "value": 50,
        "label": "Width",
        "min": 5,
        "max": 100,
        "step": 1,
    },
    "height": {
        "type": "SliderInt",
        "value": 50,
        "label": "Height",
        "min": 5,
        "max": 100,
        "step": 1,
    },
    "density": {
        "type": "SliderFloat",
        "value": 0.7,
        "label": "Population Density",
        "min": 0,
        "max": 1,
        "step": 0.01,
    },
    "radius": {
        "type": "SliderInt",
        "value": 1,
        "label": "Vision Radius",
        "min": 1,
        "max": 5,
        "step": 1,
    },
}

# Create a model instance
schelling_model = SchellingModel()

# Create the visual components
HappyPlot = make_plot_component({"share_happy": "tab:green"})
SpaceGraph = make_space_component(agent_portrayal, draw_grid=False)

# Assemble the Solara app
page = SolaraViz(
    schelling_model,
    components=[SpaceGraph, HappyPlot],
    model_params=model_params,
    name="Schelling Segregation Model (Income-based)",
)

# Return the page
page
