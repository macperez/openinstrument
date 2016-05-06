__author__ = 'macastro'

import logging

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from remoteinstrapp.models import Instrument
from remoteinstrapp.utils import convert_tools as ct
from remoteinstrapp import exceptions

# Check of installation of PyVisa
try:
    import visa
    import pyvisa.constants as v_cons
except ImportError:
    errmsg = 'ERROR: PyVisa is not installed '
    raise ImportError(errmsg)

# Get an instance of a logger
logger = logging.getLogger(__name__)

#################################
# Support functions and classes #
#################################

def get_resources(backend):
    """
    Load its backend and returns a list of all the devices connected to the computer.
    :param backend: the pyvisa backend used
    :return: the list of instruments connected to the computer
    """
    rm = visa.ResourceManager(backend)
    results = rm.list_resources('?*')
    rm.close()
    return list(results)


class Response(object):
    """
    Wrapper of the PyVisa response to the views
    """
    def __init__(self):
        self.status = None
        self.response_data = {}
        self.error = ''


############################################
# Main manager: SuperClass of the managers #
############################################

class RemoteInstAppManager(object):
    """
    This class is manager of all responsibilities of connecting with PyVisa and do all the PyVisa operations
    It contains the common operations before talks with the instruments installed and delegates the responsability in
    execute_command method.
    """
    #TODO: Include more refactor in this class removing code from 'execute_command' methods
    def __init__(self, instrumentId):
        '''
        Constructor of the class, used to load the necessary common steps.
        :param instrumentId: the instrumentId used to recover the instrument
        '''
        self.instrument = None
        self.response = Response()
        self.resource_name = None
        self.resource = None
        self.__load_instrument(instrumentId)
        self.__load_visa_backend()
        self.__open_resource()
        self.__load_parameters()

        # timeout by default (for security reasons such as avoid blocking)
        self.resource.timeout = 30000  # 30 segundos

    def __load_instrument(self, instrumentId):
        """
        Attempt to loading Instrument from databse
        :param instrumentId: the instrumentId (user id)

        """
        logger.debug('Loading instrument "{0}" from database...'.format(instrumentId))
        instruments = Instrument.objects.filter(instrumentId=instrumentId)
        if len(instruments) == 0:
            raise ObjectDoesNotExist
        self.instrument = instruments[0]
        logger.debug('OK')

    def __load_visa_backend(self):
        """
        Attempt to opening the Pyvisa backend
        """
        logger.debug('Trying to open "{0}" backend...'.format(self.instrument.backend))
        try:
            self.resource_name = visa.ResourceManager(self.instrument.backend)
            logger.debug('OK')
        except OSError as error:
            raise exceptions.NoBackendError(error)
        except ValueError as error:
            raise error
        except Exception as error:
            raise error

    def __open_resource(self):
        """
        Attempt to opening the Pyvisa resource
        """
        try:
            logger.debug('Trying to open resource "{0}" ...'.format(self.instrument.visaId))
            self.resource = self.resource_name.open_resource(self.instrument.visaId)
            logger.debug('OK')
        except OSError as error:
            raise exceptions.OpenInstrumentError(error)
        except Exception as error:
            raise error

    def __load_parameters(self):
        """
        Load the parameters from database. PyVisa_string_Parameters and PyVisa_numeric_ Parameters
        """
        logger.debug('Trying to load the parameters ...')
        for numeric_param in self.instrument.pyvisaParameters_numeric.all():
            if numeric_param.state == int (numeric_param.state):
                setattr(self.resource, numeric_param.name,int(numeric_param.state))
            else:
                setattr(self.resource, numeric_param.name,numeric_param.state)
            if getattr(self.resource, numeric_param.name) != numeric_param.state:
                raise AttributeError ('A numeric parameter has not been able to be set')
        for string_param in self.instrument.pyvisaParameters_string.all():
            val = getattr(v_cons, string_param.state) if string_param.isConstant else string_param.state
            setattr(self.resource, string_param.name, val)
            if getattr(self.resource, string_param.name) != val:
                raise AttributeError('A string parameter has not been able to be set')
        logger.debug('OK')


    def setVisaAttributesFromTask(self,command):
        """
        This method is executed for external clients of the class. It allows to load and set
        PyVisa attributes that have been configured in database thorough the web service.
        :param command: Command object (models) recovered from database that contains the information
        necessary to perform the method.
        """
        logger.debug('Trying to load the attributes from database ...')
        for numeric_param in command.visaAttributes_numeric.all():
            if numeric_param.state == int (numeric_param.state):
                setattr(self.resource, numeric_param.name,int(numeric_param.state))
            else:
                setattr(self.resource, numeric_param.name,numeric_param.state)
            if getattr(self.resource, numeric_param.name) != numeric_param.state:
                raise AttributeError ('A numeric Visa attribute has not been able to be set')

        for string_param in command.visaAttributes_string.all():
            val = getattr(v_cons, string_param.state) if string_param.isConstant else string_param.state
            setattr(self.resource, string_param.name, val)
            if getattr(self.resource, string_param.name) != val:
                raise AttributeError('A string Visa attribute  has not been able to be set')

        logger.debug('OK')


    def setting_visa_attributes(self,data):
        """
        This method is executed for the subclasses when executed command is called directly.
        :param data: json information getted from the django request
        """
        try:
            visaAttributes = data.pop('visaAttributes',{})
            for x in visaAttributes:
                val = getattr(v_cons, x['state']) if x['isConstant'] and x['state'] in dir(v_cons) else x['state']
                setattr(self.resource, x['name'], val)
                if getattr(self.resource, x['name']) != val:
                    raise AttributeError('A visa attribute has not been able to be set')
        except TypeError as error:
            raise error
        except Exception as error:
            raise error

    def close(self):
        """
        Attempt to close the resource and the resourcename, All at once.
        """
        try:
            self.resource.close()
            self.resource_name.close()
        except Exception as exc:
            raise exc

    def execute_command(self, data):
        """
        This is the method which it has to be implemented in the Child classes.
        """
        pass


