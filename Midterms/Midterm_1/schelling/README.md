*Code adapted from Mesa Examples project*

# Schelling Segregation Model

## Summary

The Schelling segregation model is a classic agent-based model, demonstrating how even a mild preference for similar neighbors can lead to a much higher degree of segregation than we would intuitively expect. The model consists of agents on a square grid, where each grid cell can contain at most one agent.

This project adapts the original Schelling model to examine income-based residential segregation. Agents are assigned income levels drawn from a long right-tailed distribution to approximate the actual U.S. income distribution. These agents are represented by a scale where yellow represents higher income agents and blue represents lower income. As in the original model, agents assess their satisfaction based on their neighborhood composition. Each agent has a satisfaction threshold, drawn from a uniform distribution between 0 and 1, representing the minimum required share of “similar” neighbors—defined as those whose incomes differ by no more than 10\%. This similarity ratio is informed by data on median income and its variation across Chicago neighborhoods. Agents incur a cost of one unit when moving and will only relocate if the utility gained from a higher share of similar neighbors exceeds this cost. However, agents do not have full visibility of all vacant locations; they consider only about ten randomly selected options. Additionally, agents who have previously moved become less tolerant of relocating again—their satisfaction threshold decreases, making them more likely to remain despite income dissimilarity.

## Before running the model

If you have already run other solara models before, skip this step.

If not, before running the model, please recreate the environment needed for running it.

```
conda env create -f environment.yml
```

## How to Run

To run the model interactively, run the following code in this directory:

```
    $ solara run app.py
```

## Files

* ``agents.py``: Contains the agent class.
* ``model.py``: Contains the model class.
* ``app.py``: Defines classes for visualizing the model in the browser via Solara, and instantiates a visualization server.


