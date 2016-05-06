"""
Created on 15/09/2015
Serializers module django-restful based
@author: manu
"""

import codecs
import logging
from django.http import Http404

from remoteinstrapp.models import Instrument, PyVisaParameter_Numeric, \
    PyVisaParameter_String, Config, \
    Capability, Characteristics, Task, Command, VisaAtributes_Numeric, VisaAttributes_String
from rest_framework import serializers


# Get an instance of a logger
logger = logging.getLogger(__name__)


## ###########################################
## Shared generic functions for this module ##
## ###########################################

def get_next_command_id(taskId):
    """
    Computes the next id for the command. Notice that it is different that internal database id (always numeric for us)
    :param taskId: the id given to a task.
    :return: a string containing the next id for commands within a task. It uses a internal database id for command.
    """
    last_id = 0
    if len(Command.objects.all()) > 0:
        last_id = Command.objects.latest('id').id
    last_id += 1
    return 't{0}_c{1}'.format(taskId, str(last_id))


def get_instrument(instrumentId):
    """
    Recover an instrument from BBDD.
    :param instrumentId: the user id for the Instrument
    :return: a list of Instruments. If we are looking for only one instrument we must pick only the first element [0]
    """
    inst = Instrument.objects.filter(instrumentId=instrumentId)
    if len(inst) == 0:
        logger.warning('The instrument {0} does not exist in BBDD'.format(instrumentId))
        raise Http404
    return inst


def get_task(taskId, instrumentId):
    """
    Recover a Task from BBDD.
    :param taskId: the user id for the Task
    :param instrumentId: the user id for the Instrument
    :return: a specific task
    """
    task = Task.objects.filter(taskId=taskId,instrument__instrumentId=instrumentId)
    if len(task) == 0:
        logger.warning('The task {0} does not exist for the instrument {1} in BBDD'.format(taskId,instrumentId))
        raise Http404
    return task[0]


#################
## Serializers ##
#################

class PyVisaParameterNumericSerializer(serializers.ModelSerializer):
    """
    PyVisa numeric parameters serializer. Include all the fields that it is needed to show.
    """
    class Meta:
        model = PyVisaParameter_Numeric
        fields = ('name',
                  'state',)


class PyVisaParameterStringSerializer(serializers.ModelSerializer):
    """
    PyVisa string parameters serializer. Include all the fields that it is needed to show.
    """
    class Meta:
        model = PyVisaParameter_String
        fields = ('name',
                  'state',
                  'isConstant',)

class CapabilitySerializer(serializers.ModelSerializer):
    """
    Capabilities serializer. Include all the fields that it is needed to show.
    """
    class Meta:
        model = Capability
        fields = ('name',
                  'value',)

    # It is necesary to override this method because we need to include the reference to an Instrument.
    def create(self, validated_data):
        instrument = get_instrument(self.initial_data['instrumentId'])[0]
        capability = Capability.objects.create(instrument=instrument, **validated_data)
        return capability

    # It is necesary to override this method because we need to include the reference to an Instrument.
    def update(self, instance, validated_data):
        #instance.name = validated_data.get('name', instance.name)
        instance.value = validated_data.get('value', instance.value)
        instance.save()
        return instance


class CharacteristicSerializer(serializers.ModelSerializer):
    """
    Characteristics serializer. Include all the fields that it is needed to show.
    """
    class Meta:
        model = Capability
        fields = ('name',
                  'value',)
    # It is necesary to override this method because we need to include the reference to an Instrument.
    def create(self, validated_data):
        instrument = get_instrument(self.initial_data['instrumentId'])[0]
        characteristic = Characteristics.objects.create(instrument=instrument, **validated_data)
        return characteristic

    # It is necesary to override this method because we need to include the reference to an Instrument.
    def update(self, instance, validated_data):
       # instance.name = validated_data.get('name', instance.name)
        instance.value = validated_data.get('value', instance.value)
        instance.save()
        return instance


