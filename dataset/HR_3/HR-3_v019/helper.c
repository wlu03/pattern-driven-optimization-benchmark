__attribute__((noinline, noclone))
void hr3_debug_v019(double val) {
    static volatile double _hr3_sink_v019;
    _hr3_sink_v019 = val;
}