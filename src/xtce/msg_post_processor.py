from abc import ABC, abstractmethod


class MsgPostProcessor(ABC):

    @abstractmethod
    def process(self, msg: bytes) -> bytes:
        """
        Process the command. This usually means modifying the command,
        such as wrapping it inside a protocol such as RFC1055.
        :return: Processed command, which is a bytes object.
        """
        raise NotImplementedError()
