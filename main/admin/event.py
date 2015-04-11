from pydispatch import dispatcher
import logging
from common import constant, variable, utils
import common.utils
import transport
import models
import main
import model_helper
import graph_plotly
import relay
import node

def handle_local_event_db_post(model, row):
    #executed on local db changes done via web ui only
    print 'Signal was sent by model {} row {}'.format(model, row)
    if str(models.Parameter) in str(model):
        logging.info('Detected Parameter change ' + row)
    elif str(models.Module) in str(model):
        logging.info('Detected Module change, applying potential changes')
        if row.host_name == constant.HOST_NAME:
            main.init_module(row.name, row.active)
    elif str(models.Node) in str(model):
        logging.info('Detected Node change, applying potential changes')
        txt = model_helper.model_row_to_json(row, operation='update')
        transport.send_message_json(json = txt)

def handle_event_mqtt_received(client, userdata, topic, obj):
    #events received via mqtt transport
    #fixme: make it generic to work with any transport
    if constant.JSON_PUBLISH_TABLE in obj:
        table = str(obj[constant.JSON_PUBLISH_TABLE])
        if table == utils.get_table_name(models.Node):#'Node':
            node.node_run.node_update(obj)
            if 'execute_command' in obj:
                execute_command = obj['execute_command']
                host_name = obj['name']
                if host_name == constant.HOST_NAME and execute_command != '':
                    main.execute_command(execute_command)
        elif table == utils.get_table_name(models.ZoneHeatRelay):
            if relay.initialised:
                relay.relay_update(obj)

    if variable.NODE_THIS_IS_MASTER_OVERALL:
        if constant.JSON_PUBLISH_GRAPH_X in obj:
            if obj[constant.JSON_PUBLISH_SAVE_TO_GRAPH]:
                if graph_plotly.initialised:
                    graph_plotly.upload_data(obj)
                else:
                    logging.debug('Graph not initialised on obj upload to graph')
            else:
                pass
        else:
            logging.debug('Mqtt event without graphing capabilities {}'.format(obj))

def on_models_committed(sender, changes):
    try:
        for obj, change in changes:
            #avoid recursion
            if hasattr(obj, 'notify_transport_enabled'):
                if obj.notify_transport_enabled:
                    if hasattr(obj, 'notified_on_db_commit'):
                        if not obj.notified_on_db_commit:
                            obj.notified_on_db_commit = True
                            txt = model_helper.model_row_to_json(obj, operation=change)
                            transport.send_message_json(json = txt)
                else:
                    pass
    except Exception, ex:
        logging.critical('Error in DB commit hook, {}'.format(ex))

def init():
    #http://pydispatcher.sourceforge.net/
    #dispatcher.connect(handle_event_sensor, signal=common.constant.SIGNAL_SENSOR, sender=dispatcher.Any)
    dispatcher.connect(handle_local_event_db_post, signal=common.constant.SIGNAL_SENSOR_DB_POST, sender=dispatcher.Any)
    dispatcher.connect(handle_event_mqtt_received, signal=common.constant.SIGNAL_MQTT_RECEIVED, sender=dispatcher.Any)