class InstrumentSerializer(serializers.ModelSerializer):
    """
    Instruments serializer. Include all the fields that it is needed to show.
    """
    # making a reference to its nested objects, because it is possible to create or update this objects when
    # you try to create or update a given instrument
    pyvisaParameters_numeric = PyVisaParameterNumericSerializer(many=True, allow_null=True,required=False)
    pyvisaParameters_string = PyVisaParameterStringSerializer(many=True, allow_null=True, required=False)

    class Meta:
        model = Instrument
        fields = ('instrumentId',
                  'visaId',
                  'backend',
                  'description',
                  'interface',
                  'protocol',
                  'externalURI',
                  'taskInterval',
                  'pyvisaParameters_numeric',
                  'pyvisaParameters_string',
                  'active',)

    # It is necesary to override due to nested objects pyvisaParameters_string, pyvisaParameters_numeric
    def create(self, validated_data):
        parameters_string_data = validated_data.pop('pyvisaParameters_string',{})
        parameters_numeric_data = validated_data.pop('pyvisaParameters_numeric',{})


        instrument = Instrument.objects.create(**validated_data)
        for parameter_data in parameters_string_data:
            PyVisaParameter_String.objects.create(instrument=instrument, **parameter_data)

        for parameter_data in parameters_numeric_data:
            PyVisaParameter_Numeric.objects.create(instrument=instrument, **parameter_data)

        return instrument

    # It is necesary to override due to nested objects pyvisaParameters_string, pyvisaParameters_numeric
    def update(self, instance, validated_data):

        instance.visaId = validated_data.get('visaId', instance.visaId)
        instance.backend = validated_data.get('backend', instance.backend)
        instance.description = validated_data.get('description', instance.description)
        instance.interface = validated_data.get('interface', instance.interface)
        instance.protocol = validated_data.get('protocol', instance.protocol)
        instance.active = validated_data.get('active', instance.active)
        instance.externalURI = validated_data.get('externalURI', instance.externalURI)
        instance.taskInterval = validated_data.get('taskInterval', instance.taskInterval)
        instance.save()
        if 'pyvisaParameters_string' in validated_data:
            for param_data in validated_data.pop('pyvisaParameters_string'):
                params_looked = PyVisaParameter_String.objects.filter(name=param_data['name'], instrument=instance)
                if len(params_looked) == 1:
                    param = params_looked[0]
                    param.state = param_data['state']
                    param.isCconstant = param_data['isConstant']
                else:
                    param = PyVisaParameter_String(name=param_data['name'],
                                                   state=param_data['state'],
                                                   isConstant=param_data['isConstant'], instrument=instance)
                param.save()

        if 'pyvisaParameters_numeric' in validated_data:
            for param_data in validated_data.pop('pyvisaParameters_numeric'):
                params_looked = PyVisaParameter_Numeric.objects.filter(name=param_data['name'], instrument=instance)
                param = None
                if len(params_looked) == 1:
                    param = params_looked[0]
                    param.state = param_data['state']
                else:
                    param = PyVisaParameter_Numeric(name=param_data['name'],
                                                    state=param_data['state'], instrument=instance)
                param.save()

        return instance



class DirectCommandSerializer(serializers.Serializer):
    """
    Used for json serializing purposes
    """
    pass




class ConfigSerializer(serializers.ModelSerializer):
    """
    ConfigTask serializer. Include the field:
    'countryId',
    'appId',
    of Config
    """
    class Meta:
        model = Config
        fields = ('countryId',
                  'appId',)


class ConfigInstrumentSerializer(serializers.ModelSerializer):
    """
    ConfigTask serializer. Include the field:
    'defaultBackend',
    of Config
    """
    class Meta:
        model = Config
        fields = ('defaultBackend',)


class ConfigTaskSerializer(serializers.ModelSerializer):
    """
    ConfigTask serializer. Include the fields:
    'broker',
    'backend',
    'dataFormat',
    'timezone'
    of Config
    """
    class Meta:
        model = Config
        fields = ('broker',
                  'backend',
                  'dataFormat',
                  'timezone')


class VisaAttributes_NumericSerializer(serializers.ModelSerializer):
    """
    VisaAttributes serializer whose fields are name and state
    """
    class Meta:
        model = VisaAtributes_Numeric
        fields = ('name',
                  'state',)


class VisaAttributes_StringSerializer(serializers.ModelSerializer):
    """
    VisaAttributes serializer whose fields are name, state and constant
    """
    class Meta:
        model = VisaAttributes_String
        fields = ('name',
                  'state',
                  'isConstant',)


