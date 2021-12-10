from multiprocessing import Pool
import time
def f(x):
    return x*x

if __name__ == '__main__':
    results = ''
    start = time.time()
    with Pool(5) as p:
        results = p.map(f, [1, 2, 3])
    end = time.time()
    print(results)
    print(f"total time : {end-start}")

    results = []
    start = time.time()
    for i in range(1,4):
        results.append(f(i))
    
    end = time.time()
    print(results)
    print(f"total time : {end-start}")
