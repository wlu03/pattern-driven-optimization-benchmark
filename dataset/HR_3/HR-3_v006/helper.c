__attribute__((noinline, noclone))
void hr3_debug_v006(float val) {
    static volatile float _hr3_sink_v006;
    _hr3_sink_v006 = val;
}