__attribute__((noinline, noclone))
void hr3_debug_v029(float val) {
    static volatile float _hr3_sink_v029;
    _hr3_sink_v029 = val;
}