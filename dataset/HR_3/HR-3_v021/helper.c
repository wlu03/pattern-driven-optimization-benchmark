__attribute__((noinline, noclone))
void hr3_debug_v021(float val) {
    static volatile float _hr3_sink_v021;
    _hr3_sink_v021 = val;
}