class CommandSerializer(serializers.ModelSerializer):
    """
    CommandSerializer whose fields are name, 'commandId',
                  'seqNumber',
                  'method',
                  'message',
                  'delay',
                  'termination',
                  'encoding',
                  'size',
                  'name',
                  'lock',
                  'visaAttributes_string',
                  'visaAttributes_numeric'
    """
    visaAttributes_numeric = VisaAttributes_NumericSerializer(many=True, allow_null=True, required=False)
    visaAttributes_string = VisaAttributes_StringSerializer(many=True, allow_null=True, required=False)
    instrumentId = ''
    taskId = ''
    termination = ''
    class Meta:
        model = Command
        fields = ('commandId',
                  'seqNumber',
                  'method',
                  'message',
                  'delay',
                  'termination',
                  'encoding',
                  'size',
                  'name',
                  'lock',
                  'visaAttributes_string',
                  'visaAttributes_numeric'
                  )

    # It is necesary to override this method because we need to use the numeric and String Visa attibutes
    def create(self, validated_data):
        numeric_attr_data = validated_data.pop('visaAttributes_numeric', {})
        string_attr_data = validated_data.pop('visaAttributes_string', {})
        taskId = self.initial_data['taskId']
        task = get_task(taskId,self.instrumentId) # you must need to recoger the task
        commandId = get_next_command_id(taskId) # the commandId it is calculated

        validated_data.pop('commandId',{})
        if 'termination' in validated_data:
            validated_data['termination'] = codecs.decode(validated_data['termination'],'unicode_escape')

        command = Command.objects.create(commandId=commandId,
                                         task=task,
                                         **validated_data)
        for numeric_attr in numeric_attr_data:
            VisaAtributes_Numeric.objects.create(command=command, **numeric_attr)
        for string_attr in string_attr_data:
            VisaAttributes_String.objects.create(command=command, **string_attr)

        return command

    # It is necesary to override this method because we need to use the numeric and String Visa attibutes
    def update(self, instance, validated_data, *args):
        instance.seqNumber = validated_data.get('seqNumber', instance.seqNumber)
        instance.method = validated_data.get('method', instance.method)
        instance.message = validated_data.get('message', instance.message)
        # be careful with end termination, here we use codecs library in order to process escape characters
        # such as \\n or \\r but after that the system need to save \r or \n only because
        # it must be treated as only char.
        instance.termination =codecs.decode(validated_data.get('termination', self.termination),'unicode_escape')
        instance.encoding = validated_data.get('encoding', instance.encoding)
        instance.size = validated_data.get('size', instance.size)
        instance.delay = validated_data.get('delay', instance.delay)
        instance.name = validated_data.get('name', instance.name)
        instance.lock = validated_data.get('lock', instance.lock)
        instance.save()

        # updating parameters
        visa_attr_string_data = validated_data.pop('visaAttributes_string', {})
        for v_a_s_data in visa_attr_string_data:
            visaAttribute_string_looked = VisaAttributes_String.objects.filter(name=v_a_s_data['name'],
                                                                               command=instance)
            if len(visaAttribute_string_looked) == 1:
                visaAttribute_string = visaAttribute_string_looked[0]
                visaAttribute_string.state = v_a_s_data['state']
                visaAttribute_string.isConstant = v_a_s_data['isConstant']
            else:
                visaAttribute_string = VisaAttributes_String(
                    name=v_a_s_data['name'], state=v_a_s_data['state'],
                    isConstant=v_a_s_data['isConstant'], command=instance
                )
            visaAttribute_string.save()
        visa_attr_numeric_data = validated_data.pop('visaAttributes_numeric', {})
        for v_a_n_data in visa_attr_numeric_data:
            visaAttribute_numeric_looked = VisaAtributes_Numeric.objects.filter(name=v_a_n_data['name'],
                                                                                command=instance)
            if len(visaAttribute_numeric_looked) == 1:
                visaAttribute_numeric = visaAttribute_numeric_looked[0]
                visaAttribute_numeric.state = v_a_n_data['state']
            else:
                visaAttribute_numeric = VisaAtributes_Numeric(
                    name=v_a_n_data['name'], state=v_a_n_data['state'],
                    command=instance
                )
            visaAttribute_numeric.save()

        return instance

    def validate(self, data):
        """
        Check the set [seqNumber,task,instrument] are unique
        """
        if 'seqNumber' in data and Command.objects.filter(task__taskId=self.taskId,
                                          task__instrument__instrumentId=self.instrumentId,
                                          seqNumber=data['seqNumber']).exists():
            raise serializers.ValidationError("The sequenceId must unique within task and instrument")

        return data



