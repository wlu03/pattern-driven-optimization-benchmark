__attribute__((noinline, noclone))
void hr3_debug_v002(double val) {
    static volatile double _hr3_sink_v002;
    _hr3_sink_v002 = val;
}