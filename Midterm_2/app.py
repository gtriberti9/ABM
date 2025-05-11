"""
Visualization and Runner for Inflation Target ABM with Banking Inclusion Effects

This file provides both a traditional matplotlib-based visualization
and the option to launch an interactive Solara dashboard.
"""
import mesa
import numpy as np
import matplotlib.pyplot as plt
from model import InflationModel
import argparse
import sys
from mesa.time import RandomActivation


class InflationModelRunner:
    """
    Class to handle model setup, run simulations, and analyze results
    """
    def __init__(self):
        # Default parameter values
        self.params = {
            "num_households": 100,
            "num_firms": 20,
            "banking_inclusion_rate": 0.6,
            "formal_sector_size": 0.7,
            "inflation_target": 0.03,
            "initial_inflation": 0.08,
            "inflation_shock_size": 0.0
        }
        self.model = None
        self.results = None
        self.schedule = RandomActivation(self)
    
    def run_model(self, steps=100, **kwargs):
        """
        Create and run a model with given parameters
        """
        # Update parameters with any provided kwargs
        model_params = self.params.copy()
        model_params.update(kwargs)
        
        # Create new model with these parameters
        self.model = InflationModel(**model_params)
        
        # Run for specified number of steps
        for _ in range(steps):
            self.model.step()
        
        # Collect and return results
        self.results = self.model.datacollector.get_model_vars_dataframe()
        return self.results
    
    def plot_results(self, save_path=None):
        """
        Create plots of key model outputs
        """
        if self.results is None:
            print("No results to plot. Run the model first.")
            return
        
        # Create figure with subplots
        fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(14, 10))
        
        # Plot 1: Inflation rate and target
        ax1 = axes[0, 0]
        self.results["Inflation"].plot(ax=ax1, label="Current Inflation")
        ax1.axhline(
            y=self.model.central_bank.inflation_target, 
            color='r', 
            linestyle='--', 
            label="Inflation Target"
        )
        ax1.set_title("Inflation Rate Over Time")
        ax1.set_ylabel("Inflation Rate")
        ax1.legend()
        ax1.grid(True)
        
        # Plot 2: Interest Rate
        ax2 = axes[0, 1]
        self.results["Interest_Rate"].plot(ax=ax2)
        ax2.set_title("Central Bank Interest Rate")
        ax2.set_ylabel("Interest Rate")
        ax2.grid(True)
        
        # Plot 3: Inflation Expectations by Group
        ax3 = axes[1, 0]
        self.results["Formal_Inflation_Expectation"].plot(ax=ax3, label="Formal Sector")
        self.results["Informal_Inflation_Expectation"].plot(ax=ax3, label="Informal Sector")
        self.results["Inflation"].plot(ax=ax3, linestyle='--', label="Actual Inflation")
        ax3.axhline(
            y=self.model.central_bank.inflation_target, 
            color='r', 
            linestyle=':', 
            label="Target"
        )
        ax3.set_title("Inflation Expectations")
        ax3.set_ylabel("Expected Inflation")
        ax3.legend()
        ax3.grid(True)
        
        # Plot 4: Aggregate Demand and Production
        ax4 = axes[1, 1]
        self.results["Aggregate_Demand"].plot(ax=ax4, label="Aggregate Demand")
        self.results["Total_Production"].plot(ax=ax4, label="Total Production")
        ax4.set_title("Aggregate Demand and Production")
        ax4.legend()
        ax4.grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
        
        plt.show()
    
    def run_banking_inclusion_experiments(self, inclusion_rates=[0.3, 0.5, 0.7, 0.9], steps=100):
        """
        Run experiments with different banking inclusion rates and 
        compare the time to reach inflation target
        """
        results = {}
        
        for rate in inclusion_rates:
            # Run model with this inclusion rate
            model_results = self.run_model(
                steps=steps, 
                banking_inclusion_rate=rate,
                initial_inflation=0.08  # Starting with same inflation shock
            )
            
            # Calculate steps to reach target (within 0.5 percentage points)
            target = self.model.central_bank.inflation_target
            tolerance = 0.005  # Half percentage point
            
            # Find when inflation stabilizes near target
            stabilized_step = None
            for step in range(min(5, len(model_results)), len(model_results)):
                recent_gap = model_results["Inflation_Gap"].iloc[step-5:step]
                if all(abs(gap) < tolerance for gap in recent_gap):
                    stabilized_step = step - 5
                    break
            
            results[rate] = {
                "data": model_results,
                "steps_to_target": stabilized_step
            }
        
        return results
    
    def plot_comparative_results(self, experiment_results, save_path=None):
        """
        Plot comparative results from banking inclusion experiments
        """
        if not experiment_results:
            print("No experiment results to plot.")
            return
            
        # Create figure with subplots
        fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(12, 10))
        
        # Plot 1: Inflation paths for different inclusion rates
        ax1 = axes[0]
        for rate, result in experiment_results.items():
            result["data"]["Inflation"].plot(
                ax=ax1, 
                label=f"Banking Inclusion: {rate*100:.0f}%"
            )
        
        # Add inflation target line
        ax1.axhline(
            y=self.model.central_bank.inflation_target, 
            color='r', 
            linestyle='--', 
            label="Inflation Target"
        )
        ax1.set_title("Inflation Convergence by Banking Inclusion Rate")
        ax1.set_ylabel("Inflation Rate")
        ax1.legend()
        ax1.grid(True)
        
        # Plot 2: Bar chart of steps to reach target
        ax2 = axes[1]
        rates = []
        steps = []
        
        for rate, result in experiment_results.items():
            if result["steps_to_target"] is not None:
                rates.append(f"{rate*100:.0f}%")
                steps.append(result["steps_to_target"])
        
        ax2.bar(rates, steps)
        ax2.set_title("Time to Reach Inflation Target")
        ax2.set_xlabel("Banking Inclusion Rate")
        ax2.set_ylabel("Model Steps")
        ax2.grid(axis='y')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
        
        plt.show()


# Example usage of the runner
if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run Inflation Target ABM')
    parser.add_argument('--dashboard', action='store_true', 
                        help='Launch interactive Solara dashboard')
    args = parser.parse_args()
    
    # Check if we should launch the Solara dashboard
    if args.dashboard:
        try:
            import solara
            print("Launching Solara interactive dashboard...")
            # Import the dashboard module and run it
            import dashboard
            solara.run(dashboard.Page)
        except ImportError:
            print("Error: Solara not installed. Please install with 'pip install solara'")
            sys.exit(1)
    else:
        # Run traditional matplotlib visualization
        # Create a runner instance
        runner = InflationModelRunner()
        
        # Run a single simulation and plot results
        print("Running base model simulation...")
        runner.run_model(steps=100)
        runner.plot_results()
        
        # Run comparative experiments with different banking inclusion rates
        print("\nRunning banking inclusion experiments...")
        experiment_results = runner.run_banking_inclusion_experiments(
            inclusion_rates=[0.2, 0.4, 0.6, 0.8],
            steps=100
        )
        
        # Plot comparative results
        runner.plot_comparative_results(experiment_results)
        
        print("\nSimulation complete.")
        print("\nTip: Run with --dashboard flag for interactive visualization:")
        print("     python app.py --dashboard")
