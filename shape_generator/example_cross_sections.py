from . import Circle, CrossSection


class EggSection(CrossSection):
    def __init__(self, r, label=None, description=None):
        R = 3 * r
        roh = r / 2
        height = r * 3
        width = r * 2
        # h1 = roh - (r + roh) / (R - roh) * roh
        h1 = 0.2 * r

        if label is None:
            label = 'Ei {:0.0f}/{:0.0f}'.format(width, height)

        CrossSection.__init__(self, label=label, description=description, width=width, height=height)
        self.add(Circle(roh, x_m=roh))
        self.add(h1)
        self.add(Circle(R, x_m=2 * r, y_m=-(R - r)))
        self.add(2 * r)
        self.add(Circle(r, x_m=2 * r))


class CircleSection(CrossSection):
    def __init__(self, r, label=None, description=None):
        d = 2 * r
        height = d
        width = d

        if label is None:
            label = 'DN {:0.0f}'.format(d)

        CrossSection.__init__(self, label=label, description=description, width=width, height=height)
        self.add(Circle(r, x_m=r))