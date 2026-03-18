__attribute__((noinline, noclone))
void hr3_debug_v022(double val) {
    static volatile double _hr3_sink_v022;
    _hr3_sink_v022 = val;
}