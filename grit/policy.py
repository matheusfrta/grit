class policy:
    def __init__(self, *layers):
        if not layers:
            raise ValueError("policy needs at least one layer")
        self.layers = layers

    def __call__(self, fn):
        for layer in reversed(self.layers):
            fn = layer(fn)
        return fn