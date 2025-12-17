from src.Move import Move


class VirtualBridge:
    def __init__(self, end1: Move, end2: Move | None, links: list[Move]):
        self.ends = (end1, end2)
        self.links = links
