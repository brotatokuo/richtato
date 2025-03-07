from abc import ABC, abstractmethod


class DB(ABC):
    def __init__(self, user):
        self.user = user

    @abstractmethod
    def add(self, user, **kwargs):
        pass

    @abstractmethod
    def delete(self, **kwargs):
        pass

    @abstractmethod
    def update(self, **kwargs):
        pass
