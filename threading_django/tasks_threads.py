__author__ = 'macastro'


import threading
import time
from remoteinstrapp.models import Instrument

class MiThread(threading.Thread):

    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        print ("soy el thread "  + self.name)
        i = 0
        while i < 10:
            print ("estoy con mi tarea {0}".format(i) )
            time.sleep(2)
            instruments = Instrument.objects.all()
            for inst in instruments:
                print (inst)
            i+=1


