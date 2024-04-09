import os

class MatrixConfig:

    def __init__(self):
        self.host = os.getenv("MATRIX_HOST")
        self.room = os.getenv("MATRIX_ROOM")
        self.access_token = os.getenv("MATRIX_ACCESS_TOKEN")

config = MatrixConfig()
