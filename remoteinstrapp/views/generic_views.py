import re
import logging
from django.http import Http404
from django.db import DatabaseError
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from pyvisa import util

from remoteinstrapp.permission import SimpleAuthentication, GivingPermissions
from remoteinstrapp.models import Instrument, Config, Capability, Characteristics, Task, Command
from remoteinstrapp.serializers import InstrumentSerializer, \
    ConfigInstrumentSerializer, ConfigSerializer, \
    ConfigTaskSerializer, CapabilitySerializer, \
    CharacteristicSerializer, TaskSerializer, CommandSerializer, ListResourcesSerializer, get_instrument, get_task

from django.conf import settings
from remoteinstrapp.app_management import manager



# Get an instance of a logger
logger = logging.getLogger(__name__)


class InstrumentList(APIView):
    """
    Verbs implementation for list of instruments GET, POST and  DELETE
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)

    def get(self, request, format=None):
        """
        Show information of all instruments
        :param request djangorestframework request object
        :param format
        """
        instruments = Instrument.objects.all()
        serializer = InstrumentSerializer(instruments, many=True)
        respuesta={}
        respuesta['instruments']=serializer.data
        return Response(respuesta)

    def post(self, request, format=None):
        """
        Add a new instrument
        :param request djangorestframework request object
        :param format
        """
        serializer = InstrumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete (self, request, format=None ):
        """
        DELETE method for all the instruments
        :param request: djangorestframework request object
        :param format: additional args
        """
        instruments = Instrument.objects.all()
        for instrument in instruments:
            instrument.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)



class InstrumentDetailViewSet (viewsets.ModelViewSet):
    """
    Verbs implementation for a specific instrument, GET, PUT, DELETE
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)
    serializer_class = InstrumentSerializer

    def obtain(self, request, *args, **kwargs):
        """
        GET method for only one Instrument
        :param request: djangorestframework request object
        :param args: additional args
        :param kwargs: additional dict obtained from url path
        """
        instrument = get_instrument(kwargs['instrumentId'])[0]
        instrument_serialized = InstrumentSerializer(instrument)
        return Response(instrument_serialized.data, status=status.HTTP_200_OK)

    def modify (self, request, *args, **kwargs):
        """
        PUT (and PATCH) method for only one Instrument
        :param request: djangorestframework request object
        :param args: additional args
        :param kwargs: additional dict obtained from url path
        """
        instrument = get_instrument(kwargs['instrumentId'])[0]
        serializer = InstrumentSerializer(instrument, data=request.data, partial=True)
        if serializer.is_valid():

            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def remove (self, request, *args, **kwargs):
        """
        DELETE method for only one Instrument
        :param request: djangorestframework request object
        :param args: additional args
        :param kwargs: additional dict obtained from url path
        """
        instrument = get_instrument(kwargs['instrumentId'])[0]
        instrument.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



########################
## Capabilities views ##
########################

