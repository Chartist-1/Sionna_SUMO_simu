import pandas as pd
import matplotlib.pyplot as plt
import ast
import os

def path_loss_graphs(scenario, filename):
    try:
        # Загрузка данных
        filepath = os.path.join('scenarios', scenario, 'output_data', filename)
        df = pd.read_csv(filepath, sep=' ')

        # Функция для получения списка машин
        def get_unique_vehicles(cars_data_str):
            try:
                cars_list = ast.literal_eval(cars_data_str)
                return [car['vehId'] for car in cars_list]
            except (ValueError, SyntaxError) as e:
                print(f"Ошибка при разборе данных автомобилей: {e}")
                return []
        
        # Функция для преобразования строки потерь
        def parse_path_loss(path_loss_str):
            try:
                return ast.literal_eval(path_loss_str)
            except (ValueError, SyntaxError) as e:
                print(f"Ошибка при разборе данных потерь: {e}")
                return {}

        # Получаем список всех уникальных машин
        all_vehicles = set()
        for cars_str in df['Cars_Data']:
            vehicles_in_frame = get_unique_vehicles(cars_str)
            all_vehicles.update(vehicles_in_frame)
        
        if not all_vehicles:
            print("Не найдены данные по транспортным средствам")
            return

        # Создаем папку для графиков
        output_dir = os.path.join('scenarios', scenario, 'vehicle_plots')
        os.makedirs(output_dir, exist_ok=True)

        # Создаем отдельный график для каждой машины
        for current_veh in sorted(all_vehicles):
            plt.figure(figsize=(12, 6))
            
            # Собираем данные по взаимодействиям
            interaction_data = {}
            for frame, path_loss_str in zip(df['Frame'], df['PathLoss']):
                path_loss_dict = parse_path_loss(path_loss_str)
                for other_veh, loss in path_loss_dict.get(current_veh, {}).items():
                    if other_veh != current_veh:  # Исключаем связь с самим собой
                        if other_veh not in interaction_data:
                            interaction_data[other_veh] = {'frames': [], 'losses': []}
                        interaction_data[other_veh]['frames'].append(frame)
                        interaction_data[other_veh]['losses'].append(loss)
            
            # Если нет данных о взаимодействиях, пропускаем
            if not interaction_data:
                plt.close()
                continue
            
            # Рисуем графики
            for other_veh, data in interaction_data.items():
                plt.plot(data['frames'], data['losses'],
                        linestyle='-',
                        linewidth=2,
                        label=f"{other_veh}",
                        alpha=0.8)
            
            # Настройки графика
            plt.title(f'Потери сигнала для {current_veh}\nСценарий: {scenario}')
            plt.xlabel('Фрейм', fontsize=12)
            plt.ylabel('Потери сигнала (dBm)', fontsize=12)
            plt.grid(True, linestyle='--', alpha=0.5)
            
            # Улучшенная легенда
            plt.legend(title="Взаимодействие с:", 
                     bbox_to_anchor=(1.05, 1), 
                     loc='upper left',
                     borderaxespad=0.)
            
            # # Настройка осей
            # plt.xlim(left=min(df['Frame']), right=max(df['Frame']))
            
            # Сохраняем график
            output_filename = f"{os.path.splitext(filename)[0]}_{current_veh}_interactions.png"
            plt.savefig(os.path.join(output_dir, output_filename), 
                      dpi=300, 
                      bbox_inches='tight',
                      facecolor='white',
                      transparent=False)
            plt.close()

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")

# Пример вызова функции
path_loss_graphs("scenario_tunnel", "output1-500.csv")