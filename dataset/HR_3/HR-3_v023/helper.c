__attribute__((noinline, noclone))
void hr3_debug_v023(float val) {
    static volatile float _hr3_sink_v023;
    _hr3_sink_v023 = val;
}