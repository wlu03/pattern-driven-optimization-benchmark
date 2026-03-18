__attribute__((noinline, noclone))
void hr3_debug_v018(float val) {
    static volatile float _hr3_sink_v018;
    _hr3_sink_v018 = val;
}