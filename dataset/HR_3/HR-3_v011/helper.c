__attribute__((noinline, noclone))
void hr3_debug_v011(float val) {
    static volatile float _hr3_sink_v011;
    _hr3_sink_v011 = val;
}