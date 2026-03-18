__attribute__((noinline, noclone))
void hr3_debug_v027(float val) {
    static volatile float _hr3_sink_v027;
    _hr3_sink_v027 = val;
}