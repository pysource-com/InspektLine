
class MainWindow:
    def __init__(self):
        self.title = "Main Application Window"
        self.width = 800
        self.height = 600

    def show(self):
        print(f"Showing window: {self.title} with size {self.width}x{self.height}")