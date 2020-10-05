"""
Base handler class.
Currently has little functionality other than initialisation of the reader and writer
"""
from abc import ABC, abstractmethod
import asyncio

class BaseHandler(ABC):
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer

    @abstractmethod
    async def handle(self, body):
        pass
