__attribute__((noinline, noclone))
void hr3_debug_v028(float val) {
    static volatile float _hr3_sink_v028;
    _hr3_sink_v028 = val;
}