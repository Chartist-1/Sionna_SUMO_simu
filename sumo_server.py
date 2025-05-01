import traci
import time

# Configuration
PORT = 8813  # Must match the port used to start SUMO

def run_client():
    try:
        # Connect to the SUMO server
        traci.init(PORT)
        print(f"Connected to SUMO server on port {PORT}")

        x_max, y_max = traci.simulation.getNetBoundary()
        print(x_max, y_max)

        step = 0
        # while step < 1000:  # Run for 1000 simulation steps
        #     traci.simulationStep()  # Advance the simulation by one step

        #     # Example: Get all vehicle IDs
        #     vehicle_ids = traci.vehicle.getIDList()
        #     for veh_ID in vehicle_ids:
        #         print(traci.vehicle.getPosition3D(vehID=veh_ID))
        #     print(f"Step {step}: Vehicles in the simulation: {vehicle_ids}")
        #     step += 1
        #     time.sleep(1)  # Optional: Slow down the simulation for visualization

    except Exception as e:
        print(f"Error during simulation: {e}")
    finally:
        # Close the connection to SUMO
        traci.close()
        print("Disconnected from SUMO server.")

if __name__ == "__main__":
    run_client()