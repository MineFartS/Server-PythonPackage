
class Weights:
    """```

    class WeightsImpl(Weights):
        def TITLE(self, sample, control):
            return (sample == control)
    
    weights = WeightsImpl(
        TITLE = 'MyTitle'
    )

    weights(
        TITLE = 'MyTitle1'
    ) -> False

    weights(
        TITLE = 'MyTitle'
    ) -> True

    ```"""
    
    def __init__(self, **controls):
        self.controls = controls

    def __call__(self, **samples) -> bool:
        from ..terminal import Log

        logm: str = f'Weighing Samples:'
        valid = True

        for key, control in self.controls.items():

            sample = samples[key]

            _valid = getattr(self, key)(
                sample = sample,
                control = control
            )

            valid &= _valid

            logm += f'\n{key}={_valid:d} | {sample=} | {control=}'

        logm += f'\n{valid=}'
 
        Log.VERB(logm)

        return valid

