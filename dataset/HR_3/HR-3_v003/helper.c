__attribute__((noinline, noclone))
void hr3_debug_v003(double val) {
    static volatile double _hr3_sink_v003;
    _hr3_sink_v003 = val;
}