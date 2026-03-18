__attribute__((noinline, noclone))
void hr3_debug_v008(float val) {
    static volatile float _hr3_sink_v008;
    _hr3_sink_v008 = val;
}