#########################
### Specific managers ###
#########################

class WriteRawCommandManager(RemoteInstAppManager):
    """
    Write_raw command implementation. Used for ascii type instruments.
    """
    def execute_command(self, data):
        logger.info("executing write_raw to {0}".format(self.instrument.instrumentId))

        #setting visa att
        self.setting_visa_attributes(data) # could raise an AttributeError

        # Recover message and lock (if exists)
        message = ""
        lock = ""
        if 'message' in data:
            message = data['message']
        if 'lock' in data:
            lock = data['lock']

        # blocks the instrument
        try:
            if lock == "lock":
                self.resource.lock()
            elif lock == "lock_context":
                self.resource.lock_context()
            elif lock == "lock_excl":
                self.resource.lock_excl()
        except:
            self.response.response_data['result'] = ""
            self.response.response_data['state'] = "lockError"
            self.response.status = status.HTTP_200_OK
            self.close()
            return self.response


        # Do the query
        try:
            message = ct.to_byte(message)
            response = self.resource.write_raw(message)
            logger.info(response)
        except:
            self.response.response_data['result'] = ""
            self.response.response_data['state'] = "writeError"
            self.response.status = status.HTTP_200_OK
            self.close()
            return self.response

        finally:
            # Unlock the instrument
            try:
                if lock == "lock" or lock == "lock_context" or lock == "lock_excl":
                    self.resource.unlock()
            except:
                self.response.response_data['result'] = response
                self.response.response_data['state'] = "unlockError"
                self.response.status = status.HTTP_200_OK
                return self.response

        self.response.response_data['state'] = "success"
        self.response.response_data['result'] = response
        self.response.status = status.HTTP_200_OK

        self.close()
        return self.response


class QueryInstrumentManager(RemoteInstAppManager):
    """
    Query command implementation. Used for ascii type instruments.
    """
    def execute_command(self, data):

        logger.info("executing query to {0}".format(self.instrument.instrumentId))
        #setting visa att
        self.setting_visa_attributes(data) # could raise an AttributeError

        # Getting the message and lock (if exists)
        message = ""
        delay = 0
        lock = ""
        if 'message' in data:
            message = data['message']
        if 'delay' in data:
            delay = data['delay']
        if 'lock' in data:
            lock = data['lock']

        # blocks the instrument
        try:
            if lock == "lock":
                self.resource.lock()
            elif lock == "lock_context":
                self.resource.lock_context()
            elif lock == "lock_excl":
                self.resource.lock_excl()
        except:
            self.response.response_data['result'] = ""
            self.response.response_data['state'] = "lockError"
            self.response.status = status.HTTP_200_OK
            self.close()
            return self.response


        # It does the query
        try:
            response = self.resource.query(message, delay=delay)
            logger.info(response)
        except:
            self.response.response_data['result'] = ""
            self.response.response_data['state'] = "queryError"
            self.response.status = status.HTTP_200_OK
            self.close()
            return self.response


        # Unlock the instrument
        try:
            if lock == "lock" or lock == "lock_context" or lock == "lock_excl":
                self.resource.unlock()
        except:
            self.response.response_data['result'] = response
            self.response.response_data['state'] = "unlockError"
            self.response.status = status.HTTP_200_OK
            return self.response

        self.response.response_data['state'] = "success"
        self.response.response_data['result'] = response
        self.response.status = status.HTTP_200_OK

        self.close()
        return self.response



