#!/usr/bin/python3
from __future__ import print_function

from math          import pi, sqrt, acosh, sin, cos
from argparse      import ArgumentParser
from antenna_model import Antenna_Model, Antenna_Optimizer, Excitation

c0 = 2.99792458e8

def transmission_line_z (wire_dia, wire_dist, eps_r = 1.00054) :
    """ Impedance of transmission line
        https://hamwaves.com/zc.circular/en/
        Default eps_r is for air.
        The wire_dist is the distance (center to center) of the two
        wires. Both need to have the same dimension (e.g. mm or cm or in).
    """
    mu0  = 4e-7 * pi
    eps0 = 1 / (mu0 * c0 ** 2)
    z0   = sqrt (mu0 / eps0)
    zc   = z0 / (pi * sqrt (eps_r)) * acosh (wire_dist / wire_dia)
    return zc
# end def transmission_line_z

def phase_shift (f, length, vf = 1) :
    """ Compute phase shift in radians for a phasing stub with the given
        length and the given frequency f (Hz).
    >>> print ("%1.3f" % phase_shift (435000000, .35))
    3.191
    """
    lamb  = c0 / f
    lvf   = lamb * vf
    phase = (length % lvf) / lvf * 2 * pi
    return phase
# end def phase_shift

def complex_voltage (phi, u = 1) :
    """ Given a phase phi (in rad) and a voltage (with only real part)
        return the complex voltage (real, imag)
    >>> print ("%2.3f %2.3f" % complex_voltage (pi))
    -1.000 0.000
    >>> print ("%2.3f %2.3f" % complex_voltage (2 * pi))
    1.000 -0.000
    >>> print ("%2.3f %2.3f" % complex_voltage (pi / 2))
    0.000 1.000
    >>> print ("%2.3f %2.3f" % complex_voltage (3 * pi / 2))
    -0.000 -1.000
    >>> print ("%2.3f %2.3f" % complex_voltage (pi / 6))
    0.866 0.500
    >>> print ("%2.3f %2.3f" % complex_voltage (pi + pi / 6))
    -0.866 -0.500
    """
    return (u * cos (phi), u * sin (phi))
# end def complex_voltage

