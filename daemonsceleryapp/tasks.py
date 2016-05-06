from __future__ import absolute_import

__author__ = 'macastro'

import logging
import requests
import json

from requests.auth import HTTPBasicAuth

from celery import shared_task
from django.utils import timezone
from django.conf import settings
from remoteinstrapp.models import Instrument, Config
from remoteinstrapp.serializers import CommandSerializer
from remoteinstrapp.app_management import manager
from daemonsceleryapp.models import TempData

# Get an instance of a logger
logger = logging.getLogger(__name__)

# Map for choose the correct manager
callable_manager_map = {
        'query_raw': manager.QueryRawInstrumentManager,
        'query': manager.QueryInstrumentManager,
        'write_raw': manager.WriteRawCommandManager,
        'read_raw': manager.ReadRawCommandManager,
        'read':manager.ReadCommandManager,
        'write':manager.WriteCommandManager,
        'get_visa_attribute':manager.GetVisaAttributeCommandManager

    }





###############################
## TASK 1 : Collecting data ##
###############################
@shared_task
def collect_data():
    """
    This task/method recovers all commands existing in the database and tries to execute them with PyVisa interface.
    All the commands and methods are defined in <code>remoteinstr.remoteinstrapp.app_management.manager</code>
    The algorithm consists in looping over all the comands that belongs to a specific task which
    in turn belongs to a specific instrument.
    A number of retries is also defined in a task level and it is used in case of any command fails
    inside of a task. In this case all the commands associated to a task are executed again from scratch.
    """
    logger.info("Starting collect_data task")
    logger.debug("Task id {0.id}".format(collect_data.request))
    instruments = Instrument.objects.filter(
        active=True,
        tasks__isnull=False,
        tasks__active=True
    ).distinct()  # This query executes a distinct command
    for instrument in instruments:
        # we catch all its tasks
        logger.debug("Iterating over instrument {0}".format(instrument.instrumentId))

        tasks = instrument.tasks.filter(active=True,commands__isnull=False).distinct()
        for task in tasks:
            retries = -1 # counter of retries, if we talk of tries should be 0
            commands = task.commands.all().order_by('seqNumber')
            success = False

            logger.info("Executing task {0} for the instrument {1} ".format(task.taskId, instrument.instrumentId))
            while not success and retries < task.retries:
                c = 0
                response = None
                success = commands.exists()
                if not success:
                    logger.warning("There is not any command for this task, please review your configuration")
                while c < commands.count() and success:
                    command = commands[c]
                    try:
                        logger.debug("- Executing command {0}:{1}".format(command.commandId,command.method))
                        manager = callable_manager_map[command.method](instrument.instrumentId)
                        manager.setVisaAttributesFromTask(command)
                        response=manager.execute_command(CommandSerializer(command).data)
                        logger.debug(response.response_data)

                        success = response.response_data['state'] == 'success'
                        logger.debug("- Executing command {0}:{1}".format(command.commandId,command.method))
                        if not success:
                            raise Exception("ERROR: misunderstanding in the commands sent")
                    except Exception as excep:
                        logger.error(" Error during execution over:instrument {0} --> task{1} -->in command {2}, attempt {3}"
                                     .format(instrument.instrumentId,task.taskId, command.method, retries+2))
                        logger.error(str(excep))
                        success = False

                    c+=1

                if success:  # store the last result of the command if it went well
                    logger.debug("The command execution was OK!")
                    tempData = TempData(
                        instrumentId=command.task.instrument.instrumentId,
                        parameterName=command.task.parameterName,
                        user=command.task.user,
                        content=response.response_data['result'],
                        queryDate=timezone.now()
                    )
                    tempData.save()

                retries += 1 # add a new attempt


