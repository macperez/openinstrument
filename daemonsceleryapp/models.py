from django.db import models


# Create your models here.


class TempData(models.Model):
    """
    Store the temporal data with the information of measurements
    @author: macastro
    """
    instrumentId = models.CharField(max_length=50)
    parameterName = models.CharField(max_length=50)
    user = models.CharField(max_length=50)
    content = models.TextField()
    queryDate = models.DateTimeField()

    def __str__(self):
        return '{0}'.format(self.instrumentId)



