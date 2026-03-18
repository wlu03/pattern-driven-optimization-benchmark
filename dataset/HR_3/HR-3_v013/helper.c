__attribute__((noinline, noclone))
void hr3_debug_v013(float val) {
    static volatile float _hr3_sink_v013;
    _hr3_sink_v013 = val;
}