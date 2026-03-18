__attribute__((noinline, noclone))
void hr3_debug_v012(double val) {
    static volatile double _hr3_sink_v012;
    _hr3_sink_v012 = val;
}