############################
## TASK 2: Sending data   ##
############################
@shared_task
def send_data(_url='http://lifewatch.viavansi.com/lifewatch-service-rest/instrumentContent/createlist',
              USER='lifewatch_user', PASS='lifewatch_pass', limit=50):
    """
    The task tries to send all the data to a external url using requests (external lib for http requests, rest)
    The algorithm consists in recover all the data from temp data group by instrument since the external service
    needs to identify firstly the instrument and after that its content.
    It is well known that send all temporal data in one go would be a risky work,
    since a big amount of data could collapse the network traffic, and several measures could lost.
    In order to prevent it, we split the temporal data in blocks of maximum 'limit' records. Each block is sent and
    the remote server should return the ids that have been processed.
    Only the records that were not able to be sent will remain in temporal data table,
    the rest should be removed from database.

    :param _url: the external url where the data will ben sent to
    :param limit: number of records per block when we make a petition to the url. It looks like a pagination...

    """
    logger.info("Starting send_data task")
    # We get the configuration from remoteinstrapp database. Only one row ..
    config = Config.objects.all()[0]

    instruments_ids_lisf_of_map = TempData.objects.values('instrumentId').distinct()

    total_number_of_temp_data = TempData.objects.count()
    logger.info("Trying to send all the records ({0}) of TempData ".format(total_number_of_temp_data))

    if not instruments_ids_lisf_of_map.exists():
        logger.info("There is not temporal data to send, skipping the cycle")
        return

    for el in instruments_ids_lisf_of_map:
        instrumentId = el['instrumentId']
        temps_data = TempData.objects.filter(instrumentId=instrumentId)

        j = 0  # data are split into blocks of limit size as maximum
        block = 0
        proc_and_deleted = 0
        logger.debug("page limit = {0} from {1} to {2}".format(limit,j,j+limit))
        while j + limit < len(temps_data):

            block += 1
            logger.debug(">>  block {0}".format(block))
            # we convert the data into dict notation for using json later
            data_to_be_sent = convert_data_to_dict(temps_data[j:j + limit], config)
            response = None
            try:
                final_data  = json.dumps(data_to_be_sent)
                logger.debug(">>  final_data {0}".format(final_data))
                response = requests.post(_url,final_data,auth=HTTPBasicAuth(USER,PASS),
                                         headers={'Content-Type': 'application/json'})

                logger.debug(">>  response {0}".format(response))
                logger.debug(">>  content {0}".format(response.content))
            except ConnectionError as exc:
                logger.error("Error during connection with external URL for block {0} of data".format(block))
                logger.error(exc)
            except Exception as exc:
                logger.error("Error during connection with external URL for block {0} of data".format(block))
                logger.error(exc)

            if response and response.status_code == requests.codes.created:
                try:
                    # we remove all the data that have been successfully processed
                    deleted_records = delete(temps_data[j:j + limit])
                    logger.debug(
                        " Request OK for the block {0} .It has been deleted {1} records after this sending".format(
                            block, deleted_records))
                    proc_and_deleted += deleted_records
                except ValueError as exc:
                    logger.error("The format of the data returned by the external server is not expected")
                    logger.error(exc)

                except Exception as exc:
                    logger.error("The format of the data returned by the external server is not expected")
                    logger.error(exc)

            j += limit

        # the process is repeated for the last records that remain in the last block
        block +=1
        logger.debug("page limit = {0} from {1} to {2}".format(limit,j,len(temps_data)))
        data_to_be_sent = convert_data_to_dict(temps_data[j:], config)
        response = None
        try:
            final_data  = json.dumps(data_to_be_sent)
            logger.debug(">>  final_data {0}".format(final_data))
            response = requests.post(_url,json.dumps(data_to_be_sent),auth=HTTPBasicAuth(USER,PASS),
                                     headers={'Content-Type': 'application/json'})

        except ConnectionError as exc:
            logger.error("Error during connection with external URL for block {0} of data".format(block))
            logger.error(exc)

        except Exception as exc:
            logger.error("Error during connection with external URL for block {0} of data".format(block))
            logger.error(exc)

        if response and response.status_code == requests.codes.created:
            try:
                deleted_records = delete(temps_data[j:j + limit])
                logger.debug(
                        " Request OK for the block {0} .It has been deleted {1} records after this sending".format(
                            block, deleted_records))
                proc_and_deleted += deleted_records
            except ValueError as exc:
                logger.error("The format of the data returned by the external server is not expected")
                logger.error(exc)
            except Exception as exc:
                logger.error("The format of the data returned by the external server is not expected")
                logger.error(exc)

    logger.info("{0} records of temporal data were deleted from database in this execution of this task"
                .format(proc_and_deleted))

    if total_number_of_temp_data != proc_and_deleted:
        logger.warning("The amount of records deleted should be the same that the "\
                       "amount of records that were recovered from database")

    # END


def convert_data_to_dict(temp_data, config):
    """
    This method converts temp_data and config in the following structure

    {
  "instrumentContent": [
    {
      "content": "sdsjdsj",
      "parameter": "temp",
      "idApp": "01",
      "idCountry": "01",
      "instrumentName": "IntsPrueba",
      "date": "2015-01-02"
    },
    {
      "content": "aaaa",
      "parameter": "hum",
      "idApp": "01",
      "idCountry": "01",
      "instrumentName": "IntsPrueba",
      "date": "2015-01-01"
    }
  ],
  "instrumentName": "IntsPrueba"
}
    """

    list_contents = []
    for td in temp_data:
        _dict_td = {
            "content":td.content,
            "parameter":td.parameterName,
            "date":td.queryDate.strftime(settings.DATE_FORMAT_EXTERNAL_WEB_SERVICE),
            "idApp":config.appId,
            "idCountry":config.countryId,
            "instrumentName":td.instrumentId
        }
        list_contents.append(_dict_td)

    return {"instrumentContent":list_contents, "instrumentName": temp_data[0].instrumentId}


def delete(temps_data):
    """
    Delete all the data from the database whose ids do not exist in sent_rows
    :param temps_data: data to be deleted

    :return: the number of records deleted
    """
    deleted = 0
    for tempData in temps_data:
        tempData.delete()
        deleted +=1

    return deleted



############################
## TASK 3 : Cleaning data ##
############################

@shared_task
def clean_data(interval=1440):
    """
    Clean the Temporal data in TempData table. This task removes all the records that are older than a specify amount of
    minutes computed from now to the past.
    :param interval: minutes interval
    """
    logger.info("Starting clean_data task")
    deleted = 0
    filter_date_time_condition =timezone.now()-timezone.timedelta(minutes=interval)
    for temp in TempData.objects.filter(queryDate__lt=timezone.now()-timezone.timedelta(minutes=interval)):
        deleted+=1
        temp.delete()

    if deleted:
        logger.info("Has been deleted {0} records of temporal data older than {1}"
                    .format(deleted, filter_date_time_condition.strftime(settings.DATE_FORMAT_EXTERNAL_WEB_SERVICE)))
    else:
        logger.info("No records deleted this time.")

