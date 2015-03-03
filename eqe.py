import visa
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from srs import SR570
from ametek import SR7230
from arc import SpecPro
from time import sleep

plt.interactive(True)
fg, ax = plt.subplots()
lns, = ax.plot([],[],'o-')
ax.set_autoscale_on(True)



SiRd = np.genfromtxt("12187.csv", skip_header=1, delimiter=",")
SiR = interp1d(SiRd[:,0], SiRd[:,1], kind='cubic')

rm = visa.ResourceManager()

tia_in = rm.open_resource("ASRL1::INSTR", baud_rate=9600, data_bits=8, stop_bits=visa.constants.StopBits.two,write_termination='\r\n')
tia = SR570(tia_in)

lia_in = rm.open_resource("TCPIP::169.254.150.230::50000::SOCKET", read_termination='\0',  write_termination='\0')
lia = SR7230(lia_in)

mon = SpecPro(4, "")

lam = np.arange(300, 605, 5)

dwell = lia.filter_time_constant*6

tia.sensitivity = 500e-6

sens = tia.sensitivity

mvolt = np.zeros(lam.shape)
mphas = np.zeros(lam.shape)
mlam = np.zeros(lam.shape)
mcur = np.zeros(lam.shape)
mpow = np.zeros(lam.shape)

p = DynamicPlot()

#for idx, l in enumerate(lam):
#    sleep(dwell)
#    p.update(l,1240.0/l)
    
for idx, l in enumerate(lam):
    mon.wavelength = l
    sleep(dwell)
    mlam[idx] = mon.wavelength
    tmp = lia.magphase
    mvolt[idx] = tmp[0]
    mphas[idx] = tmp[1]
    mcur[idx] = mvolt[idx]*sens
    mpow[idx] = mcur[idx]*SiR(mlam[idx])
    p.update(mlam[idx], mpow[idx])
    # lns.set_xdata(np.append(lns.get_xdata(), mlam[idx]))
    #lns.set_ydata(np.append(lns.get_ydata(), mpow[idx]))
    #ax.relim()
    #ax.autoscale_view()
    #plt.draw()
    # fg.canvas.draw()
    # fg.canvas.flush_events()

mon.close()
tia_in.close()
lia_in.close()

class DynamicPlot():
    
    def __init__(self):
        #Set up plot
        self.figure, self.ax = plt.subplots()
        self.lines, = self.ax.plot([],[], 'o-')
        #Autoscale on unknown axis and known lims on the other
        self.ax.set_autoscale_on(True)

    def update(self, newx, newy):
        #Update data (with the new _and_ the old points)
        self.lines.set_xdata(np.append(self.lines.get_xdata(), newx))
        self.lines.set_ydata(np.append(self.lines.get_ydata(), newy))
        #Need both of these in order to rescale
        self.ax.relim()
        self.ax.autoscale_view()
        #We need to draw *and* flush
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()