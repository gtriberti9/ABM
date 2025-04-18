from mesa import Agent
import random
import numpy as np

class SchellingAgent(Agent):
    ## Initiate agent instance, inherit model trait from parent class
    def __init__(self, model):
        super().__init__(model)

        # CHANGE 1
        # Set agent type using a skwewed distribution (US income distribution)
        # instead of binary type
        skw_income = np.random.lognormal(mean=0, sigma=0.8) 
        self.income_class = skw_income / (1 + skw_income) #Normalized 0 to 1
        
        self.type = self.income_class

        # CHANGE 2
        # Giving agents different thresholds
        # Assumption: the threshold has a uniform distribution
        self.threshold = random.uniform(0, 1)


        # CHANGE 3
        # Adaptation
        self.past_moves = 0
        self.adaptive = False

        # Movement cost (arbitrary)
        self.move_cost = 1

    
    def is_satisfied(self, neighbors):
        '''
        Fraction to check if agent is happy with their neighbors' share alike
        ratio. For the agent to be satisfied, the income class of their 
        neighbor should be around 10% far from their incom size. 

        The 10% threshold was looking at https://metop.io/insights/agqp map in 
        Chicago with average wage by neighborhood and its variation. 
        '''
        if not neighbors:
            return False
        
        # They are similar if they have a difference of -at most- 10%
        similar = sum(1 for n in neighbors 
                      if abs(n.type - self.type) <= 0.1)
        
        share_alike = similar / len(neighbors)

        # Each individual has their own threshold
        return share_alike >= self.threshold
    
    def evaluate_location(self, pos):
        # Check cost and similarity at a candidate position
        neighbors = self.model.grid.get_neighbors(pos, moore=True, radius=self.model.radius, include_center=False)
        if not neighbors:
            return -float('inf')

        similar = sum(1 for n in neighbors 
                      if abs(n.type - self.type) <= 0.1)
        share_alike = similar / len(neighbors)

        # Assumption: A function of effective costs such that poorer agents are 
        # more sensitive to cost. The 0.01 is to ensure we are not dividing by 0.
        effective_cost = self.move_cost * (1 / (self.type + 0.01)) 
        func = share_alike - effective_cost
        return func
    

    ## Define basic decision rule
    def move(self):
        # Current neighbors
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, radius=self.model.radius, include_center=False)

        # Satisfaction check
        if self.is_satisfied(neighbors):
            self.model.happy += 1
            return

        empty_cells = list(self.model.grid.empties)

        # CHANGE 4
        # The agent only evaluates some empty cells (Not all of them)
        candidates = random.sample(empty_cells, min(len(empty_cells), 10))  

        best_pos = None
        best_eval = -float('inf')

        for pos in candidates:
            eval = self.evaluate_location(pos)
            if eval > best_eval:
                best_eval = eval
                best_pos = pos

        # Move to best location
        if best_pos:
            self.model.grid.move_agent(self, best_pos)
            self.past_moves += 1

            # Adaptive tolerance: if the agent moved multiple times he will adapt
            # in future steps decreasing their threshold
            if self.adaptive and self.past_moves >= 10:
                self.threshold = min(1.0, self.threshold - 0.01)  # Become less picky if moving a lot    


