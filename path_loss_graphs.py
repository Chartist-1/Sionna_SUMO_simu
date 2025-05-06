import pandas as pd
import matplotlib.pyplot as plt
import ast


def path_loss_graphs(scenario, filename):
    df = pd.read_csv(f'scenarios/{scenario}/output_data/{filename}', sep=' ')

    def get_unique_vehicles(cars_data_str):
        cars_list = ast.literal_eval(cars_data_str)
        return [car['vehId'] for car in cars_list]
    
    def get_total_loss(rssi_dict_str):
        rssi_dict = ast.literal_eval(rssi_dict_str)
        return {veh: sum(v for k, v in vals.items() if k != veh) 
                for veh, vals in rssi_dict.items()}
    
    all_vehicles = set()
    for cars_str in df['Cars_Data']:
        vehicles_in_frame = get_unique_vehicles(cars_str)
        all_vehicles.update(vehicles_in_frame)

    vehicles = sorted(list(all_vehicles))

    df['Total_Loss'] = df['PathLoss'].apply(get_total_loss)
    for veh in vehicles:
        df[f'Loss_{veh}'] = df['Total_Loss'].apply(lambda x: x.get(veh, 0))

    # Настройка графика
    plt.figure(figsize=(12, 6))

    # Построение линий для каждого vehicle
    for veh in vehicles:
        plt.plot(df['Frame'], df[f'Loss_{veh}'], label=veh, linewidth=2)

    # Настройка оформления
    plt.title('Суммарные потери сигнала для каждого транспортного средства', pad=20)
    plt.xlabel('Номер кадра', labelpad=10)
    plt.ylabel('Суммарные потери сигнала (dBm)', labelpad=10)
    plt.grid(True, alpha=0.3)
    plt.legend()

    # Сохранение в файл
    plt.savefig(f'scenarios/{scenario}/signal_loss_plot.png', 
            dpi=300, 
            bbox_inches='tight', 
            facecolor='white')

    # Закрытие фигуры (чтобы не занимала память)
    plt.close()

path_loss_graphs("scenario_serpantine", "output50-150.csv")