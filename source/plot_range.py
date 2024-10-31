"""
Date: 241030
Author: danikam
Purpose: Plot approximate truck range as a function of fuel-tractor mass and volume ratios
"""

import pandas as pd
import matplotlib.pyplot as plt
from common_tools import get_top_dir

# Load data
top_dir = get_top_dir()
truck_data = pd.read_csv(f'{top_dir}/data/truck_info.csv')
fuel_data = pd.read_csv(f'{top_dir}/data/fuel_info.csv')

# Parameters
GALLONS_PER_M3 = 264.172    # Gallons per cubic meter

def get_mpgde(fuel, truck_fuel_info_df):
    """
    Gets the diesel equivalent miles per gallon (mpgde) for a given fuel from the dataframe with truck and fuel info
    
    Parameters
    ----------
    fuel : str
        Name of fuel to read in mpgde for
    
    truck_fuel_info_df : Pandas dataframe
        Pandas dataframe containing info for the class 8 truck with respect to different fuels

    Returns
    -------
    fuel_mpgde : float
        mpgde for the truck running on the given fuel
    """
    try:
        # Retrieve MPGDE for the given fuel
        fuel_mpgde = truck_fuel_info_df.loc[fuel, 'MPGDE']
        return float(fuel_mpgde)
    except KeyError:
        print(f"Fuel '{fuel}' not found in the truck fuel info dataframe.")
        return None

def calculate_miles_per_fuel(mpdge_fuel, energy_density_fuel, mass_density_fuel, energy_density_diesel, mass_density_diesel):
    """
    Calculates the average mile per mass of fuel.
    
    Parameters
    ----------
    mpdge_fuel : float
        The miles per diesel equivalent gallon for the fuel of interest
    
    energy_density_fuel : float
        The energy density of the fuel, in MJ / kg of fuel
        
    mass_density_fuel : float
        The mass density of the fuel, in kg / m^3
        
    energy_density_diesel : float
        The energy density of diesel, in MG / kg of diesel

    energy_density_diesel : float
        The mass density of diesel, in kg / m^3

    Returns
    -------
    miles_per_kg_fuel : float
        Average truck miles per kg of fuel
        
    miles_per_m3_fuel : float
        Average truck miles per cubic meter of fuel
    
    """
    
    miles_per_kg_diesel = mpdge_fuel / (mass_density_diesel / GALLONS_PER_M3)
    miles_per_kg_fuel = miles_per_kg_diesel * energy_density_fuel / energy_density_diesel
    miles_per_m3_fuel = miles_per_kg_fuel * mass_density_fuel
    
    return miles_per_kg_fuel, miles_per_m3_fuel
    
