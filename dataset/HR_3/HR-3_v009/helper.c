__attribute__((noinline, noclone))
void hr3_debug_v009(double val) {
    static volatile double _hr3_sink_v009;
    _hr3_sink_v009 = val;
}