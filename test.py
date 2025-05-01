import time

def timer(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()           # начало отсчёта
        result = func(*args, **kwargs)        # вызов функции
        end = time.perf_counter()             # конец отсчёта
        print(f"[TIMER] {func.__name__} выполнена за {end - start:.6f} сек")
        return result
    return wrapper


@timer
def waste_time(n):
    s = 0
    for i in range(n):
        s += i*i
    return s

print(waste_time(10_000_000))