#!/usr/bin/python3
from __future__ import print_function

from antenna_model import Antenna_Model, Antenna_Optimizer, Excitation
from antenna_model import Arg_Handler
from coaxmodel     import belden_8295, sytronic_RG213UBX, sytronic_RG_58_CU

class Transmission_Line_Match (Antenna_Model) :
    wire_radius = 2e-3
    wire_len    = 0.005
    # Use wire_len for transmission lines: Since we're specifying the
    # transmission line length as a parameter to the TL card anyway we
    # can simplify the structure by not reserving so much space.
    use_wlen    = True
    feed_len    =  9.86
    z0          = 50.0
    frqstart    = 3.499
    frqend      = 3.501
    phi_inc     = 180
    theta_inc   = 90
    theta_max   = int (180 / theta_inc + 1)
    phi_max     = int (360 / phi_inc   + 1)
    z_load      = 150.0

    def __init__ \
        ( self
        , stub_dist
        , stub_len
        , is_open   = False
        , is_series = False
        , f_mhz     = None
        , coaxmodel = None
        , z_load    = None
        , **kw
        ) :
        self.stub_dist = stub_dist
        self.stub_len  = stub_len
        self.is_open   = is_open
        self.is_series = is_series
        self.coaxmodel = coaxmodel
        if z_load is not None :
            self.z_load = z_load
        if f_mhz is not None :
            self.frqstart  = f_mhz - 0.01
            self.frqend    = f_mhz + 0.01
        self.f_mhz     = (self.frqstart + self.frqend) / 2.0
        self.frequency = self.f_mhz * 1e6

        if self.coaxmodel :
            self.coaxmodel.f = self.frequency
        self.__super.__init__ (**kw)
    # end def __init__

    def cmdline (self) :
        r = []
        if self.is_open :
            r.append ('--is-open')
        if self.is_series :
            r.append ('--is-series')
        if self.coaxmodel :
            r.append ('-c %s' % self.coaxmodel.name)
        r.append ('-d %(stub_dist)1.10f')
        r.append ('-l %(stub_len)1.10f')
        r.append ('-f %(f_mhz)1.2f')
        r.append ('-z %.2f%+.2fj' % (self.z_load.real, self.z_load.imag))
        return ' '.join (r) % self.__dict__
    # end def cmdline

    def geometry (self, nec = None) :
        if nec is None :
            nec = self.nec
        geo = nec.get_geometry ()
        sd = self.stub_dist
        if self.use_wlen :
            sd = self.wire_len
        sl = self.stub_len
        if self.use_wlen :
            sl = self.wire_len
        fl = self.feed_len
        if self.use_wlen :
            fl = self.wire_len
        self.tag = 1
        self.ex  = None
        geo.wire \
            ( self.tag
            , 1
            , 0,             0, 0
            , self.wire_len, 0, 0
            , self.wire_radius
            , 1, 1
            )
        self.load_wire_tag = self.tag
        self.tag += 1
        geo.wire \
            ( self.tag
            , 1
            , 0,             sd, 0
            , self.wire_len, sd, 0
            , self.wire_radius
            , 1, 1
            )
        self.stub_point_tag = self.tag
        self.tag += 1
        if self.is_series :
            geo.wire \
                ( self.tag
                , 1
                , 0, sd,                 0
                , 0, sd + self.wire_len, 0
                , self.wire_radius
                , 1, 1
                )
            self.tag += 1
            geo.wire \
                ( self.tag
                , 1
                , self.wire_len, sd,                 0
                , self.wire_len, sd + self.wire_len, 0
                , self.wire_radius
                , 1, 1
                )
            self.stub_start_tag = self.tag
            self.tag += 1
            geo.wire \
                ( self.tag
                , 1
                , self.wire_len + sl, sd,                 0
                , self.wire_len + sl, sd + self.wire_len, 0
                , self.wire_radius
                , 1, 1
                )
            self.stub_end_tag = self.tag
            self.tag += 1
            geo.wire \
                ( self.tag
                , 1
                , 0,             sd + self.wire_len, 0
                , self.wire_len, sd + self.wire_len, 0
                , self.wire_radius
                , 1, 1
                )
            self.feed_end_tag = self.tag
            self.tag += 1
        else :
            self.stub_start_tag = self.tag - 1
            self.feed_end_tag   = self.tag - 1
            geo.wire \
                ( self.tag
                , 1
                , 0,             sd, -sl
                , self.wire_len, sd, -sl
                , self.wire_radius
                , 1, 1
                )
            self.stub_end_tag = self.tag
            self.tag += 1
        feedlen = sd + fl
        if self.is_series :
            feedlen += self.wire_len
        geo.wire \
            ( self.tag
            , 1
            , 0,             feedlen, 0
            , self.wire_len, feedlen, 0
            , self.wire_radius
            , 1, 1
            )
        self.ex = Excitation (self.tag, 1)
        nec.geometry_complete (0)
        if self.coaxmodel :
            y11 = coaxmodel.y11 (self.frequency, self.stub_dist)
            y12 = coaxmodel.y12 (self.frequency, self.stub_dist)
            y22 = coaxmodel.y22 (self.frequency, self.stub_dist, self.z_load)
            nec.nt_card \
                ( self.stub_point_tag, 1
                , self.load_wire_tag,  1
                , y11.real, y11.imag
                , y12.real, y12.imag
                , y22.real, y22.imag
                )
        else :
            y_load = 1 / self.z_load
            nec.tl_card \
                ( self.stub_point_tag, 1
                , self.load_wire_tag,  1
                , self.z0
                , self.stub_dist
                , 0, 0, y_load.real, y_load.imag
                )
        # The stub termination is an admittance!
        y_stub = 1e30
        z_coax = 0.0
        if self.is_open :
            y_stub = 0
            # We *can* model an open circuit in coaxmodel
            z_coax = None
        if self.coaxmodel :
            y11 = coaxmodel.y11 (self.frequency, self.stub_len)
            y12 = coaxmodel.y12 (self.frequency, self.stub_len)
            y22 = coaxmodel.y22 (self.frequency, self.stub_len, z_coax)
            nec.nt_card \
                ( self.stub_start_tag, 1
                , self.stub_end_tag,   1
                , y11.real, y11.imag
                , y12.real, y12.imag
                , y22.real, y22.imag
                )
        else :
            # Well, y_stub is real for now, but this may change
            nec.tl_card \
                ( self.stub_start_tag, 1
                , self.stub_end_tag,   1
                , self.z0
                , self.stub_len
                , 0, 0, y_stub.real, y_stub.imag
                )
        nec.tl_card \
            ( self.ex.tag,       self.ex.segment
            , self.feed_end_tag, 1
            , self.z0
            , self.feed_len
            , 0, 0, 0, 0
            )
    # end def geometry
