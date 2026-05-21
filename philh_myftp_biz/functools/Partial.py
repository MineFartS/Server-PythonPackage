from functools import partial

class Partial[T](partial[T]):

    def __call__(self, *args, **kwargs):

        return super().__call__(*self.args, *args, **kwargs)

        