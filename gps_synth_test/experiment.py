from abc import ABC, abstractmethod
class User(ABC):
    def __init__(self, name):
        self.name = name

    def some_function(self, p:int):
        print(f"Do something in User class {p}")


class User_walk(User):
    def __init__(self, name, speed):
        super().__init__(name)
        self.speed = speed

    def some_function(self):
        super().some_function(self.name) 

    def return_nothing(self): 
        return "sdfsdopiouiytrertyu" # Calling the superclass's function


user_walk = User_walk("John", "sdfdsfds")
nothing = user_walk.return_nothing()
user_walk.some_function()

import time

def timer(func):
    def wrapper(*args, **kwargs):
        # start the timer
        start_time = time.time()
        # call the decorated function
        result = func(*args, **kwargs)
        # remeasure the time
        end_time = time.time()
        # compute the elapsed time and print it
        execution_time = end_time - start_time
        print(f"Execution time: {execution_time} seconds")
        # return the result of the decorated function execution
        return result
    # return reference to the wrapper function
    return wrapper

@timer
def train_model():
    print("Starting the model training function...")
    # simulate a function execution by pausing the program for 5 seconds
    time.sleep(5) 
    print("Model training completed!")

train_model()