class QueryRawInstrumentManager(RemoteInstAppManager):
    """
    Query_raw command implementation. Used for ascii type instruments.
    """
    def execute_command(self, data):
        logger.info("executing query_raw to {0}".format(self.instrument.instrumentId))
        self.setting_visa_attributes(data) # could raise an AttributeError
        message = ""
        size = None
        lock = ""
        delay = 0
        if 'message' in data:
            message = data['message']
        if 'size' in data:
            size = data['size']
        if 'delay' in data:
            delay = data['delay']
        if 'lock' in data:
            lock = data['lock']

        try:
            if lock == "lock":
                self.resource.lock()
            elif lock == "lock_context":
                self.resource.lock_context()
            elif lock == "lock_excl":
                self.resource.lock_excl()
        except:
            self.response.response_data['result'] = ""
            self.response.response_data['state'] = "lockError"
            self.response.status = status.HTTP_200_OK
            self.close()
            return self.response

        try:
            import time
            message = ct.to_byte(message)
            logger.debug(message)
            response1 = self.resource.write_raw(message)
            logger.debug(message)
            time.sleep(delay)
            response2 = self.resource.read_raw(size=size)
            logger.debug(response2)

        except:
            self.response.response_data['result'] = ""
            self.response.response_data['state'] = "queryError"
            self.response.status = status.HTTP_200_OK
            self.close()
            return self.response

        try:
            if lock == "lock" or lock == "lock_context" or lock == "lock_excl":
                self.resource.unlock()
        except:
            self.response.response_data['result'] = ct.to_str(response2)
            self.response.response_data['state'] = "unlockError"
            self.response.status = status.HTTP_200_OK
            return self.response

        self.response.response_data['state'] = "success"
        self.response.response_data['result'] = ct.to_str(response2)
        self.close()

        return self.response



class ReadRawCommandManager(RemoteInstAppManager):
    """
    Read_raw command implementation. Used for ascii type instruments.
    """

    def execute_command(self, data):

        logger.info("executing read_raw to {0}".format(self.instrument.instrumentId))
        self.setting_visa_attributes(data) # could raise an AttributeError
        size = None
        lock = ""
        if 'size' in data:
            size = data['size']
        if 'lock' in data:
            lock = data['lock']

        try:
            if lock == "lock":
                self.resource.lock()
            elif lock == "lock_context":
                self.resource.lock_context()
            elif lock == "lock_excl":
                self.resource.lock_excl()
        except:
            self.response.response_data['result'] = ""
            self.response.response_data['state'] = "lockError"
            self.response.status = status.HTTP_200_OK
            self.close()
            return self.response


        try:
            response = self.resource.read_raw(size=size)
            logger.debug(response)
        except:
            self.response.response_data['result'] = ""
            self.response.response_data['state'] = "readError"
            self.response.status = status.HTTP_200_OK
            self.close()
            return self.response


        try:
            if lock == "lock" or lock == "lock_context" or lock == "lock_excl":
                self.resource.unlock()
        except:
            self.response.response_data['result'] = ct.to_str(response)
            self.response.response_data['state'] = "unlockError"
            self.response.status = status.HTTP_200_OK
            return self.response

        self.response.response_data['state'] = "success"
        self.response.response_data['result'] = ct.to_str(response)
        self.response.status = status.HTTP_200_OK

        self.close()
        return self.response


