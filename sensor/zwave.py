from main.logger_helper import L
from common import Constant
from main.admin import models
import six
if six.PY3:
    from pydispatch import dispatcher
else:
    from louie import dispatcher
import time
from pydispatch import dispatcher as haiot_dispatch


class P:
    network = None
    module_imported = False

try:
    import openzwave
    from openzwave.node import ZWaveNode
    from openzwave.value import ZWaveValue
    from openzwave.scene import ZWaveScene
    from openzwave.controller import ZWaveController
    from openzwave.network import ZWaveNetwork
    from openzwave.option import ZWaveOption
    P.module_imported = True
except Exception as e:
    L.l.info("Cannot import openzwave")


def louie_network_started(network):
    print('Louie signal: OpenZWave network started: homeid {:08x} - {} nodes found.'.format(
        network.home_id, network.nodes_count))


def louie_network_failed(network):
    L.l.info('Louie signal: OpenZWave network failed.')


def louie_network_resetted(network):
    L.l.info('Louie signal: OpenZWave network is resetted.')


# https://raw.githubusercontent.com/OpenZWave/python-openzwave/master/examples/api_demo.py
def louie_network_ready(network):
    L.l.info('Louie signal: ZWave network is ready : {} nodes were found.'.format(network.nodes_count))
    L.l.info('Louie signal: Controller : {}'.format(network.controller))
    dispatcher.connect(louie_node_update, ZWaveNetwork.SIGNAL_NODE)
    dispatcher.connect(louie_value, ZWaveNetwork.SIGNAL_VALUE)
    dispatcher.connect(louie_value_update, ZWaveNetwork.SIGNAL_VALUE_REFRESHED)
    dispatcher.connect(louie_value_added, ZWaveNetwork.SIGNAL_VALUE_ADDED)
    #dispatcher.connect(louie_value_changed, ZWaveNetwork.SIGNAL_VALUE_CHANGED)
    dispatcher.connect(louie_value_removed, ZWaveNetwork.SIGNAL_VALUE_REMOVED)
    dispatcher.connect(louie_ctrl_message, ZWaveController.SIGNAL_CONTROLLER)


def louie_node_update(network, node):
    #L.l.info('Louie signal: Node update : {}.'.format(node))
    pass


def louie_value(network, node, value):
    #L.l.info('Louie signal: Value {} for {}={} {}'.format(node.product_name, value.label, value.data, value.units))
    #PowerLevel (Normal), Energy (kWh),  Energy (kVAh), Power (W), Voltage (V), Current (A), Power Factor, Unknown
    if value.label == "Power" or (value.label == "Energy" and value.units == "kWh"):
        #L.l.info("Saving power utility")
        if value.units == "W":
            units_adjusted = "watt"  # this should match Utility unit name in models definition
        else:
            units_adjusted = value.units
        haiot_dispatch.send(Constant.SIGNAL_UTILITY_EX, sensor_name=node.product_name,
                            value=value.data, unit=units_adjusted)
    else:
        current_record = models.Sensor.query.filter_by(sensor_name=node.product_name).first()
        current_record.vad = None
        current_record.iad = None
        record = models.Sensor(sensor_name=node.product_name)
        if value.label == "Voltage":
            record.vad = value.data
            record.save_changed_fields(current_record=current_record, new_record=record, notify_transport_enabled=True,
                                       save_to_graph=True, debug=False)
        elif value.label == "Current":
            record.iad = value.data
            record.save_changed_fields(current_record=current_record, new_record=record, notify_transport_enabled=True,
                                       save_to_graph=True, debug=False)
        current_record.commit_record_to_db()


def louie_value_update(network, node, value):
    L.l.info('Louie signal: Value update: {} = {}.'.format(node, value))


def louie_value_changed(network, node, value):
    L.l.info('Louie signal: Value changed for {}={} {}'.format(value.label, value.data, value.units))


def louie_value_added(network, node, value):
    L.l.info('Louie signal: Value added: {} = {}.'.format(node, value))


def louie_value_removed(network, node, value):
    L.l.info('Louie signal: Value removed: {} = {}.'.format(node, value))


def louie_ctrl_message(state, message, network, controller):
    L.l.info('Louie signal : Controller message : {}.'.format(message))


def unload():
    if P.network is not None:
        P.network.stop()


# http://openzwave.github.io/python-openzwave/network.html
def init():
    if P.module_imported:
        device = "/dev/ttyACM0"
        L.l.info('Zwave initialising on {}'.format(device))
        # Define some manager options
        options = ZWaveOption(device, config_path="../openzwave/config", user_path=".", cmd_line="")
        options.set_log_file("OZW_Log.log")
        options.set_append_log_file(False)
        options.set_console_output(False)
        options.set_save_log_level("Debug")
        #options.set_save_log_level('Info')
        options.set_logging(False)
        #options.set_logging(True)
        options.set_poll_interval(5)
        options.set_save_configuration(True)
        options.lock()

        # Create a network object
        P.network = ZWaveNetwork(options, log=None, autostart=False)
        dispatcher.connect(louie_network_started, ZWaveNetwork.SIGNAL_NETWORK_STARTED)
        dispatcher.connect(louie_network_failed, ZWaveNetwork.SIGNAL_NETWORK_FAILED)
        dispatcher.connect(louie_network_resetted, ZWaveNetwork.SIGNAL_NETWORK_RESETTED)
        dispatcher.connect(louie_network_ready, ZWaveNetwork.SIGNAL_NETWORK_READY)

        P.network.start()

        L.l.info("Waiting for zwave driver")
        for i in range(0, 120):
            if P.network.state >= P.network.STATE_STARTED:
                L.l.info("Zwave driver started")
                break
            else:
                time.sleep(0.1)
        if P.network.state < P.network.STATE_STARTED:
            L.l.info("Can't initialise zwave driver. Look at the logs in OZW_Log.log")
            return False
        L.l.info("Home id : {}, Nodes in network : {}".format(P.network.home_id_str, P.network.nodes_count))
        L.l.info("Waiting for network to become ready")
        for i in range(0, 120):
            if P.network.state >= P.network.STATE_READY:
                break
            else:
                time.sleep(0.1)
                #L.l.info("state = {}".format(P.network.state))
        if not P.network.is_ready:
            L.l.info("Can't start network! Look at the logs in OZW_Log.log")
            return False
        else:
            L.l.info("Network is started!")

        # not working
        #P.network.set_poll_interval(milliseconds=3000, bIntervalBetweenPolls=False)
        #P.network.test(1)
        return True
    else:
        L.l.info("Zwave init skipped")
        return False


def thread_run():
    #L.l.info("State is {}".format(P.network.state))
    for node_id in P.network.nodes:
        if id > 1:
            node = P.network.nodes[node_id]
            #L.l.info("Node {}".format(node))
            node.request_state()