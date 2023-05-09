try:
    from typing import Optional, Sequence, Iterator, Union
    from typing_extensions import SupportsIndex
except ImportError:
    pass

class DiscardingQueue:
    """
    This implements a queue that will only go up to max_len items long, and then
    will discard the oldest elements. Used because circuitpython's Deque is very limited
    """
    def __init__(self, it: Optional[Sequence] = None, max_len: int = 10):
        self.max_len = max_len
        """Maximum number of items within the queue"""
        if it is not None:
            self.queue = list(it[-max_len:])

    def append(self, obj) -> None:
        """
        Add an item to the queue. Silently discard oldest item if this would make the queue too long

        :param obj: Object to add to the queue
        :return:
        """
        if len(self.queue) == self.max_len:
            self.pop()
        self.queue.append(obj)

    def pop(self):
        """
        Pop oldest item off the queue, remove that item from the queue
        :return: Oldest item
        """
        return self.queue.pop(0)

    def index(self, __value, __start: SupportsIndex = ..., __stop: SupportsIndex = ...) -> int:
        return self.queue.index(__value, __start, __stop)

    def __len__(self) -> int:
        return len(self.queue)

    def __iter__(self) -> Iterator:
        return iter(self.queue)

    def __getitem__(self, i: int):
        print(f"len is {len(self.queue)}, index is {i}")
        return self.queue[i]
