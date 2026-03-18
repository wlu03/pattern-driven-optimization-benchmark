__attribute__((noinline, noclone))
void hr3_debug_v015(double val) {
    static volatile double _hr3_sink_v015;
    _hr3_sink_v015 = val;
}