# end class Transmission_Line_Match

class Transmission_Line_Optimizer (Antenna_Optimizer) :

    def __init__ \
        ( self
        , is_open      = False
        , is_series    = False
        , add_lambda_4 = False
        , f_mhz        = None
        , coaxmodel    = None
        , z_load       = 150.0
        , **kw
        ) :
        self.is_open      = is_open
        self.is_series    = is_series
        self.add_lambda_4 = add_lambda_4
        self.f_mhz        = f_mhz
        self.coaxmodel    = coaxmodel
        self.z_load       = z_load
        c  = 3e8
        tl = Transmission_Line_Match
        if f_mhz is None :
            self.f_mhz = (tl.frqstart + tl.frqend) / 2
        self.lambda_4 = c / 1e6 / self.f_mhz / 4
        if self.coaxmodel :
            self.lambda_4 = self.coaxmodel.lamda (self.f_mhz * 1e6) / 4
        self.minmax = [(0, self.lambda_4), (0, 2 * self.lambda_4)]
        if self.add_lambda_4 :
            self.minmax [0] = (self.lambda_4, 2 * self.lambda_4)
        self.__super.__init__ (**kw)
    # end def __init__

    def compute_antenna (self, p, pop) :
        stub_dist = self.get_parameter (p, pop, 0)
        stub_len  = self.get_parameter (p, pop, 1)
        tl = Transmission_Line_Match \
            ( stub_dist      = stub_dist
            , stub_len       = stub_len
            , is_open        = self.is_open
            , is_series      = self.is_series
            , frqidxmax      = 3
            , wire_radius    = self.wire_radius
            , copper_loading = self.copper_loading
            , f_mhz          = self.f_mhz
            , coaxmodel      = self.coaxmodel
            , z_load         = self.z_load
            )
        return tl
    # end def compute_antenna

    def evaluate (self, p, pop) :
        self.neval += 1
        ant, vswrs, gmax, rmax, swr_eval, swr_med = self.phenotype (p, pop)
        return 1.0 / swr_med
    # end def evaluate

