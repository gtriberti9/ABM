"""
Interactive Solara Dashboard for Inflation Target ABM with Banking Inclusion Effects
"""
import solara
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import altair as alt
from model import InflationModel

# Initialize model parameters with reactive variables
num_households = solara.reactive(100)
num_firms = solara.reactive(20)
banking_inclusion_rate = solara.reactive(0.6)
formal_sector_size = solara.reactive(0.7)
inflation_target = solara.reactive(0.03)
initial_inflation = solara.reactive(0.08)
inflation_shock_size = solara.reactive(0.0)
simulation_steps = solara.reactive(100)

# Reactive variables for storing results
model_results = solara.reactive(None)
current_model = solara.reactive(None)
simulation_complete = solara.reactive(False)
steps_to_target = solara.reactive(None)

# Reactive variables for experiments
run_experiment = solara.reactive(False)
experiment_results = solara.reactive({})
experiment_complete = solara.reactive(False)


@solara.component
def parameter_controls():
    """Component to display and control model parameters"""
    with solara.Card("Model Parameters", elevation=2):
        with solara.Column():
            solara.SliderInt("Number of Households", value=num_households, min=10, max=500, step=10)
            solara.SliderInt("Number of Firms", value=num_firms, min=5, max=100, step=5)
            solara.SliderFloat("Banking Inclusion Rate", value=banking_inclusion_rate, min=0.1, max=1.0, step=0.05, format="%.2f")
            solara.SliderFloat("Formal Sector Size", value=formal_sector_size, min=0.1, max=1.0, step=0.05, format="%.2f")
            solara.SliderFloat("Inflation Target", value=inflation_target, min=0.01, max=0.1, step=0.005, format="%.3f")
            solara.SliderFloat("Initial Inflation", value=initial_inflation, min=0.02, max=0.2, step=0.01, format="%.2f")
            solara.SliderFloat("Inflation Shock Size", value=inflation_shock_size, min=0.0, max=0.1, step=0.01, format="%.2f")
            solara.SliderInt("Simulation Steps", value=simulation_steps, min=20, max=300, step=10)


@solara.component
def run_controls():
    """Component with buttons to run simulation and experiments"""
    def run_single_simulation():
        simulation_complete.set(False)
        model = InflationModel(
            num_households=num_households.value,
            num_firms=num_firms.value,
            banking_inclusion_rate=banking_inclusion_rate.value,
            formal_sector_size=formal_sector_size.value,
            inflation_target=inflation_target.value,
            initial_inflation=initial_inflation.value,
            inflation_shock_size=inflation_shock_size.value
        )
        current_model.set(model)
        
        # Run the model for specified steps
        for _ in range(simulation_steps.value):
            model.step()
        
        # Collect results
        results = model.datacollector.get_model_vars_dataframe()
        model_results.set(results)
        
        # Calculate steps to target
        target = inflation_target.value
        tolerance = 0.005  # Half percentage point
        
        stabilized_step = None
        for step in range(min(5, len(results)), len(results)):
            # Check if inflation has been close to target for several steps
            recent_gap = abs(results["Inflation"].iloc[step-5:step] - target)
            if all(gap < tolerance for gap in recent_gap):
                stabilized_step = step - 5
                break
        
        steps_to_target.set(stabilized_step)
        simulation_complete.set(True)
    
    def run_experiment_simulations():
        experiment_complete.set(False)
        run_experiment.set(True)
        
        # Define different banking inclusion rates to test
        inclusion_rates = [0.2, 0.4, 0.6, 0.8]
        results = {}
        
        for rate in inclusion_rates:
            # Run model with this inclusion rate
            model = InflationModel(
                num_households=num_households.value,
                num_firms=num_firms.value,
                banking_inclusion_rate=rate,
                formal_sector_size=formal_sector_size.value,
                inflation_target=inflation_target.value,
                initial_inflation=initial_inflation.value,
                inflation_shock_size=inflation_shock_size.value
            )
            
            # Run for specified steps
            for _ in range(simulation_steps.value):
                model.step()
            
            # Collect results
            model_data = model.datacollector.get_model_vars_dataframe()
            
            # Calculate steps to target
            target = inflation_target.value
            tolerance = 0.005  # Half percentage point
            
            stabilized_step = None
            for step in range(min(5, len(model_data)), len(model_data)):
                # Check if inflation has been close to target for several steps
                recent_gap = abs(model_data["Inflation"].iloc[step-5:step] - target)
                if all(gap < tolerance for gap in recent_gap):
                    stabilized_step = step - 5
                    break
            
            results[rate] = {
                "data": model_data,
                "steps_to_target": stabilized_step
            }
        
        experiment_results.set(results)
        experiment_complete.set(True)
        run_experiment.set(False)
    
    with solara.Row():
        solara.Button(
            label="Run Simulation",
            on_click=run_single_simulation,
            color="primary",
            outlined=True,
            classes=["mr-4"]
        )
        solara.Button(
            label="Run Banking Inclusion Experiments",
            on_click=run_experiment_simulations,
            color="secondary",
            outlined=True
        )


