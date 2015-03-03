from pyvd_common import within_limits


class LKS355():
    setpoint_range = [0, 325]

    def __init__(self, inst):
        self.inst = inst
        self.inst.write("*CLS")

    @property
    def heater1_range(self):
        return int(self.inst.query_ascii_values("RANGE? 1")[0])

    @heater1_range.setter
    def heater1_range(self, value):
        if (within_limits(int(value), [0, 3])):
            self.inst.write("RANGE 1,%d" % value)

    @property
    def heater2_range(self):
        return int(self.inst.query_ascii_values("RANGE? 2")[0])

    @heater2_range.setter
    def heater2_range(self, value):
        if (within_limits(int(value), [0, 3])):
            self.inst.write("RANGE 2,%d" % value)

    @property
    def heater1_output(self):
        return self.inst.query_ascii_values("HTR? 1")[0]

    @property
    def heater2_output(self):
        return self.inst.query_ascii_values("HTR? 2")[0]

    @property
    def heater1_setpoint(self):
        return self.inst.query_ascii_values("SETP? 1")[0]

    @heater1_setpoint.setter
    def heater1_setpoint(self, value):
        if (within_limits(value, self.setpoint_range)):
            self.inst.write("SETP 1,%f", value)

    @property
    def heater2_setpoint(self):
        return self.inst.query_ascii_values("SETP? 2")[0]

    @heater2_setpoint.setter
    def heater2_setpoint(self, value):
        if (within_limits(value, self.setpoint_range)):
            self.inst.write("SETP 2,%f", value)

    @property
    def heater1_output_enabled(self):
        return (
            within_limits(int(self.inst.query_ascii_values("OUTMODE? 1")[0]),
                          [1, 3]))

    @heater1_output_enabled.setter
    def heater1_output_enabled(self, value):
        if (value):
            self.inst.write("OUTMODE 1,1,1,0")
        else:
            self.inst.write("OUTMODE 1,4,1,0")

    @property
    def heater2_output_enabled(self):
        return (
            within_limits(int(self.inst.query_ascii_values("OUTMODE? 2")[0]),
                          [1, 3]))

    @heater2_output_enabled.setter
    def heater2_output_enabled(self, value):
        if (value):
            self.inst.write("OUTMODE 2,1,2,0")
        else:
            self.inst.write("OUTMODE 2,4,2,0")

    @property
    def temperature(self):
        return [
            self.inst.query_ascii_values("KRDG? A")[0],
            self.inst.query_ascii_values("KRDG? B")[0]
        ]

    @property
    def brightness(self):
        return int(self.inst.query_ascii_values("BRIGT?")[0])

    @brightness.setter
    def brightness(self, value):
        if (within_limits(int(value), [0, 4])):
            self.inst.write("BRIGT %d" % value)

    @property
    def leds(self):
        return (self.inst.query_ascii_values("LEDS?") == 1)

    @leds.setter
    def leds(self, value):
        if (value):
            self.inst.write("LEDS 1")
        else:
            self.inst.write("LEDS 0")
