from abc import ABC


class MsgPostProcessor(ABC):
    def process(self, msg: bytes) -> bytes:
        """
        Process the command. This usually means modifying the command,
        such as wrapping it inside a protocol such as RFC1055.
        :return:
        """
        raise NotImplementedError()
