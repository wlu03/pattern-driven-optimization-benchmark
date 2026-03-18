__attribute__((noinline, noclone))
void hr3_debug_v025(float val) {
    static volatile float _hr3_sink_v025;
    _hr3_sink_v025 = val;
}