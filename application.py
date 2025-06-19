import multiprocessing
import os

def run_webapp(script_name):
    os.system(f"python3 ./src/{script_name}")

def run_controller(script_name):
    os.system(f"ryu-manager ./src/{script_name}")

if __name__ == "__main__":
    p1 = multiprocessing.Process(target=run_controller, args=("controller.py",))
    p2 = multiprocessing.Process(target=run_webapp, args=("webapp.py",))

    p1.start()
    p2.start()

    p1.join()
    p2.join()