class HB9CV (Antenna_Model) :
    """ The HB9CV antenna is a two-element yagi-uda antenna.
        It uses transmission lines for off-center feeding.
        The feedpoint is between the middle of the reflector and two
        connected transmission lines. When viewed with the reflector at
        the front and the director at the back, the length l5 is the
        distance from the middle if the reflector to the feedpoint on
        the right of the reflector. The length l4 is the distance from
        the middle of the director to the left feedpoint on the
        director.
    """

    director      = 317.2e-3
    reflector     = 344.8e-3
    refl_dist     = 86.2e-3
    l4            = 43.1e-3
    l5            = 46.55e-3
    stub_height   = 5e-3
    segs_dipole   = 19
    segs_stub     =  1 # When using transmission line we use 1 here
    segs_boom     =  5
    segs_h        =  5

    def __init__ \
        ( self
        , director      = director
        , reflector     = reflector
        , refl_dist     = refl_dist
        , l4            = l4
        , l5            = l5
        , stub_height   = stub_height
        , ** kw
        ) :
        self.director    = director
        self.reflector   = reflector
        self.refl_dist   = refl_dist
        self.l4          = l4
        self.l5          = l5
        self.stub_height = stub_height
        self.__super.__init__ (**kw)
    # end def __init__

    def cmdline (self) :
        return \
            ("-l %(director)1.4f -r %(reflector)1.4f " \
             "-d %(refl_dist)1.4f -4 %(l4)1.4f -5 %(l5)1.4f "
             "-H %(stub_height)1.4f" % self.__dict__
            )
    # end def cmdline

    def geometry (self, nec = None) :
        if nec is None :
            nec = self.nec
        geo = nec.get_geometry ()
        self.tag = 1
        self.ex  = None

        # Director
        geo.wire \
            ( self.tag
            , self.segs_dipole
            , self.refl_dist,                    0, 0
            , self.refl_dist, -self.director / 2.0, 0
            , self.wire_radius
            , 1, 1
            )
        self.tag += 1
        # Second half of Director needs to be modelled in two parts,
        # because stub connection must be at end of wire(s)
        geo.wire \
            ( self.tag
            , self.segs_stub
            , self.refl_dist,       0, 0
            , self.refl_dist, self.l4, 0
            , self.wire_radius
            , 1, 1
            )
        self.tag += 1
        if self.director / 2.0 > self.l4 :
            geo.wire \
                ( self.tag
                , self.segs_stub
                , self.refl_dist,             self.l4, 0
                , self.refl_dist, self.director / 2.0, 0
                , self.wire_radius
                , 1, 1
                )
            self.tag += 1

        # Reflector
        geo.wire \
            ( self.tag
            , self.segs_dipole
            , 0,                    0, 0
            , 0, self.reflector / 2.0, 0
            , self.wire_radius
            , 1, 1
            )
        self.tag += 1
        # Second half of Reflector needs to be modelled in two parts,
        # because stub connection must be between end of wire(s).
        geo.wire \
            ( self.tag
            , self.segs_stub
            , 0,        0, 0
            , 0, -self.l5, 0
            , self.wire_radius
            , 1, 1
            )
        self.tag += 1
        if self.reflector / 2.0 > self.l5 :
            geo.wire \
                ( self.tag
                , self.segs_stub
                , 0,              -self.l5, 0
                , 0, -self.reflector / 2.0, 0
                , self.wire_radius
                , 1, 1
                )
            self.tag += 1
        # Boom
        geo.wire \
            ( self.tag
            , self.segs_boom
            , 0,              0, 0
            , self.refl_dist, 0, 0
            , self.boom_radius
            , 1, 1
            )
        self.tag += 1
        # Single segment wire from boom to phasing on director side
        # Used for feed
        geo.wire \
            ( self.tag
            , 1
            , self.refl_dist, 0, 0
            , self.refl_dist, 0, self.stub_height
            , self.wire_radius
            , 1, 1
            )
        self.ex = Excitation (self.tag, 1)
        self.tag  += 1
        # Connect Director Stub to Director
        geo.wire \
            ( self.tag
            , self.segs_stub
            , self.refl_dist, self.l4,                0
            , self.refl_dist, self.l4, self.stub_height
            , self.wire_radius
            , 1, 1
            )
        #director_stub_tag = self.tag
        self.tag  += 1
        # Connect Reflector Stub to Reflector
        geo.wire \
            ( self.tag
            , self.segs_stub
            , 0, -self.l5,                0
            , 0, -self.l5, self.stub_height
            , self.wire_radius
            , 1, 1
            )
        #reflector_stub_tag = self.tag
        self.tag  += 1
        # Experiment with two feedpoints: Doesn't work as it's
        # impossible to then find out what the impedance of the real
        # feedpoint would be.
        # Phasing and feed from stub on boom to stub on director
        #geo.wire \
        #    ( self.tag
        #    , 1
        #    , self.refl_dist,       0, self.stub_height
        #    , self.refl_dist, self.l4, self.stub_height
        #    , self.wire_radius
        #    , 1, 1
        #    )
        #self.ex    = []
        #frq = self.frqstart + (self.frqend - self.frqstart) / 2
        #phi = phase_shift (frq, self.l4)
        #u_real, u_imag = complex_voltage (phi)
        #self.ex.append (Excitation (self.tag, 1, u_real, u_imag))
        #self.tag += 1
        # Phasing and feed from stub on boom to stub on reflector
        #geo.wire \
        #    ( self.tag
        #    , 1
        #    , self.refl_dist,        0, self.stub_height
        #    ,              0, -self.l5, self.stub_height
        #    , self.wire_radius
        #    , 1, 1
        #    )
        #phi = phase_shift (frq, self.l5 + self.refl_dist)
        #u_real, u_imag = complex_voltage (phi)
        #self.ex.append (Excitation (self.tag, 1, u_real, u_imag))
        #self.tag += 1

        # Wire from lower part of feedpoint to upper part of director
        # stub: Used as transmisssion-line endpoint
        geo.wire \
            ( self.tag
            , 1
            , self.refl_dist,        0, 0
            ,              0, -self.l5, self.stub_height
            , self.wire_radius
            , 1, 1
            )
        reflector_stub_tag = self.tag
        self.tag += 1

        # Wire from lower part of feedpoint to upper part of reflector
        # stub: Used as transmisssion-line endpoint
        geo.wire \
            ( self.tag
            , 1
            , self.refl_dist,       0, 0
            , self.refl_dist, self.l4, self.stub_height
            , self.wire_radius
            , 1, 1
            )
        director_stub_tag = self.tag
        self.tag += 1

        nec.geometry_complete (0)
        impedance = transmission_line_z (self.wire_radius * 2, self.stub_height)
        nec.tl_card \
            ( self.ex.tag, self.ex.segment
            , reflector_stub_tag, 1
            , impedance
            , self.refl_dist + self.l5
            , 0, 0, 0, 0
            )
        nec.tl_card \
            ( self.ex.tag, self.ex.segment
            , director_stub_tag, 1
            , impedance
            , self.l4
            , 0, 0, 0, 0
            )
    # end def geometry