@solara.component
def result_visualization():
    """Component to display simulation results"""
    if not simulation_complete.value:
        if model_results.value is None:
            return solara.Info("Run a simulation to see results")
        else:
            return solara.Loading("Running simulation...")
    
    results = model_results.value
    model = current_model.value
    
    with solara.Card("Simulation Results", elevation=2):
        with solara.Column():
            # Create matplotlib figure
            fig = plt.figure(figsize=(12, 8))
            
            # First subplot: Inflation and target
            ax1 = fig.add_subplot(221)
            results["Inflation"].plot(ax=ax1, label="Current Inflation")
            ax1.axhline(
                y=model.central_bank.inflation_target,
                color='r',
                linestyle='--',
                label="Inflation Target"
            )
            ax1.set_title("Inflation Rate Over Time")
            ax1.set_ylabel("Inflation Rate")
            ax1.legend()
            ax1.grid(True)
            
            # Second subplot: Interest rate
            ax2 = fig.add_subplot(222)
            results["Interest_Rate"].plot(ax=ax2)
            ax2.set_title("Central Bank Interest Rate")
            ax2.set_ylabel("Interest Rate")
            ax2.grid(True)
            
            # Third subplot: Inflation expectations
            ax3 = fig.add_subplot(223)
            results["Formal_Inflation_Expectation"].plot(ax=ax3, label="Formal Sector")
            results["Informal_Inflation_Expectation"].plot(ax=ax3, label="Informal Sector")
            results["Inflation"].plot(ax=ax3, linestyle='--', label="Actual Inflation")
            ax3.axhline(
                y=model.central_bank.inflation_target,
                color='r',
                linestyle=':',
                label="Target"
            )
            ax3.set_title("Inflation Expectations")
            ax3.set_ylabel("Expected Inflation")
            ax3.legend()
            ax3.grid(True)
            
            # Fourth subplot: Aggregate demand and production
            ax4 = fig.add_subplot(224)
            results["Aggregate_Demand"].plot(ax=ax4, label="Aggregate Demand")
            results["Total_Production"].plot(ax=ax4, label="Total Production")
            ax4.set_title("Aggregate Demand and Production")
            ax4.legend()
            ax4.grid(True)
            
            plt.tight_layout()
            
            # Display the figure in Solara
            solara.FigureMatplotlib(fig)
            
            # Display time to reach target
            if steps_to_target.value is not None:
                solara.Success(f"Inflation stabilized near target in {steps_to_target.value} steps")
            else:
                solara.Warning("Inflation did not stabilize near target within simulation period")


@solara.component
def experiment_visualization():
    """Component to display banking inclusion experiment results"""
    if not experiment_complete.value:
        if run_experiment.value:
            return solara.Loading("Running experiments...")
        else:
            return solara.Info("Run banking inclusion experiments to see comparative results")
    
    results = experiment_results.value
    
    with solara.Card("Banking Inclusion Experiment Results", elevation=2):
        with solara.Column():
            # Create matplotlib figure for experiment results
            fig = plt.figure(figsize=(12, 8))
            
            # First subplot: Inflation paths
            ax1 = fig.add_subplot(211)
            for rate, result in results.items():
                result["data"]["Inflation"].plot(
                    ax=ax1,
                    label=f"Banking Inclusion: {rate*100:.0f}%"
                )
            
            # Add inflation target line
            ax1.axhline(
                y=inflation_target.value,
                color='r',
                linestyle='--',
                label="Inflation Target"
            )
            ax1.set_title("Inflation Convergence by Banking Inclusion Rate")
            ax1.set_ylabel("Inflation Rate")
            ax1.legend()
            ax1.grid(True)
            
            # Second subplot: Bar chart of steps to target
            ax2 = fig.add_subplot(212)
            rates = []
            steps = []
            
            for rate, result in results.items():
                if result["steps_to_target"] is not None:
                    rates.append(f"{rate*100:.0f}%")
                    steps.append(result["steps_to_target"])
                else:
                    rates.append(f"{rate*100:.0f}%")
                    steps.append(simulation_steps.value)  # Use max steps if target not reached
            
            ax2.bar(rates, steps)
            ax2.set_title("Time to Reach Inflation Target")
            ax2.set_xlabel("Banking Inclusion Rate")
            ax2.set_ylabel("Model Steps")
            ax2.grid(axis='y')
            
            plt.tight_layout()
            
            # Display the figure in Solara
            solara.FigureMatplotlib(fig)
            
            # Display summary
            reached_targets = [r for r in results.values() if r["steps_to_target"] is not None]
            if reached_targets:
                min_steps = min(r["steps_to_target"] for r in reached_targets)
                max_steps = max(r["steps_to_target"] for r in reached_targets)
                solara.Info(f"Time to reach target ranged from {min_steps} to {max_steps} steps")
            else:
                solara.Warning("No scenarios reached inflation target within simulation period")


@solara.component
def dashboard():
    """Main dashboard component combining all elements"""
    solara.Title("Inflation Targeting ABM with Banking Inclusion Effects")
    
    with solara.Columns([1, 2]):
        with solara.Column():
            parameter_controls()
            solara.Markdown("""
            ### About This Model
            
            This Agent-Based Model (ABM) simulates how banking inclusion affects
            inflation targeting in developing economies. The model features:
            
            - Households that can be formal (banked) or informal (unbanked)
            - Firms operating in formal and informal sectors
            - A central bank using interest rates to target inflation
            
            Banking inclusion affects how quickly monetary policy transmits
            through the economy, as formal sector agents are more responsive
            to interest rate changes.
            """)
            run_controls()
        
        with solara.Column():
            with solara.TabContainer():
                with solara.Tab("Simulation Results"):
                    result_visualization()
                with solara.Tab("Banking Inclusion Experiments"):
                    experiment_visualization()


# Main application
@solara.component
def Page():
    """Main page component"""
    dashboard()


if __name__ == "__main__":
    solara.run(Page)