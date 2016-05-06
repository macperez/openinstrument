import logging
import django.test
from mock import patch

from django.utils import timezone
from remoteinstrapp.models import Instrument, Command, Task, Config
from remoteinstrapp.app_management import manager

from daemonsceleryapp import tasks
from daemonsceleryapp.models import TempData


# Get an instance of a logger
logger = logging.getLogger(__name__)

SENDING_DATA_NUMBER_OF_TEMP_DATA_ROWS_ = 21


class A_CollectingDataTestCase(django.test.TestCase):
    """
    Test batteries for the method collect_data of tasks
    """
    def setUp(self):
        """
        Preload of instruments , with tasks, with commands
        """
        instruments = populate_instruments()
        tasks = populate_tasks(instruments)
        populateCommands(tasks)

    @patch.object(manager.QueryRawInstrumentManager, "execute_command")
    @patch.object(manager.WriteRawCommandManager, 'execute_command')
    def test_collect_data_ok(self, mock_QueryRawInstrumentManagerr_execute_command,
                             mock_WriteRawInstrumentManagerr_execute_command):
        """
        Test collect_data task. mocking two managers QueryRawInstrumentManager and WriteRawInstrumentManage

        :param mock_QueryRawInstrumentManagerr_execute_command: mock for this manager
        :param mock_WriteRawInstrumentManagerr_execute_command: mock for this manager

        """

        # Simulating the manager responses (if you do not have instruments connected)
        mock_QueryRawInstrumentManagerr_execute_command.return_value\
            = simulate_response()
        mock_WriteRawInstrumentManagerr_execute_command.return_value\
            = simulate_response()
        tasks.collect_data()
        tempdatas = TempData.objects.all()

        self.assertEqual(tempdatas.count(), 0) # if there is no instrument connected to the system



class B_SendingDataTestCase(django.test.TestCase):
    """
    Test batteries for the method send_data of tasks
    """

    def setUp(self):
        """
        Populate the data base with a configuration and temps data
        """
        # creating a configuration
        Config.objects.create(countryId='es',appId='cdp',defaultBackend='@py',
                              broker='django://',backend='db+mysql://ebd:ebd@127.0.0.1:1000/ebddatabase',
                              dataFormat='json',timezone='Europe/Madrid')

        # number of records in temp data table
        for n in range(SENDING_DATA_NUMBER_OF_TEMP_DATA_ROWS_):
            TempData.objects.create(instrumentId='IntsPrueba',
                                    parameterName='param'+str(n),
                                    user='user'+str(n),
                                    content='lectura ok',
                                    queryDate=timezone.now())


    def test_send_data(self):
        """
        The aim to test here is achieve that all the temp data created are sent and removed.
        """

        temps_data = TempData.objects.all()
        self.assertEqual(len(temps_data),SENDING_DATA_NUMBER_OF_TEMP_DATA_ROWS_)
        #tasks.send_data(_url='http://devdca.adevice.com.es',limit=15)
        tasks.send_data(limit=15)

        temps_data = TempData.objects.all()

        self.assertEqual(len(temps_data),0)



class C_CleaningDataTestCase(django.test.TestCase):
    """
    Test batteries for the method clean_data of tasks
    """
    def setUp(self):
        """
        Populate the data base with temps data
        """
        for n in range(SENDING_DATA_NUMBER_OF_TEMP_DATA_ROWS_):
            TempData.objects.create(instrumentId='instr'+str(n),
                                    parameterName='param'+str(n) ,
                                    user='user'+str(n),
                                    content='lectura ok',
                                    queryDate=timezone.now()-timezone.timedelta(minutes=n*10))

    def test_clean_data(self):
        """
        The aim to test here is achieve that all the temp data
        created older than a specific date, that it is supposed to be wrong sent,
        are cleaned after a given amount of time (minutes)
        """
        logger.info("Starting test_clean_data")
        temp_data = TempData.objects.all()
        self.assertEqual(len(temp_data),SENDING_DATA_NUMBER_OF_TEMP_DATA_ROWS_)
        # Firstly we removed the records older than 200 minutes (from now), Only it will remain the last record.

        tasks.clean_data(199)
        temp_data = TempData.objects.all()
        self.assertEqual(len(temp_data),SENDING_DATA_NUMBER_OF_TEMP_DATA_ROWS_-1)

        # Secondly we removed the records with a difference greater than 10 mintues.
        # It will only remain one record, the first.

        tasks.clean_data(10)
        temp_data = TempData.objects.all()
        self.assertEqual(len(temp_data),1)
        self.assertEqual(temp_data[0].instrumentId,'instr0')
