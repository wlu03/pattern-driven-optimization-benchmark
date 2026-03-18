__attribute__((noinline, noclone))
void hr3_debug_v010(double val) {
    static volatile double _hr3_sink_v010;
    _hr3_sink_v010 = val;
}