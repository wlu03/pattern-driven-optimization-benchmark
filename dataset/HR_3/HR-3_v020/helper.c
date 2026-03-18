__attribute__((noinline, noclone))
void hr3_debug_v020(double val) {
    static volatile double _hr3_sink_v020;
    _hr3_sink_v020 = val;
}