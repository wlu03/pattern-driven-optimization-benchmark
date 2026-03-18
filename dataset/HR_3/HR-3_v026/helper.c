__attribute__((noinline, noclone))
void hr3_debug_v026(double val) {
    static volatile double _hr3_sink_v026;
    _hr3_sink_v026 = val;
}