__attribute__((noinline, noclone))
void hr3_debug_v016(float val) {
    static volatile float _hr3_sink_v016;
    _hr3_sink_v016 = val;
}