class TaskSerializer(serializers.ModelSerializer):
    """
    TaskSerializer whose fields are 'taskId',
                  'description',
                  'parameterName',
                  'user',
                  'retries',
                  'priority',
                  'active',
                  'commands'

    """
    commands = CommandSerializer(many=True, allow_null=True)
    instrumentId = ''
    class Meta:
        model = Task
        fields = ('taskId',
                  'description',
                  'parameterName',
                  'user',
                  'retries',
                  'priority',
                  'active',
                  'commands'
                  )

    # It is necesary to override this method because we need to use commmand creation
    def create(self, validated_data):

        commands_data = validated_data.pop('commands',{})
        instrument = get_instrument(self.initial_data['instrumentId'])[0]
        task = Task.objects.create(instrument=instrument, **validated_data)

        for command_data in commands_data:
            commandId = get_next_command_id(task.taskId)
            if 'termination' in command_data:
               command_data['termination']=  \
                   codecs.decode(command_data.get('termination'),'unicode_escape')
            numeric_attr_data = {}
            string_attr_data = {}
            if 'visaAttributes_numeric' in command_data:
                numeric_attr_data = command_data.pop("visaAttributes_numeric")

            if 'visaAttributes_string' in command_data:
                string_attr_data = command_data.pop('visaAttributes_string')

            command_data.pop('commandId',{})
            command = Command.objects.create(commandId=commandId, task=task, **command_data)

            for numeric_attr in numeric_attr_data:
                VisaAtributes_Numeric.objects.create(command=command, **numeric_attr)
            for string_attr in string_attr_data:
                VisaAttributes_String.objects.create(command=command, **string_attr)

        return task

    # This method it is prepared for commands updating but it is not implemented at the moment
    def update(self, instance, validated_data):
        instance.description = validated_data.get('description', instance.description)
        instance.parameterName = validated_data.get('parameterName', instance.parameterName)
        instance.user = validated_data.get('user', instance.user)
        instance.retries = validated_data.get('retries', instance.retries)
        instance.priority = validated_data.get('priority', instance.priority)
        instance.active = validated_data.get('active', instance.active)
        instance.save()
        #commands_data = validated_data.pop('commands', {})
        # for c_data in commands_data:
        #     commands_looked = Command.objects.filter(commandId=c_data['commandId'], task=instance)
        #     if len(commands_looked) == 1:
        #         command = commands_looked[0]
        #         command.seqNumber = c_data['seqNumber']
        #         command.method = c_data['method']
        #         command.message = c_data['message']
        #         command.termination = c_data['termination']
        #         command.encoding = c_data['encoding']
        #         command.size = c_data['size']
        #         command.name = c_data['name']
        #         command.lock = c_data['lock']
        #
        #     else:  # aqui presuponemos que la consulta devuelve o uno o cero resultados
        #         command = Command(
        #             commandId=self.get_next_id(instance.taskId), seqNumber=c_data['seqNumber'],
        #             method=c_data['method'],
        #             message=c_data['message'], termination=c_data['termination'],
        #             encoding=c_data['encoding'], size=c_data['size'],
        #             name=c_data['name'], lock=c_data['lock'],
        #             task=instance
        #         )
        #     command.save()
        #     visa_attr_string_data = c_data.pop('visaAttributes_string', {})
        #     for v_a_s_data in visa_attr_string_data:
        #         visaAttribute_string_looked = VisaAttributes_String.objects.filter(name=v_a_s_data['name'],
        #                                                                            command=command)
        #         if len(visaAttribute_string_looked) == 1:
        #             visaAttribute_string = visaAttribute_string_looked[0]
        #             visaAttribute_string.state = v_a_s_data['state']
        #             visaAttribute_string.isConstant = v_a_s_data['isConstant']
        #         else:
        #             visaAttribute_string = VisaAttributes_String(
        #                 name=v_a_s_data['name'], state=v_a_s_data['state'],
        #                 isConstant=v_a_s_data['isConstant'], command=command
        #             )
        #         visaAttribute_string.save()
        #
        #     visa_attr_numeric_data = c_data.pop('visaAttributes_numeric', {})
        #     for v_a_n_data in visa_attr_numeric_data:
        #         visaAttribute_numeric_looked = VisaAtributes_Numeric.objects.filter(name=v_a_n_data['name'],
        #                                                                             command=command)
        #         if len(visaAttribute_numeric_looked) == 1:
        #             visaAttribute_numeric = visaAttribute_numeric_looked[0]
        #             visaAttribute_numeric.state = v_a_n_data['state']
        #         else:
        #             visaAttribute_numeric = VisaAtributes_Numeric(
        #                 name=v_a_n_data['name'], state=v_a_n_data['state'],
        #                 command=command
        #             )
        #         visaAttribute_numeric.save()

        return instance

    def validate(self, data):
        """
        Check the set [task,instrument] are unique
        """
        if 'taskId' in data and Task.objects.filter(taskId=data['taskId'],
                                          instrument__instrumentId=self.instrumentId).exists():
            raise serializers.ValidationError("The taskId must unique within an instrument")

        return data


class ListResourcesSerializer(serializers.Serializer):
    """
    ListResourceSerializer for list resources url
    """
    list_resources = serializers.CharField(read_only=True)
