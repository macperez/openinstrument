from django.db import models


# Create your models here.
# The model of the remoteInstrumentWS

class Instrument(models.Model):
    """
    It represents a simple instrument
    @author: macastro
    """
    instrumentId = models.CharField(max_length=50, unique=True)
    visaId = models.CharField(max_length=255)
    backend = models.CharField(max_length=50, default='@py')
    description = models.CharField(max_length=255, null=True, blank=True)
    interface = models.CharField(max_length=50, null=True, blank=True)
    protocol = models.CharField(max_length=50, null=True, blank=True)
    active = models.BooleanField(default=False)
    externalURI = models.CharField(max_length=1000, null=True, blank=True)
    taskInterval = models.IntegerField(default=60000,blank=True)  #milis

    def __str__(self):
        return '{0}'.format(self.instrumentId)


class PyVisaParameter_Numeric(models.Model):
    """
    It represents a simple numeric parameter. Has to be associated to a instrument
    @author: macastro
    """
    instrument = models.ForeignKey(Instrument, related_name='pyvisaParameters_numeric')
    name = models.CharField(max_length=100)
    state = models.FloatField(default=0.0)

    class Meta:
        select_on_save = True
        ordering = ['name']

    def __str__(self):
        return 'Numeric {0}:{1}'.format(self.name, self.state)


class PyVisaParameter_String(models.Model):
    """
    It represents a simple string parameter. Has to be associated to a instrument
    @author: macastro
    """
    instrument = models.ForeignKey(Instrument, related_name='pyvisaParameters_string')
    name = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    isConstant = models.BooleanField(default= False)
    class Meta:
        select_on_save = True
        ordering = ['name']

    def __str__(self):
        return 'String {0}:{1} Const'.format(self.name, self.state) if self.isConstant else 'String {0}:{1}'



class Capability(models.Model):
    """
    It represents a simple capability. Has to be associated to a instrument
    @author: dcallejo
    """
    instrument = models.ForeignKey(Instrument, related_name='capabilities')
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=100)

    def __str__(self):
        return '{0}:{1}'.format(self.name, self.value)


class Characteristics(models.Model):
    '''
    It represents a simple characteristic. Has to be associated to a instrument
    @author: dcallejo
    '''
    instrument = models.ForeignKey(Instrument, related_name='characteristics')
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=100)

    def __str__(self):
        return '{0}:{1}'.format(self.name, self.value)



class Task(models.Model):
    """
    It represents a task. Really it is a configuration for real tasks queued on celery,
    @author: dcallejo
    """
    taskId = models.CharField(max_length=50)
    description = models.CharField(max_length=255,null=True, blank=True)
    parameterName = models.CharField(max_length=50)
    user = models.CharField(max_length=255)
    retries = models.IntegerField(default=0, blank=True)
    priority = models.IntegerField(default=0, blank=True)
    active = models.BooleanField(default=True)
    instrument = models.ForeignKey(Instrument, related_name='tasks')

    class Meta:
        unique_together = ('taskId', 'instrument',)

    def __str__(self):
        return '{0}'.format(self.taskId)


class Command(models.Model):
    """
    It represents a command. Has to be associated to a Task.
    @author: dcallejo
    """
    task = models.ForeignKey(Task, related_name='commands')
    commandId = models.CharField(max_length=50, blank=True)
    seqNumber = models.IntegerField()
    method = models.CharField(max_length=50)
    message = models.CharField(max_length=1000, null=True, blank= True)
    delay  = models.FloatField(default=0.0, blank=True)
    termination = models.CharField(max_length=50, default='\r\n', blank=True)
    encoding = models.CharField(max_length=50, default='ascii', blank= True)
    size = models.IntegerField(default=20480, blank=True)
    name = models.CharField(max_length=50, null=True, blank= True)
    lock = models.CharField(max_length=50, blank= True)
    class Meta:
        unique_together = ('seqNumber', 'task',)


    def __str__(self):
        return '{0}'.format(self.commandId)


class VisaAttributes_String(models.Model):
    """
    It represents a VISA Attribute of String. Has to be associated to a Command.
    @author: dcallejo
    """
    command = models.ForeignKey(Command, related_name='visaAttributes_string')
    name = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    isConstant = models.BooleanField(default=False)

    def __str__(self):
        return 'String {0}:{1} Const'.format(self.name, self.state) if self.isConstant else 'String {0}:{1}'


class VisaAtributes_Numeric(models.Model):
    """
    It represents a VISA Attribute of Numeric. Has to be associated to a Command.
    @author: dcallejo
    """
    command = models.ForeignKey(Command, related_name='visaAttributes_numeric')
    name = models.CharField(max_length=100)
    state = models.FloatField(default=0.0)

    class Meta:
        select_on_save = True
        ordering = ['name']

    def __str__(self):
        return 'Numeric {0}:{1}'.format(self.name, self.state)



class Config(models.Model):
    """
    It represents the general configuration for relevant information about web services and its behaviour
    within PyVisa functionality
    @author: dcallejo
    """
    countryId = models.CharField(max_length=50)
    appId = models.CharField(max_length=50)
    defaultBackend = models.CharField(max_length=50)
    broker = models.CharField(max_length=50)
    backend = models.CharField(max_length=50)
    dataFormat = models.CharField(max_length=50)
    timezone = models.CharField(max_length=50)

    def __str__(self):
        return '{0}'.format(self.idCountry)