#    def print_string (self, file, p, pop) :
#        antenna, vswrs, gmax, rmax, swr_eval, swr_med = self.phenotype (p, pop)
#        print ("vswrs: %s" % vswrs, file = file)
#        print (antenna.as_nec (), file = file)
#    # end def print_string

# end class Transmission_Line_Optimizer

if __name__ == '__main__' :
    models = 'lossless', 'belden_8295', 'sytronic_RG213UBX', 'sytronic_RG_58_CU'
    cmd = Arg_Handler \
        ( wire_radius    = 0.002
        , frqidxmax      = 3
        , copper_loading = False
        )
    cmd.add_argument \
        ( '-c', '--coaxmodel'
        , help    = "Coax to model, one of %s" % ', '.join (models)
        , default = 'lossless'
        )
    cmd.add_argument \
        ( '-d', '--stub-distance'
        , type    = float
        , help    = "Distance of matching stub from load"
        , default = 7.106592973007906
        )
    cmd.add_argument \
        ( '-f', '--f-mhz'
        , type    = float
        , help    = "Frequency to match transmission line (MHz)"
        , default = 3.5
        )
    cmd.add_argument \
        ( '-l', '--stub-length'
        , type    = float
        , help    = "Length of matching stub"
        , default = 32.193495674862291
        )
    cmd.add_argument \
        ( '--is-open'
        , help    = "Use open stub"
        , action  = "store_true"
        )
    cmd.add_argument \
        ( '--is-series'
        , help    = "Use stub in series with transmission line"
        , action  = "store_true"
        )
    cmd.add_argument \
        ( '--add-lambda-4'
        , help    = "Add lambda/4 to the matching point (optimizer)"
        , action  = "store_true"
        )
    cmd.add_argument \
        ( '-z', '--z-load'
        , help    = "Impedance at load to be matched"
        , type    = complex
        )
    args = cmd.parse_args ()
    if args.coaxmodel not in models :
        print ('Invalid coax model: "%s"' % args.coaxmodel)
        cmd.print_usage ()
    if args.coaxmodel == 'lossless' :
        coaxmodel = None
    else :
        coaxmodel = globals () [args.coaxmodel]
    if args.action == 'optimize' :
        tlo = Transmission_Line_Optimizer \
            ( is_open      = args.is_open
            , is_series    = args.is_series
            , add_lambda_4 = args.add_lambda_4
            , f_mhz        = args.f_mhz
            , coaxmodel    = coaxmodel
            , z_load       = args.z_load
            , ** cmd.default_optimization_args
            )
        tlo.run ()
    else :
        tl = Transmission_Line_Match \
            ( stub_dist = args.stub_distance
            , stub_len  = args.stub_length
            , is_open   = args.is_open
            , is_series = args.is_series
            , f_mhz     = args.f_mhz
            , coaxmodel = coaxmodel
            , z_load    = args.z_load
            , ** cmd.default_antenna_args
            )
        if args.action == 'necout' :
            print (tl.as_nec ())
        elif args.action not in actions :
            cmd.print_usage ()
        else :
            tl.compute ()
        if args.action == 'swr' :
            tl.swr_plot ()
        elif args.action == 'gain' :
            tl.plot ()
        elif args.action == 'frgain' :
            print ('\n'.join (tl.show_gains ()))