################################################################################################



def simulate_response():

        _r = manager.Response()
        _r.response_data['state']='success'
        _r.response_data['result']= "resultado de prueba"
        return _r


# Creando 5 comandos, tres para la tarea 1 y dos para la tarea2.
def populateCommands(tasks):
    t1_c1 = Command(
        commandId='t0_c1',
        task=tasks[0],
        seqNumber=1,
        method='query_raw',
        message='0001000000060501006f0003',
        termination='\\r\\n',
        encoding='ascii',
        size=100
    )
    t1_c1.save()
    t1_c2 = Command(
        commandId='t0_c2',
        task=tasks[0],
        seqNumber=2,
        method='query_raw',
        message='0001000000060501006f0003',
        termination='\\r\\n',
        encoding='ascii',
        size=100
    )
    t1_c2.save()

    t1_c3 = Command(
        commandId='t0_c3',
        task=tasks[0],
        seqNumber=3,
        method='query_raw',
        message='0001000000060501006f0003',
        termination='\\r\\n',
        encoding='ascii',
        size=100
    )
    t1_c3.save()
    t2_c1 = Command(
        commandId='t2_c1',
        task=tasks[1],
        seqNumber=1,
        method='write_raw',
        message='0001000000060501006f0003',
        termination='\\r\\n',
        encoding='ascii',
        size=100
    )
    t2_c1.save()
    t2_c2 = Command(
        commandId='t2_c2',
        task=tasks[1],
        seqNumber=2,
        method='query_raw',
        message='0001000000060501006f0003',
        termination='\\r\\n',
        encoding='ascii',
        size=100
    )
    t2_c2.save()


def populate_tasks(instruments):
    task0 = Task(
        taskId='0',
        instrument=instruments[0],
        description='Recogida de datos',
        parameterName='waterTemperature2',
        user='aperez',
        retries=1,
        priority=2,
        active=True
    )
    task1 = Task(
        taskId='1',
        instrument=instruments[0],
        description='Recogida d',
        parameterName='waterTemperature2',
        user='aperez',
        retries=1,
        priority=2,
        active=True
    )
    task2 = Task(
        taskId='2',
        instrument=instruments[1],
        description='Recogida d',
        parameterName='waterTemperature2',
        user='aperez',
        retries=1,
        priority=2,
        active=True
    )
    task0.save()
    task1.save()
    task2.save()
    return task0, task1, task2


def populate_instruments():
    beagle = Instrument(
        instrumentId='beagle-1',
        visaId='ASRL/dev/ttyUSB0::INSTR',
        backend='@py',
        description='Concentrador de ONE-GO (BeagleBone)',
        interface='rs2222',
        protocol='ascii',
        taskInterval=5,
        active=True
    )
    beagle.save()
    gps = Instrument(
        instrumentId='gpsfeed-1',
        visaId='ASRL/dev/ttyUSB0::INSTR',
        backend='@py',
        description='Concentrador de ONE-GO (BeagleBone)',
        interface='rs2222',
        protocol='ascii',
        taskInterval=5,
        active=False
    )
    gps.save()
    meteo = Instrument(
        instrumentId='vxt520_1-1',
        visaId='ASRLCOM3::INSTR',
        backend='@py',
        description='Estacion meteorologica VAISALA',
        interface='rs232',
        protocol='ascii',
        taskInterval=5,
        active=True
    )
    meteo.save()

    return beagle, gps, meteo