def create_range_vs_fuel_ratio_dfs(truck_info_df, truck_fuel_info_df, fuel_info_df):
    """
    Creates a dictionary of dataframes, one for each fuel type, with truck range and fuel ratios
    for ranges from 100 to 1000 miles in increments of 100, expressed as percentages of GVW and dry van volume.

    Parameters
    ----------
    truck_info_df : Pandas dataframe
        Dataframe containing truck information including max GVW and dry van volume.

    truck_fuel_info_df : Pandas dataframe
        Dataframe containing MPGDE values for each fuel type.

    fuel_info_df : Pandas dataframe
        Dataframe containing energy and mass density for each fuel type.

    Returns
    -------
    range_vs_fuel_ratio_dfs : dict
        Dictionary of dataframes with keys as fuel types and values as dataframes containing
        truck range data for ranges from 100 to 1000 miles.
    """

    # Initialize the dictionary to store DataFrames for each fuel
    range_vs_fuel_ratio_dfs = {}
    
    # Extract truck parameters from truck_info_df
    max_gvw = truck_info_df.loc["Max Gross Vehicle Weight (kg)", "Value"]
    dry_van_volume = truck_info_df.loc["Dry Van Volume (m^3)", "Value"]
    
    # Define range values (100 to 1000 miles in increments of 100)
    range_values = list(range(100, 1001, 100))
    
    for fuel in fuel_info_df.index:
        # Get MPGDE for the fuel
        mpgde_fuel = get_mpgde(fuel, truck_fuel_info_df)
        if mpgde_fuel is None:
            continue  # Skip if MPGDE is not available for the fuel

        # Retrieve energy and mass density for the fuel
        energy_density_fuel = fuel_info_df.loc[fuel, 'Energy Density (MJ / kg)']
        mass_density_fuel = fuel_info_df.loc[fuel, 'Mass Density (kg / m^3)']
        
        # Diesel reference values for energy and mass density
        energy_density_diesel = fuel_info_df.loc['Diesel', 'Energy Density (MJ / kg)']
        mass_density_diesel = fuel_info_df.loc['Diesel', 'Mass Density (kg / m^3)']
        
        # Calculate miles per kg and miles per m^3 of fuel
        miles_per_kg_fuel, miles_per_m3_fuel = calculate_miles_per_fuel(
            mpgde_fuel, energy_density_fuel, mass_density_fuel, energy_density_diesel, mass_density_diesel
        )
        
        # Initialize a list to collect data for the current fuel
        rows = []
        
        for truck_range in range_values:
            # Calculate required fuel mass and volume for the specified truck range
            fuel_mass = truck_range / miles_per_kg_fuel
            fuel_volume = truck_range / miles_per_m3_fuel
            
            # Calculate fuel mass and volume as percentages of GVW and Dry Van Volume
            fuel_mass_percentage = (fuel_mass / max_gvw) * 100
            fuel_volume_percentage = (fuel_volume / dry_van_volume) * 100
            
            # Append row to results for this fuel
            rows.append([truck_range, fuel_mass, fuel_mass_percentage, fuel_volume, fuel_volume_percentage])
        
        # Create a DataFrame for this fuel type
        fuel_df = pd.DataFrame(rows, columns=[
            'Truck Range (miles)', 'Fuel Mass (kg)', 'Fuel Mass (% of GVW)',
            'Fuel Volume (m^3)', 'Fuel Volume (% of Dry Van Volume)'
        ])
        
        # Add the DataFrame to the dictionary with the fuel type as the key
        range_vs_fuel_ratio_dfs[fuel] = fuel_df
    
    return range_vs_fuel_ratio_dfs
    


def plot_fuel_mass_volume_percentage_stacked(range_vs_fuel_ratio_dfs):
    """
    Plots Fuel Volume (% of Dry Van Volume) and Fuel Mass (% of GVW) on two vertically stacked plots,
    with each plot containing lines for all fuels.

    Parameters
    ----------
    range_vs_fuel_ratio_dfs : dict
        Dictionary of DataFrames with keys as fuel types and values as DataFrames containing
        truck range data for each fuel, including 'Truck Range (miles)', 'Fuel Mass (% of GVW)',
        and 'Fuel Volume (% of Dry Van Volume)' columns.
    """
    
    # Set up the figure and axes for stacked plots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)
    
    # Plot Fuel Volume (% of Dry Van Volume) for each fuel on the top subplot
    for fuel, df in range_vs_fuel_ratio_dfs.items():
        ax1.plot(df['Truck Range (miles)'], df['Fuel Volume (% of Dry Van Volume)'], label=fuel)
    ax1.set_ylabel('Fuel Volume (% of Dry Van Volume)')
    ax1.set_title('Fuel Volume as Percentage of Dry Van Volume')
    ax1.legend()
    
    # Plot Fuel Mass (% of GVW) for each fuel on the bottom subplot
    for fuel, df in range_vs_fuel_ratio_dfs.items():
        ax2.plot(df['Truck Range (miles)'], df['Fuel Mass (% of GVW)'], label=fuel)
    ax2.set_xlabel('Truck Range (miles)')
    ax2.set_ylabel('Fuel Mass (% of GVW)')
    ax2.set_title('Fuel Mass as Percentage of GVW')
    ax2.legend()

    # Adjust layout
    plt.tight_layout()
    plt.show()

    
def main():
    truck_info_df = pd.read_csv(f"{top_dir}/data/truck_info.csv", index_col=0)
    truck_fuel_info_df = pd.read_csv(f"{top_dir}/data/truck_fuel_info.csv", index_col=0)
    fuel_info_df = pd.read_csv(f"{top_dir}/data/fuel_info.csv", index_col=0)
    
    range_vs_fuel_ratio_dfs = create_range_vs_fuel_ratio_dfs(truck_info_df, truck_fuel_info_df, fuel_info_df)

    # Plot the data
    plot_fuel_mass_volume_percentage_stacked(range_vs_fuel_ratio_dfs)
    
main()
