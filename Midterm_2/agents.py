"""
Agents for Inflation Target ABM with Banking Inclusion Effects
"""
import mesa
import numpy as np


class Household(mesa.Agent):
    """
    A household agent represents consumers in the economy.
    
    Each household has consumption patterns and can be either 
    formal (banked) or informal (unbanked).
    """
    def __init__(self, unique_id, model, formal=True, savings=100, income=50):
        super().__init__(unique_id, model)
        # Determines if the household has access to banking services
        self.formal = formal
        self.savings = savings
        self.income = income
        # Consumption patterns and price expectations
        self.consumption_rate = 0.8  # % of income spent
        self.expected_inflation = model.current_inflation
        # Sensitivity to interest rate changes (higher for formal households)
        self.interest_rate_sensitivity = 0.5 if formal else 0.1
    
    def step(self):
        """
        Household agent behavior during each step:
        1. Receive income
        2. Update inflation expectations
        3. Decide consumption based on income, savings, and interest rates
        """
        # Update inflation expectations (formal households track central bank target more closely)
        target_gap = self.model.central_bank.inflation_target - self.expected_inflation
        adjustment_speed = 0.5 if self.formal else 0.2  # Formal households adjust faster
        self.expected_inflation += adjustment_speed * target_gap
        
        # Calculate consumption based on income and interest rate effects
        base_consumption = self.income * self.consumption_rate
        
        # Interest rate effect (higher rates reduce consumption)
        interest_effect = -self.interest_rate_sensitivity * self.model.central_bank.interest_rate
        
        # Adjust consumption (formal households are more affected by interest rate)
        adjusted_consumption = base_consumption * (1 + interest_effect)
        adjusted_consumption = max(adjusted_consumption, 0.2 * self.income)  # Minimum subsistence consumption
        
        # Save the rest
        self.savings += self.income - adjusted_consumption
        
        # Contribute to aggregate demand
        self.model.aggregate_demand += adjusted_consumption


class Firm(mesa.Agent):
    """
    A firm agent represents businesses that produce goods and services.
    
    Each firm sets prices based on costs and market conditions.
    """
    def __init__(self, unique_id, model, formal=True, production_capacity=100):
        super().__init__(unique_id, model)
        self.formal = formal  # Determines if the firm is formal or informal
        self.production_capacity = production_capacity
        self.current_production = production_capacity * 0.8  # Starting at 80% capacity
        self.price_level = 1.0
        self.markup = 0.15  # Basic profit margin
        # Formal firms are more responsive to central bank signals
        self.central_bank_influence = 0.8 if formal else 0.3
    
    def step(self):
        """
        Firm agent behavior during each step:
        1. Observe market conditions
        2. Decide production levels
        3. Set prices
        """
        # Adjust production based on aggregate demand
        demand_pressure = self.model.aggregate_demand / self.model.total_production_capacity - 1
        
        # Adjust capacity utilization (with bounds)
        capacity_change = 0.1 * demand_pressure
        new_utilization = (self.current_production / self.production_capacity) + capacity_change
        new_utilization = max(0.5, min(new_utilization, 1.0))  # Between 50% and 100%
        self.current_production = new_utilization * self.production_capacity
        
        # Contribute to total production
        self.model.total_production += self.current_production
        
        # Price setting mechanism
        # Cost push factors from demand pressure
        cost_push = max(0, demand_pressure) * 0.5
        
        # Expectations impact
        aggregate_expectations = self.model.get_average_inflation_expectation()
        expectation_effect = 0.3 * aggregate_expectations
        
        # Central bank credibility effect (formal firms pay more attention)
        cb_target = self.model.central_bank.inflation_target
        target_adjustment = self.central_bank_influence * (cb_target - self.model.current_inflation)
        
        # Calculate price adjustment
        price_adjustment = cost_push + expectation_effect + target_adjustment
        
        # Apply the adjustment bounded to reasonable changes
        bounded_adjustment = max(-0.05, min(price_adjustment, 0.1))
        self.price_level *= (1 + bounded_adjustment)
        
        # Contribute to price index
        self.model.price_index_numerator += self.price_level * self.current_production


class CentralBank(mesa.Agent):
    """
    The central bank agent sets monetary policy to target inflation.
    """
    def __init__(self, unique_id, model, inflation_target=0.03):
        super().__init__(unique_id, model)
        self.inflation_target = inflation_target
        self.interest_rate = 0.05  # 5% initial interest rate
        # Taylor rule parameters
        self.taylor_inflation_weight = 1.5
        self.taylor_output_weight = 0.5
        self.nominal_rate = 0.0642  # Long-term nominal interest rate
    
    def step(self):
        """
        Central bank behavior during each step:
        1. Observe inflation and output gap
        2. Adjust interest rates according to a Taylor-type rule
        """
        # Calculate inflation gap
        inflation_gap = self.model.current_inflation - self.inflation_target
        
        # Calculate output gap (simplified)
        output_gap = self.model.aggregate_demand / self.model.total_production - 1
        
        # Apply a Taylor-type rule for interest rate setting
        # r = r* + π + α(π - π*) + β(y - y*)
        target_rate = (self.nominal_rate + 
                      self.model.current_inflation + 
                      self.taylor_inflation_weight * inflation_gap + 
                      self.taylor_output_weight * output_gap)
        
        # Gradual adjustment of interest rates (central banks avoid large jumps)
        adjustment_speed = 0.5
        self.interest_rate += adjustment_speed * (target_rate - self.interest_rate)
        
        # Bound interest rate to reasonable values
        self.interest_rate = max(0.01, min(self.interest_rate, 0.20))  # Between 1% and 20%