class CapabilitiesList(APIView):
    """
    Verbs implementation for list of capabilities GET, POST and  DELETE
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)

    def get(self, request,instrumentId, format=None):
        instrument = get_instrument(instrumentId)
        capabilities = Capability.objects.filter(instrument=instrument)
        serializer = CapabilitySerializer(capabilities, many=True)
        return Response({'capabilities':serializer.data})

    def post(self, request,instrumentId ,format=None):
        request.data['instrumentId']= instrumentId
        serializer = CapabilitySerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request,instrumentId ,format=None):
        """
        :param request:
        :param instrumentId:
        :param format:
        :return:
        """
        capabilities = Capability.objects.filter(instrument__instrumentId=instrumentId)
        for cap in capabilities:
            cap.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class CapabilitiesDetail(viewsets.ModelViewSet):
    """
    Verbs implementation for a specific Capability, GET, PUT, DELETE
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)
    serializer_class = CapabilitySerializer

    def get_capability(self,name):

        capabilities = Capability.objects.filter(name=name)
        if capabilities.count() == 0:
            logger.warning("The capacity {0} does not exist".format(name))
            raise Http404
        return capabilities[0]

    def get_capabilities(self, request, *args, **kwargs):
        instrumentId = kwargs['instrumentId']
        capabilities = Capability.objects.filter(instrument__instrumentId = instrumentId,name = kwargs['capability'])
        if capabilities.count() == 0:
            logger.warning("The capability {0} does not exist".format(kwargs['capability']))
            _state = status.HTTP_404_NOT_FOUND
            data = {}
        else:
            _state = status.HTTP_200_OK
            serializer = CapabilitySerializer(capabilities[0])
            data = serializer.data
        return Response(data,  status=_state)


    def put_capabilities (self, request, *args, **kwargs):
        capability_name = kwargs['capability']
        capability = self.get_capability(capability_name)
        serializer = CapabilitySerializer(capability, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete_capability(self, request, *args, **kwargs):
        capability_name = kwargs['capability']
        capability = self.get_capability(capability_name)
        capability.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


###########################
## Characteristics views ##
###########################

class CharacteristicsList(APIView):
    """
    Verbs implementation for list of characteristics GET, POST and  DELETE
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)

    def get(self, request,instrumentId, format=None):

        instrument = get_instrument(instrumentId)
        characteristics = Characteristics.objects.filter(instrument = instrument)
        serializer = CharacteristicSerializer(characteristics, many=True)
        return Response({'characteristics':serializer.data})

    def post(self, request,instrumentId ,format=None):
        request.data['instrumentId']= instrumentId
        serializer = CharacteristicSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request,instrumentId ,format=None):

        characteristics = Characteristics.objects.filter(instrument__instrumentId=instrumentId)
        for ch in characteristics:
            ch.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class CharacteristicsDetail(viewsets.ModelViewSet):
    """
    Verbs implementation for a specific characteristic, GET, PUT, DELETE
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)
    serializer_class = CharacteristicSerializer

    def get_characteristic(self,name):
        characteristics = Characteristics.objects.filter(name=name)
        if characteristics.count() == 0:
            logger.warning("The characteristic {0} does not exist".format(name))
            raise Http404
        return characteristics[0]

    def get_characteristics(self, request, *args, **kwargs):
        instrumentId = kwargs['instrumentId']


        characteristics = Characteristics.objects.filter(instrument__instrumentId = instrumentId,
                                                         name = kwargs['characteristic'])
        if characteristics.count() == 0:
            _state = status.HTTP_404_NOT_FOUND
            data = {}
        else:
            _state = status.HTTP_200_OK
            serializer = CharacteristicSerializer(characteristics[0])
            data = serializer.data
        return Response(data, status=_state)

    def put_characteristics (self, request, *args, **kwargs):
        characteristic_name = kwargs['characteristic']
        characteristic = self.get_characteristic(characteristic_name)
        serializer = CharacteristicSerializer(characteristic, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete_characteristics(self, request, *args, **kwargs):
        characteristic_name = kwargs['characteristic']
        characteristic = self.get_characteristic(characteristic_name)
        characteristic.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


##################
## Tasks views  ##
##################

class TasksViewList(APIView):
    """
    Verbs implementation for list of tasks GET, POST and  DELETE
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)
    def get(self, request,instrumentId, format=None):

        instrument = get_instrument(instrumentId)
        tasks = Task.objects.filter(instrument=instrument)
        serializer = TaskSerializer(tasks, many=True)
        return Response({'tasks':serializer.data})

    def post(self, request,instrumentId ,format=None):
        request.data['instrumentId']= instrumentId
        serializer = TaskSerializer(data=request.data)
        serializer.instrumentId = instrumentId
        if serializer.is_valid():
            try:
                serializer.save()
                message = serializer.data
                _state = status.HTTP_201_CREATED
            except DatabaseError as err:
                _state = status.HTTP_500_INTERNAL_SERVER_ERROR
                message = {'error':str(err)}
        else:
            message = serializer.errors
            _state = status.HTTP_400_BAD_REQUEST
        return Response(message, status=_state)

    def delete(self, request, instrumentId, format=None):

        tasks = Task.objects.filter(instrument__instrumentId=instrumentId)
        for tk in tasks:
            tk.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskViewDetail(viewsets.ModelViewSet):
    """
    Verbs implementation for a specific task, GET, PUT, DELETE
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)
    serializer_class = TaskSerializer

    def get_task(self, request, *args, **kwargs):
        instrumentId = kwargs['instrumentId']
        tasks = Task.objects.filter(instrument__instrumentId=instrumentId, taskId=kwargs['taskId'])
        if len(tasks) == 0:
            _state = status.HTTP_404_NOT_FOUND
            data = {}
        else:
            _state = status.HTTP_200_OK
            serializer = TaskSerializer(tasks[0])
            data = serializer.data
        return Response(data, status=_state)

    def put_task (self, request, *args, **kwargs):
        task = get_task(kwargs['taskId'],kwargs['instrumentId'])
        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete_task(self, request, *args, **kwargs):
        taskId = kwargs['taskId']
        task = get_task(kwargs['taskId'],kwargs['instrumentId'])
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


##########################
## Commands tasks views ##
##########################

