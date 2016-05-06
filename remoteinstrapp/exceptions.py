__author__ = 'macastro'


#OSError(EnvironmentError): Come from this kind of error
class OpenInstrumentError(OSError):

    def __init__(self,error):
        # Call the base class constructor with the parameters it needs
        #super(OpenInstrumentError, self).__init__(message)
        self.error = error

    def __str__(self):
        return str(self.error)

#OSError(EnvironmentError): Come from this kind of error
class NoBackendError(OSError):

    def __init__(self,error):
        # Call the base class constructor with the parameters it needs
        #super(NoBackendError, self).__init__(message)
        self.error = error

    def __str__(self):
        return str(self.error)
