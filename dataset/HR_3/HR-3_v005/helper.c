__attribute__((noinline, noclone))
void hr3_debug_v005(double val) {
    static volatile double _hr3_sink_v005;
    _hr3_sink_v005 = val;
}