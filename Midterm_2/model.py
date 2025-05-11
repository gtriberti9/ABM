"""
Inflation Target ABM Model with Banking Inclusion Effects
"""
import mesa
import numpy as np
from agents import Household, Firm, CentralBank


class InflationModel(mesa.Model):
    """
    Model class for simulating inflation targeting in developing economies
    with varying levels of banking inclusion.
    """
    def __init__(
        self,
        num_households=100,
        num_firms=20,
        banking_inclusion_rate=0.6,
        formal_sector_size=0.7,
        inflation_target=0.03,
        initial_inflation=0.08,  # Starting with an inflation shock
        inflation_shock_size=0.0
    ):
        super().__init__()
        self.num_households = num_households
        self.num_firms = num_firms
        self.banking_inclusion_rate = banking_inclusion_rate
        self.formal_sector_size = formal_sector_size
        
        # Model state variables
        self.current_inflation = initial_inflation
        self.price_index = 1.0
        self.previous_price_index = 1.0
        self.aggregate_demand = 0
        self.total_production = 0
        self.price_index_numerator = 0
        self.total_production_capacity = 0
        
        # Schedule for activating agents
        self.schedule = mesa.time.RandomActivation(self)
        
        # Data collection
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Inflation": lambda m: m.current_inflation,
                "Interest_Rate": lambda m: m.central_bank.interest_rate,
                "Aggregate_Demand": lambda m: m.aggregate_demand,
                "Total_Production": lambda m: m.total_production,
                "Inflation_Gap": lambda m: m.current_inflation - m.central_bank.inflation_target,
                "Formal_Inflation_Expectation": lambda m: m.get_formal_inflation_expectation(),
                "Informal_Inflation_Expectation": lambda m: m.get_informal_inflation_expectation()
            },
            agent_reporters={
                "Formal": lambda a: getattr(a, "formal", None),
                "Type": lambda a: type(a).__name__,
                "Expected_Inflation": lambda a: getattr(a, "expected_inflation", None),
                "Price_Level": lambda a: getattr(a, "price_level", None),
                "Savings": lambda a: getattr(a, "savings", None)
            }
        )
        
        # Create the Central Bank agent
        self.central_bank = CentralBank(0, self, inflation_target=inflation_target)
        self.schedule.add(self.central_bank)
        
        # Create household agents
        for i in range(1, num_households + 1):
            # Determine if household is formal (banked)
            is_formal = np.random.random() < banking_inclusion_rate
            
            # Create household with different parameters based on formality
            base_income = np.random.normal(50, 15)  # Base income distribution
            income_factor = 1.2 if is_formal else 0.8  # Formal households have higher income
            h = Household(
                i,
                self,
                formal=is_formal,
                savings=np.random.normal(100, 30) * income_factor,
                income=base_income * income_factor
            )
            self.schedule.add(h)
        
        # Create firm agents
        for i in range(num_households + 1, num_households + num_firms + 1):
            # Determine if firm is in formal sector
            is_formal = np.random.random() < formal_sector_size
            
            # Create firm with different parameters based on formality
            base_capacity = np.random.normal(100, 20)
            capacity_factor = 1.3 if is_formal else 0.7  # Formal firms have higher capacity
            capacity = base_capacity * capacity_factor
            
            f = Firm(i, self, formal=is_formal, production_capacity=capacity)
            self.schedule.add(f)
            self.total_production_capacity += capacity
        
        # Apply initial inflation shock if specified
        if inflation_shock_size > 0:
            self.current_inflation += inflation_shock_size
        
        # Collect initial data
        self.datacollector.collect(self)
    
    def step(self):
        """
        Model step function: advance the model by one step
        """
        # Reset aggregates for this step
        self.aggregate_demand = 0
        self.total_production = 0
        self.price_index_numerator = 0
        
        # Run all agent steps
        self.schedule.step()
        
        # Calculate new price index (weighted by production)
        self.previous_price_index = self.price_index
        if self.total_production > 0:  # Avoid division by zero
            self.price_index = self.price_index_numerator / self.total_production
        
        # Calculate inflation rate
        self.current_inflation = (self.price_index / self.previous_price_index) - 1
        
        # Collect data
        self.datacollector.collect(self)
    
    def get_average_inflation_expectation(self):
        """
        Calculate the average inflation expectation across all households
        """
        households = [agent for agent in self.schedule.agents if isinstance(agent, Household)]
        if not households:
            return self.current_inflation
        
        return sum(h.expected_inflation for h in households) / len(households)
    
    def get_formal_inflation_expectation(self):
        """
        Calculate average inflation expectation for formal (banked) households
        """
        formal_households = [
            agent for agent in self.schedule.agents 
            if isinstance(agent, Household) and agent.formal
        ]
        if not formal_households:
            return self.current_inflation
        
        return sum(h.expected_inflation for h in formal_households) / len(formal_households)
    
    def get_informal_inflation_expectation(self):
        """
        Calculate average inflation expectation for informal (unbanked) households
        """
        informal_households = [
            agent for agent in self.schedule.agents 
            if isinstance(agent, Household) and not agent.formal
        ]
        if not informal_households:
            return self.current_inflation
        
        return sum(h.expected_inflation for h in informal_households) / len(informal_households)