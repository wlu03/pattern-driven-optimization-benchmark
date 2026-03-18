__attribute__((noinline, noclone))
void hr3_debug_v004(double val) {
    static volatile double _hr3_sink_v004;
    _hr3_sink_v004 = val;
}