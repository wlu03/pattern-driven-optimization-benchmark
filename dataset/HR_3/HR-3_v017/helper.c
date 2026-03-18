__attribute__((noinline, noclone))
void hr3_debug_v017(double val) {
    static volatile double _hr3_sink_v017;
    _hr3_sink_v017 = val;
}