# end class HB9CV

class HB9CV_Optimizer (Antenna_Optimizer) :
    """ Optimize given folded dipole
        Length are encoded with a resolution of .5mm
        We use:
        * 25cm   <= director    <= 35cm
        * 25cm   <= reflector   <= 35cm
        *  5cm   <= refl_dist   <= 15cm
        *  3cm   <= l4          <= 10cm
        *  3cm   <= l5          <= 10cm
        *  5mm   <= stub_height <= 1.5cm
    """

    def __init__ (self, **kw) :
        self.minmax = \
            [ (0.25, 0.35), (0.25, 0.35), (0.05, 0.15)
            , (0.03, 0.1),  (0.03, 0.1),  (0.005, 0.015)
            ]
        self.__super.__init__ (**kw)
    # end def __init__

    def compute_antenna (self, p, pop) :
        director      = self.get_parameter (p, pop, 0)
        reflector     = self.get_parameter (p, pop, 1)
        refl_dist     = self.get_parameter (p, pop, 2)
        l4            = self.get_parameter (p, pop, 3)
        l5            = self.get_parameter (p, pop, 4)
        h             = self.get_parameter (p, pop, 5)
        fd = HB9CV \
            ( director      = director
            , reflector     = reflector
            , refl_dist     = refl_dist
            , l4            = l4
            , l5            = l5
            , stub_height   = h
            , frqidxmax     = 3
            , wire_radius   = self.wire_radius
            )
        return fd
    # end def compute_antenna

# end class HB9CV_Optimizer

if __name__ == '__main__' :
    actions = ['optimize', 'necout', 'swr', 'gain', 'frgain']
    cmd = ArgumentParser ()
    cmd.add_argument \
        ( 'action'
        , help = "Action to perform, one of %s" % ', '.join (actions)
        )
    cmd.add_argument \
        ( '-4', '--l4'
        , type    = float
        , help    = "Length of l4 (stub on director side)"
        , default = 0.0431
        )
    cmd.add_argument \
        ( '-5', '--l5'
        , type    = float
        , help    = "Length of l5 (stub on reflector side)"
        , default = 0.04655
        )
    cmd.add_argument \
        ( '-d', '--reflector-distance'
        , type    = float
        , help    = "Distance of the reflector from nearest dipole part"
        , default = 0.0862
        )
    cmd.add_argument \
        ( '-H', '--stub-height'
        , type    = float
        , help    = "Height of stubs above antenna"
        , default = '0.017'
        )
    cmd.add_argument \
        ( '-l', '--director-length'
        , type    = float
        , help    = "Length of the director"
        , default = 0.3172
        )
    cmd.add_argument \
        ( '-R', '--random-seed'
        , type    = int
        , help    = "Random number seed for optimizer, default=%(default)s"
        , default = 42
        )
    cmd.add_argument \
        ( '-r', '--reflector-length'
        , type    = float
        , help    = "Length of the reflector"
        , default = 0.3448
        )
    cmd.add_argument \
        ( '-w', '--wire-radius'
        , type    = float
        , help    = "Radius of the wire"
        , default = 0.00075
        )
    cmd.add_argument \
        ( '-v', '--verbose'
        , help    = "Verbose reporting in every generation"
        , action  = 'store_true'
        )
    args = cmd.parse_args ()
    if args.action == 'optimize' :
        do = HB9CV_Optimizer \
            ( verbose     = args.verbose
            , random_seed = args.random_seed
            , wire_radius = args.wire_radius
            )
        do.run ()
    else :
        frqidxmax = 201
        if args.action in ('frgain', 'necout') :
            frqidxmax = 3
        fd = HB9CV \
            ( director      = args.director_length
            , reflector     = args.reflector_length
            , refl_dist     = args.reflector_distance
            , l4            = args.l4
            , l5            = args.l5
            , stub_height   = args.stub_height
            , wire_radius   = args.wire_radius
            , frqidxmax     = frqidxmax
            )
        if args.action == 'necout' :
            print (fd.as_nec ())
        elif args.action not in actions :
            cmd.print_usage ()
        else :
            fd.compute ()
        if args.action == 'swr' :
            fd.swr_plot ()
        elif args.action == 'gain' :
            fd.plot ()
        elif args.action == 'frgain' :
            print ('\n'.join (fd.show_gains ()))
