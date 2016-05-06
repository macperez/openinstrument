__author__ = 'macastro'

import json
import logging

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets

from rest_framework.response import Response
from rest_framework import status as st

from remoteinstrapp.permission import SimpleAuthentication, GivingPermissions
from remoteinstrapp.models import Instrument
from remoteinstrapp.serializers import  DirectCommandSerializer
from remoteinstrapp.app_management import manager
from remoteinstrapp.exceptions import OpenInstrumentError, NoBackendError


# Get an instance of a logger
logger = logging.getLogger(__name__)

##########################
## Direct command views ##
##########################

class CommandViewSet(viewsets.ModelViewSet):
    """
    List all the available commands for the instruments
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)
    serializer_class = DirectCommandSerializer

    def obtain_command_list(self, request, *args, **kwargs):
        instrumentId = kwargs['instrumentId']
        data = request.data
        instruments = Instrument.objects.filter(instrumentId=instrumentId)
        if len(instruments)==0:
            return Response({'detail':'The instrument does not exist'}, status=st.HTTP_404_NOT_FOUND)
        # we load the instructions from a json file.
        with open('fixtures/get_instruments_commands.json') as json_data:
            d_commands = json.load(json_data)
        return Response(d_commands, status=st.HTTP_202_ACCEPTED)


def perform_method(request,instrumentId,manager_type):
    """
    This method's got the logic for choose the proper manager wrapper
    :param request: django rest framework request ....
    :param kwargs: args passed from view in order to get the parameters from url

    :param manager_type:
    :return:
    """

    result = ''
    state = ''
    rest_response = {}
    http_state = None
    try: # to call the proper instrument manager
        mng = {
                "WriteRawCommandManager":manager.WriteRawCommandManager,
                "QueryInstrumentManager":manager.QueryInstrumentManager,
                "QueryRawInstrumentManager":manager.QueryRawInstrumentManager,
                "ReadRawCommandManager":manager.ReadRawCommandManager,
                "ReadCommandManager":manager.ReadCommandManager,
                "WriteCommandManager":manager.WriteCommandManager,
                "GetVisaAttributeCommandManager":manager.GetVisaAttributeCommandManager,
               }[manager_type](instrumentId)

    except ImportError as error: # if pyvisa is not installed
        http_state = st.HTTP_500_INTERNAL_SERVER_ERROR
        state = 'pyVisaNotInstalled'
        result = str(error)
    except ObjectDoesNotExist as error:
        http_state = st.HTTP_404_NOT_FOUND
        state='instrumentNotExists'
        result = str(error)
    except ValueError as error: # raise when the user set a bad backend, not in the oficial list of backends
        http_state = st.HTTP_400_BAD_REQUEST
        state='wrongBackendConfigured'
        result = str(error)
    except NoBackendError as error: # The backend in data is not installed in the computer
        http_state = st.HTTP_500_INTERNAL_SERVER_ERROR
        state='noBackendError'
        result = str(error)
    except OpenInstrumentError as error: # The instrument in data is not connected to the computer
        http_state = st.HTTP_500_INTERNAL_SERVER_ERROR
        state='openInstrumentError'
        result = str(error)
    except OSError as error: #if the backend is not installed
        http_state = st.HTTP_500_INTERNAL_SERVER_ERROR
        state ='oserror'
        result = str(error)
    except AttributeError as error: # due to visaParameter_string or visaParameter_numeric assignement
            http_state = st.HTTP_500_INTERNAL_SERVER_ERROR
            state = 'pyVisaParametersError'
            result = str(error)
    except Exception as error: # another exception that we do not know previously
        state = 'unknownError'
        http_state = st.HTTP_500_INTERNAL_SERVER_ERROR
        result = str(error)

    #we execute the command
    if not http_state:
        data = request.data
        try:
            response = mng.execute_command(data)
            http_state = response.status
            state = response.response_data['state']
            result= response.response_data['result']


        except AttributeError as error: # due to visaAttributes_string or visaAttributes_numeric assignement
            http_state = st.HTTP_400_BAD_REQUEST
            state = 'VisaAttributesError'
            result = str(error)

    rest_response['state'] = state
    rest_response['result'] = result

    return Response(rest_response, status=http_state)


class CommandWriteRawViewSet(viewsets.ModelViewSet):
    """
    POST to execute write_raw
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)
    serializer_class = DirectCommandSerializer

    def perform_write_raw(self, request, *args, **kwargs):
        return perform_method(request,kwargs['instrumentId'],'WriteRawCommandManager')


class CommandReadRawViewSet(viewsets.ModelViewSet):
    """
    POST to execute read_raw
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)
    serializer_class = DirectCommandSerializer
    def perform_query(self, request, *args, **kwargs):
        return perform_method(request,kwargs['instrumentId'],'ReadRawCommandManager')


class CommandReadViewSet(viewsets.ModelViewSet):
    """
    POST to execute read
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)
    serializer_class = DirectCommandSerializer
    def perform_query(self, request, *args, **kwargs):
        return perform_method(request,kwargs['instrumentId'],'ReadCommandManager')



class CommandWriteViewSet(viewsets.ModelViewSet):
    """
    POST to execute write
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)
    serializer_class = DirectCommandSerializer
    def perform_query(self, request, *args, **kwargs):
        return perform_method(request,kwargs['instrumentId'],'WriteCommandManager')



class CommandQueryViewSet(viewsets.ModelViewSet):
    """
    POST to execute query
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)
    serializer_class = DirectCommandSerializer
    def perform_query(self, request, *args, **kwargs):
        return perform_method(request,kwargs['instrumentId'],'QueryInstrumentManager')



class CommandQueryRawViewSet(viewsets.ModelViewSet):
    """
    POST to execute query_raw
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)
    serializer_class = DirectCommandSerializer

    def perform_query_raw(self, request, *args, **kwargs):
        return perform_method(request,kwargs['instrumentId'],'QueryRawInstrumentManager')


class CommandGetVisaAttrViewSet(viewsets.ModelViewSet):
    """
    POST to execute get_visa_attribute
    """
    permission_classes=(GivingPermissions,)
    authentication_classes = (SimpleAuthentication,)
    serializer_class = DirectCommandSerializer

    def perform_query(self, request, *args, **kwargs):
        return perform_method(request,kwargs['instrumentId'],'GetVisaAttributeCommandManager')
