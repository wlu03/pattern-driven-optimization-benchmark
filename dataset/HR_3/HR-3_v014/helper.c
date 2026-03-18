__attribute__((noinline, noclone))
void hr3_debug_v014(double val) {
    static volatile double _hr3_sink_v014;
    _hr3_sink_v014 = val;
}