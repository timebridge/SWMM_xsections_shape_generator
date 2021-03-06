import re
from math import cos, radians
from os import path

from numpy import NaN, array, interp, argmax, ndarray, min, max, append
from pandas import isna, notna

from .helpers import sqrt, channel_end, Circle
from .shape_generator import CrossSection


class CrossSectionHolding(CrossSection):
    """
    cross section class for Holding Graz

    Attributes:
        add_dim (bool): add the dimension (height x width) to the label and output filename
        add_dn (bool): add the channel diameter (DN ...) to the label and output filename
    """

    def __init__(self, label, add_dim=False, add_dn=None, **kwargs):
        """Initialise the cross section class

        Args:
            label (str): name/label/number of the cross section
            add_dim (bool): if the dimensions should be added to :py:attr:`~out_filename` used for the export
            add_dn (Optional[float]): if the channel dimension should be added to :py:attr:`~out_filename`
                                    used for the export enter the diameter as float
            **kwargs (object): see :py:attr:`~__init__`

        Keyword Args:
            description (Optional[str]): optional description of the cross section
            height (float): absolute height of the CS
            width (Optional[float]): absolute width of the CS (optional) can be calculated
            working_directory (str): directory where the files get saved
            unit (Optional[str]): enter unit to add the unit in the plots

        """
        if isinstance(label, (float, int)):
            label = '{:0.0f}'.format(label)
        else:
            label = label

        if not label.startswith('Pr_'):
            label = 'Pr_' + label

        self.add_dim = add_dim
        self.add_dn = add_dn

        CrossSection.__init__(self, label, **kwargs)

    def __str__(self):
        s = CrossSection.__str__(self)
        if self.add_dim:
            s += '  |  {:0.0f}'.format(self.height)
            if self.width:
                s += 'x{:0.0f}'.format(self.width)

        if self.add_dn:
            s += '  |  DN{:0.0f}'.format(self.add_dn)
        return s

    @property
    def out_filename(self):
        """
        filename of the figure/text-file to be created

        Returns:
            str: filename

        """
        file = path.join(self.working_directory, '{}'.format(self.label))
        if self.add_dim:
            file += '_{:0.0f}'.format(self.height)
            if self.width:
                file += 'x{:0.0f}'.format(self.width)

        if self.add_dn:
            file += '_DN{:0.0f}'.format(self.add_dn)
        return file

    ####################################################################################################################
    @classmethod
    def standard(cls, label, description, height, width=NaN, r_channel=NaN, r_roof=NaN, r_wall=NaN, slope_bench=NaN,
                 r_round=NaN, r_wall_bottom=NaN, h_bench=NaN, pre_bench=NaN, w_channel=NaN, **kwargs):
        """
        standard cross section

        Args:
            label (str): see :py:attr:`~__init__`
            description (str): see :py:attr:`~__init__`
            height (float): see :py:attr:`~__init__`
            width (float): see :py:attr:`~__init__`

            r_channel (float): radius of the dry-weather channel (=Trockenwetter Rinne)

            w_channel (float): half width of the channel, only in combination with ``r_channel`` active
            pre_bench (float): slope of the upper end of the channel in degree, only in combination with
            ``r_channel`` active
            r_round (float): radius of the rounding of the edges, only in combination with ``r_channel`` active
            h_bench (float): height where the bench begins, only in combination with ``r_channel`` active
            slope_bench (float): slope of the bench (=Berme) in degree, or slope of the rainwater-floor (
            =Regenwetterrinne)

            r_roof (float): radius of the roof (=Decke)

            r_wall (float): radius of the sidewall (=Seitenwand), only in combination with ``r_roof`` active
            r_wall_bottom (float): radius of the bottom sidewall (=untere Seitenwand), only in combination with
            ``r_wall`` active

            **kwargs (object): see :py:attr:`~__init__`

        Keyword Args:
            working_directory (str): directory where the files get saved
            unit (Optional[str]): enter unit to add the unit in the plots

        Returns:
            CrossSectionHolding: standard cross section

        Examples:
            see :doc:`standard_cross_section`

        .. figure:: images/standard.gif
            :align: center
            :alt: standard cross section
            :figclass: align-center

            Standard cross section

        +---------+---------------------+
        | english | deutsch             |
        +=========+=====================+
        | channel | Trockenwetter-Rinne |
        +---------+---------------------+
        | roof    | Firste/Decke        |
        +---------+---------------------+
        | wall    | Seitenwand          |
        +---------+---------------------+
        | bench   | Berme               |
        +---------+---------------------+

        """

        # ------------------------------------------------
        cross_section = cls(label=label, description=description, height=height,
                            width=(width if notna(width) else None), **kwargs)

        # ------------------------------------------------
        # TW-Rinne
        if notna(r_channel):
            cross_section.add(Circle(r_channel, x_m=r_channel))

            # ------------------------------------------------
            if notna(pre_bench):
                cross_section.add(channel_end(r_channel, pre_bench))

                if notna(h_bench) or isna(slope_bench):
                    cross_section.add(pre_bench, '°slope')

                if notna(h_bench):
                    cross_section.add(h_bench)

            elif notna(w_channel):
                cross_section.add(None, w_channel)

            else:
                if notna(h_bench):
                    cross_section.add(h_bench)
                else:
                    cross_section.add(r_channel)
                    if isna(r_round):
                        r_round = 0
                    cross_section.add(r_channel + r_round, r_channel)

        # ------------------------------------------------
        if notna(slope_bench):
            # Berme winkel in °
            cross_section.add(slope_bench, '°slope')

        # ------------------------------------------------
        if isna(r_channel) and isna(slope_bench):
            cross_section.add(0, width / 2)

        # ------------------------------------------------
        if isna(r_roof):
            # eckige Decke
            cross_section.add(None, width / 2)
            cross_section.add(height, width / 2)

        else:
            if isna(r_wall):
                cross_section.add(None, width / 2)
                cross_section.add(height - r_roof, width / 2)
            else:
                # ------------------------------------------------
                h1 = sqrt((r_wall - r_roof) ** 2 - (r_wall - width / 2) ** 2)
                # h_middle = round(height - r_roof - h1, 8)
                h_middle = height - r_roof - h1

                # ------------------------------------------------
                if isna(r_wall_bottom):
                    cross_section.add(None, width / 2)
                    cross_section.add(h_middle, width / 2)

                else:
                    cross_section.add(Circle(r_wall_bottom, x_m=h_middle, y_m=width / 2 - r_wall_bottom))
                    cross_section.add(h_middle)

                # ------------------------------------------------
                cross_section.add(Circle(r_wall, x_m=h_middle, y_m=width / 2 - r_wall))
                cross_section.add(h_middle + h1 / (r_wall - r_roof) * r_wall)

            # ------------------------------------------------
            cross_section.add(Circle(r_roof, x_m=height - r_roof))

        # ------------------------------------------------
        return cross_section

    ####################################################################################################################
    @classmethod
    def box(cls, label, height, width, channel=None, bench=None, roof=None, rounding=0.0, **kwargs):
        """
        pre defined box (=Kasten) cross section

        Args:
            label (str): see :py:attr:`~__init__`
            height (float): see :py:attr:`~__init__`
            width (float): see :py:attr:`~__init__`
            channel (Optional[float]): diameter of the dry weather channel
            bench (Optional[float]): bench (=Berme)

                - ``''``: flache Berme
                - ``'R'``: V-förmiges Profil
                - ``'H'``: Schräge Verschneidung

            roof (Optional[float]): roof (=Decke)

                - ``''``: gerade
                - ``'B'``: Bogen
                - ``'K'``: Kreis

            rounding (Optional[float]): rounding of the edges
            **kwargs (object): see :py:attr:`~__init__`

        Keyword Args:
            description (Optional[str]): optional longer name of the cross section
            working_directory (str): directory where the files get saved
            unit (Optional[str]): enter unit to add the unit in the plots

        Returns:
            CrossSectionHolding: pre defined box (=Kasten) cross section

        Examples:
            see :doc:`show_case-kasten`
        """
        name = 'K'
        cross_section = cls(label=label, width=width, height=height, **kwargs)

        if isna(channel):
            channel = None
        else:
            channel = float(channel)

        if isna(bench):
            bench = ''

        if isna(roof):
            roof = ''

        if channel or bench:
            name += '.'
            bench = str(bench).strip()

            if isinstance(channel, float):
                name += '{:0.0f}'.format(channel)
                # diameter to radius
                channel /= 2
                cross_section.add(Circle(channel, x_m=channel))

            if isinstance(bench, str):
                if bench != '45':
                    name += str(bench)

                if bench == 'R':
                    cross_section.add(30, '%slope')
                    cross_section.add(None, width / 2)

                elif bench == 'H':
                    cross_section.add(channel_end(channel, 45))
                    cross_section.add(45, '°slope')
                    cross_section.add(None, width / 2)

                elif bench == '45':
                    cross_section.add(channel_end(channel, 45))
                    cross_section.add(45, '°slope')
                    cross_section.add(channel + rounding)
                    cross_section.add(channel + rounding, width / 2)

                else:
                    # Berme
                    # cross_section.add(channel, width / 2)
                    # cross_section.add(channel + rounding, width / 2)

                    if 1:
                        cross_section.add(channel_end(channel, 45))
                        cross_section.add(45, '°slope')
                    else:
                        cross_section.add(channel, channel)
                    cross_section.add(channel + rounding, None)
                    cross_section.add(5, '°slope')
                    cross_section.add(None, width / 2)

        else:
            # ebene Sohle
            cross_section.add(0, width / 2)

        if roof:
            name += '_' + str(roof)

            if roof == '':
                # gerade Decke
                cross_section.add(height, width / 2)

            elif roof == 'B':
                # Bogen-Decke
                cross_section.add(height - width * (1 - cos(radians(30))), width / 2)
                cross_section.add(Circle(width, x_m=height - width))

            elif roof == 'K':
                # Kreis Decke
                cross_section.add(height - width / 2, width / 2)
                cross_section.add(Circle(width / 2, x_m=height - width / 2))
        else:
            # gerade Decke
            cross_section.add(height, width / 2)

        if cross_section.label is None or cross_section.label == '':
            cross_section.label = name

        return cross_section

    ####################################################################################################################
    @classmethod
    def box_from_string(cls, label, **kwargs):
        """
        create pre defined box (=Kasten) cross section with the string label.

        This function takes the information from the label and pass them to the :py:attr:`~box` - function.

        Args:
            label (str): see the :doc:`show_case-kasten`
            **kwargs (object): see :py:attr:`~__init__`

        Keyword Args:
            height (float): see :py:attr:`~__init__`
            width (float): see :py:attr:`~__init__`
            rounding (Optional[float]): rounding of the edges
            description (Optional[str]): optional longer name of the cross section
            working_directory (str): directory where the files get saved
            unit (Optional[str]): enter unit to add the unit in the plots

        Returns:
            CrossSectionHolding: pre defined box (=Kasten) cross section

        Examples:
            see :doc:`show_case-kasten`

            .. figure:: images/Kasten-Profile.gif
                :align: center
                :alt: Kasten-Profile
                :figclass: align-center

                Kasten-Profile
        """
        infos = re.findall(r'(K)(\.?)(\d*)([RH]?)_?([BK]?)', label)  # _(\d+)x(\d+)
        if len(infos) == 1:
            infos = infos[0]
            _, _, channel, bench, roof = infos

            if channel != '':
                channel = float(channel)
            else:
                channel = None

            bench, roof = [x_ if x_ != '' else None for x_ in (bench, roof)]

            cross_section = cls.box(label, channel=channel, bench=bench, roof=roof, **kwargs)
            return cross_section

        # --------------------------------------
        else:
            raise NotImplementedError('"{}" unknown !'.format(label))

    @classmethod
    def from_point_cloud(cls, relative_coordinates, *args, **kwargs):
        """
        get the cross sections from a point cloud where every point is relative to the lowers point in the
        cross section

        Args:
            relative_coordinates (list[tuple[float, float]] | numpy.array): list of height- and width tuple
                                                  with the origin in the lowest point of the cross section
            *args: arguments, see :py:attr:`~__init__`
            **kwargs: keyword arguments, see :py:attr:`~__init__`

        Keyword Args:
            label (str): main name/label/number of the cross section
            description (Optional[str]): optional longer name of the cross section
            height (float): absolute height of the CS
            width (Optional[float]): absolute width of the CS (optional) can be calculated
            working_directory (str): directory where the files get saved
            unit (Optional[str]): enter unit to add the unit in the plots
            add_dim (bool): if the dimensions should be added to :py:attr:`~out_filename` used for the export
            add_dn (Optional[float]): if the channel dimension should be added to :py:attr:`~out_filename`
                                    used for the export enter the diameter as float

        Returns:
            CrossSectionHolding: of the point cloud

        .. figure:: images/point_cloud.gif
            :align: center
            :alt: point cloud
            :figclass: align-center

            Point cloud
        """
        if isinstance(relative_coordinates, (list, tuple)):
            x, y = zip(*relative_coordinates)
            x = array(x)
            y = array(y)
        elif isinstance(relative_coordinates, ndarray):
            x = relative_coordinates[:, 0]
            y = relative_coordinates[:, 1]
        else:
            raise NotImplementedError()

        height = max(y)
        width = max(x) - min(x)
        kwargs.update({'height': height, 'width': width})
        cross_section = cls(*args, **kwargs)

        # for the interpolation
        y = append(y, [0])
        x = append(x, [0])

        yi = sorted(set(y))
        xi = interp(yi, y[:argmax(y) + 1], x[:argmax(y) + 1]) - \
             interp(yi, y[::-1][:argmax(y[::-1]) + 1], x[::-1][:argmax(y[::-1]) + 1])
        xi /= 2
        for x, y in zip(yi, xi):
            if y == 0 and x in (0, height):
                continue
            cross_section.add(x, y)
        return cross_section
