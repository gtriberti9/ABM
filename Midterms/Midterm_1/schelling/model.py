# model.py
from mesa import Model
from mesa.space import SingleGrid
from mesa.datacollection import DataCollector
from agents import SchellingAgent

class SchellingModel(Model):
    def __init__(self, width=50, height=50, density=0.7, radius=1, seed=None):
        super().__init__(seed=seed)
        self.width = width
        self.height = height
        self.density = density
        self.radius = radius

        self.grid = SingleGrid(width, height, torus=True)
        self.happy = 0

        self.datacollector = DataCollector(
            model_reporters={
                "happy": "happy",
                "share_happy": lambda m: (m.happy / len(m.agents)) * 100 if len(m.agents) > 0 else 0
            }
        )

        for _, pos in self.grid.coord_iter():
            if self.random.random() < self.density:
                self.grid.place_agent(SchellingAgent(self), pos)

        self.datacollector.collect(self)

    def step(self):
        self.happy = 0
        self.agents.shuffle_do("move")
        self.datacollector.collect(self)
        self.running = self.happy < len(self.agents)