class CommandViewList(APIView):
    """
    Verbs implementation for list of commands GET, POST and  DELETE
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)

    def get(self, request, instrumentId, taskId, format=None):
        commands = Command.objects.filter(task__taskId=taskId,task__instrument__instrumentId=instrumentId)
        serializer = CommandSerializer(commands, many=True)
        return Response({'commands':serializer.data})

    def post(self, request, instrumentId, taskId, format=None):
        request.data['taskId']= taskId
        serializer = CommandSerializer(data=request.data)
        serializer.instrumentId = instrumentId

        serializer.taskId = taskId
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, instrumentId, taskId, format=None):

        commands = Command.objects.filter(task__taskId=taskId,task__instrument__instrumentId=instrumentId)
        for cm in commands:
            cm.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class CommandViewDetail(viewsets.ModelViewSet):
    """
    Verbs implementation for a specific command, GET, PUT, DELETE
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)

    serializer_class = CommandSerializer

    def get_object_command(self,instrumentId, taskId, commandId):
        command = Command.objects.filter(
            task__taskId=taskId, task__instrument__instrumentId=instrumentId,commandId = commandId)
        if len(command)== 0:
            raise Http404
        return command[0]

    def get_command(self, request, *args, **kwargs):
        serializer = CommandSerializer(
            self.get_object_command(kwargs['instrumentId'],kwargs['taskId'],kwargs['commandId']))
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put_command (self, request, *args, **kwargs):
        command = self.get_object_command(kwargs['instrumentId'],kwargs['taskId'],kwargs['commandId'])

        serializer = CommandSerializer(command, data=request.data, partial=True)
        if serializer.is_valid():

            serializer.save()

            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete_command(self, request, *args, **kwargs):
        command = self.get_object_command(kwargs['instrumentId'],kwargs['taskId'],kwargs['commandId'])
        command.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



####################
## Config views ####
####################

class ConfigViewDetail(viewsets.ModelViewSet):
    """
    Allows to GET and PUT  some fields of CONFIG
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)
    queryset = Config.objects.all()
    serializer_class = ConfigSerializer

    def list_config(self, request, *args, **kwargs):
        config_task = Config.objects.all()[0]
        return Response(ConfigSerializer(config_task).data)

    def update_config (self, request, *args, **kwargs):
        config_task = Config.objects.all()[0]
        serializer = ConfigSerializer(config_task,data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConfigInstrumentViewDetail(viewsets.ModelViewSet):
    """
    Allows to GET and PUT  some fields of CONFIG
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)
    queryset = Config.objects.all()
    serializer_class = ConfigInstrumentSerializer

    def list_config(self, request, *args, **kwargs):
        config_task = Config.objects.all()[0]
        return Response(ConfigInstrumentSerializer(config_task).data)

    def update_config_instrument (self, request, *args, **kwargs):
        config_task = Config.objects.all()[0]
        serializer = ConfigInstrumentSerializer(config_task,data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConfigInstrumentBackendsViewDetail(viewsets.ModelViewSet):
    """
    Allows to GET the backends installed
    """
    serializer_class = ConfigTaskSerializer
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)
    def list (self, request, *args, **kwargs):
        if not settings.DEACTIVATE_CHECK_BACKENDS:
            try:
                messg = util.get_debug_info(False)
                matcher = re.finditer(r'\s+(.+):\s+Version:\s?([\S]+)',messg)
                state = status.HTTP_200_OK
                data = {'backends':[{"version":m.group(2),"backendId":m.group(1)} for m in matcher]}
            except Exception:
                data = {'detail':'Operation not available'}
                state = status.HTTP_500_INTERNAL_SERVER_ERROR
        else:
            data = {'detail':'Operation not available'}
            state = status.HTTP_500_INTERNAL_SERVER_ERROR

        return Response(data, status=state)


class ConfigTaskViewDetail(viewsets.ModelViewSet):
    """
    Allows to GET, PUT some common information about tasks.
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)
    queryset = Config.objects.all()
    serializer_class = ConfigTaskSerializer

    def list_config(self, request, *args, **kwargs):
        config_task = Config.objects.all()[0]
        return Response(ConfigTaskSerializer(config_task).data)


    def update_config_task (self, request, *args, **kwargs):
        config_task = Config.objects.all()[0]
        serializer = ConfigTaskSerializer(config_task,data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConfigInstrumentDiscoverViewDetail(viewsets.ModelViewSet):
    """
    Allow to GET the instruments connected to the server.
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)
    serializer_class = ListResourcesSerializer
    queryset = Config.objects.all()
    def list(self, request, *args, **kwargs):
        backend = self.request.query_params.get('backend', None)
        state = status.HTTP_200_OK
        message = None
        return_list = []
        if backend is None or backend =='':
            backend = self.queryset[0].defaultBackend
        try:
            return_list = manager.get_resources(backend)
            if len(return_list) == 0:
                state = status.HTTP_404_NOT_FOUND
                message = 'There is no detected devices'
        except OSError as error:
            state = status.HTTP_500_INTERNAL_SERVER_ERROR
            message = str(error)
        result =  {'instruments':return_list} if state == status.HTTP_200_OK else message

        return  Response(result, status=state)