class ReadCommandManager(RemoteInstAppManager):
    """
    Read command implementation. Used for ascii type instruments.
    """
    def execute_command(self, data):
        logger.info("executing read to {0}".format(self.instrument.instrumentId))
        #setting visa att
        self.setting_visa_attributes(data) # could raise an AttributeError
        termination = None
        encoding = None
        lock = ""
        if 'termination' in data:
            termination = data['termination']
        if 'encoding' in data:
            encoding = data['encoding']
        if 'lock' in data:
            lock = data['lock']

        try:
            if lock == "lock":
                self.resource.lock()
            elif lock == "lock_context":
                self.resource.lock_context()
            elif lock == "lock_excl":
                self.resource.lock_excl()
        except:
            self.response.response_data['result'] = ""
            self.response.response_data['state'] = "lockError"
            self.response.status = status.HTTP_200_OK
            self.close()
            return self.response

        try:
            response = self.resource.read(termination=termination, encoding=encoding)
            logger.debug(response)
        except:
            self.response.response_data['result'] = ""
            self.response.response_data['state'] = "readError"
            self.response.status = status.HTTP_200_OK
            self.close()
            return self.response

        try:
            if lock == "lock" or lock == "lock_context" or lock == "lock_excl":
                self.resource.unlock()
        except:
            self.response.response_data['result'] = response
            self.response.response_data['state'] = "unlockError"
            self.response.status = status.HTTP_200_OK
            return self.response

        self.response.response_data['state'] = "success"
        self.response.response_data['result'] = response
        self.response.status = status.HTTP_200_OK

        self.close()
        return self.response

class WriteCommandManager(RemoteInstAppManager):
    """
    Write command implementation. Used for ascii type instruments.
    """
    def execute_command(self, data):
        logger.info("executing write to {0}".format(self.instrument.instrumentId))

        self.setting_visa_attributes(data)
        message = ""
        termination = None
        encoding = None
        lock = ""
        if 'message' in data:
            message = data['message']
        if 'termination' in data:
            termination = data['termination']
        if 'encoding' in data:
            encoding = data['encoding']
        if 'lock' in data:
            lock = data['lock']

        try:
            if lock == "lock":
                self.resource.lock()
            elif lock == "lock_context":
                self.resource.lock_context()
            elif lock == "lock_excl":
                self.resource.lock_excl()
        except:
            self.response.response_data['result'] = ""
            self.response.response_data['state'] = "lockError"
            self.response.status = status.HTTP_200_OK
            self.close()
            return self.response

        try:
            response = self.resource.write(message, termination=termination, encoding=encoding)
            logger.debug(response)
        except:
            self.response.response_data['result'] = ""
            self.response.response_data['state'] = "writeError"
            self.response.status = status.HTTP_200_OK
            return self.response

        try:
            if lock == "lock" or lock == "lock_context" or lock == "lock_excl":
                self.resource.unlock()
        except:
            self.response.response_data['result'] = response
            self.response.response_data['state'] = "unlockError"
            self.response.status = status.HTTP_200_OK
            self.close()
            return self.response

        self.response.response_data['state'] = "success"
        self.response.response_data['result'] = str(response)
        self.response.status = status.HTTP_200_OK

        self.close()
        return self.response


class GetVisaAttributeCommandManager(RemoteInstAppManager):
    """
    Get_visa_attribute command implementation. Used for ascii type instruments.
    """
    def execute_command(self, data):

        logger.info("executing get_visa_attribute to {0}".format(self.instrument.instrumentId))
        self.setting_visa_attributes(data) # could raise an AttributeError

        name = ""
        lock = ""
        if 'name' in data:
            name = data['name']
        if 'lock' in data:
            lock = data['lock']

        # Bloquea el instrumento segn lock
        try:
            if lock == "lock":
                self.resource.lock()
            elif lock == "lock_context":
                self.resource.lock_context()
            elif lock == "lock_excl":
                self.resource.lock_excl()
        except:
            self.response.response_data['result'] = ""
            self.response.response_data['state'] = "lockError"
            self.response.status = status.HTTP_200_OK
            self.close()
            return self.response

        # Realiza la consulta
        try:
            response = self.resource.get_visa_attribute(getattr(visa.constants, name))
            logger.debug(response)
        except AttributeError:
            self.response.response_data['result'] = ""
            self.response.response_data['state'] = "visaAttributeNotFound"
            self.response.status = status.HTTP_200_OK
            self.close()
            return self.response
        except:
            self.response.response_data['result'] = ""
            self.response.response_data['state'] = "getVisaAttributeError"
            self.response.status = status.HTTP_200_OK
            self.close()
            return self.response

        try:
            if lock == "lock" or lock == "lock_context" or lock == "lock_excl":
                self.resource.unlock()
        except:
            self.response.response_data['result'] = response
            self.response.response_data['state'] = "unlockError"
            self.response.status = status.HTTP_200_OK
            return self.response

        self.response.response_data['state'] = "success"
        self.response.response_data['result'] = str(response)
        self.response.status = status.HTTP_200_OK

        self.close()
        return self.response
