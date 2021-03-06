from main.logger_helper import L
from main.admin import models
from transport.mqtt_io import sender
from common import Constant


class P:
    openhab_topic = None

    def __init__(self):
        pass


def send_mqtt_openhab(subtopic, payload):
    sender.send_message(payload, P.openhab_topic + "/" + subtopic)

#  OUTBOUND RULES START


def rule_openhab_sensor(obj=models.Sensor(), field_changed_list=None):
    key = 'temperature'
    if hasattr(obj, key) and obj.temperature is not None:
        send_mqtt_openhab(subtopic=key + "_" + obj.sensor_name, payload=obj.temperature)
    key = 'humidity'
    if hasattr(obj, key) and obj.humidity is not None:
        send_mqtt_openhab(subtopic=key + "_" + obj.sensor_name, payload=obj.humidity)
    key = 'pressure'
    if hasattr(obj, key) and obj.pressure is not None:
        send_mqtt_openhab(subtopic=key + "_" + obj.sensor_name, payload=obj.pressure)
    key = 'vad'
    if hasattr(obj, key) and obj.vad is not None:
        send_mqtt_openhab(subtopic=key + "_" + obj.sensor_name, payload=obj.vad)
    key = 'vdd'
    if hasattr(obj, key) and obj.vdd is not None:
        send_mqtt_openhab(subtopic=key + "_" + obj.sensor_name, payload=obj.vdd)
    key = 'iad'
    if hasattr(obj, key) and obj.iad is not None:
        send_mqtt_openhab(subtopic=key + "_" + obj.sensor_name, payload=obj.iad)


def rule_openhab_utility(obj=models.Utility(), field_changed_list=None):
    if hasattr(obj, 'utility_type'):
        # L.l.info("PROCESSING utility {}".format(obj.utility_type))
        key = 'electricity'
        if obj.utility_type == key:
                if obj.units_2_delta is not None:
                    send_mqtt_openhab(subtopic=key + "_" + obj.utility_name, payload=obj.units_2_delta)
                if obj.units_delta is not None and obj.units_delta != 0:
                    send_mqtt_openhab(subtopic=key + "_" + obj.unit_name + "_" + obj.utility_name,
                                      payload=obj.units_delta)
        key = 'water'
        if obj.utility_type == key and obj.units_delta is not None:
            send_mqtt_openhab(subtopic=key + "_" + obj.utility_name, payload=obj.units_delta)
        key = 'gas'
        if obj.utility_type == key and obj.units_delta is not None:
            send_mqtt_openhab(subtopic=key + "_" + obj.utility_name, payload=obj.units_delta)
    else:
        # L.l.info("NO UTILITY TYPE in {}".format(obj))
        pass


def rule_openhab_alarm(obj=models.ZoneAlarm(), field_changed_list=None):
    key = 'contact'
    if obj.alarm_pin_triggered is True:
        state = "OPEN"
    else:
        state = "CLOSED"
    send_mqtt_openhab(subtopic=key + "_" + obj.alarm_pin_name, payload=state)


def rule_openhab_ups(obj=models.Ups(), field_changed_list=None):
    if field_changed_list is not None:
        key = 'power_failed'
        if key in field_changed_list:
            if obj.power_failed:
                state = "OFF"
            else:
                state = "ON"
            send_mqtt_openhab(subtopic="ups_" + key, payload=state)
        key = 'load_percent'
        if key in field_changed_list:
            send_mqtt_openhab(subtopic="ups_" + key, payload=obj.load_percent)
        key = 'battery_voltage'
        if key in field_changed_list:
            send_mqtt_openhab(subtopic="ups_" + key, payload=obj.battery_voltage)
        key = 'input_voltage'
        if key in field_changed_list:
            send_mqtt_openhab(subtopic="ups_" + key, payload=obj.input_voltage)


def rule_openhab_custom_relay(obj=models.ZoneCustomRelay(), field_changed_list=None):
    if field_changed_list is not None:
        if obj.relay_is_on:
            state = "ON"
        else:
            state = "OFF"
        send_mqtt_openhab(subtopic="relay_" + obj.relay_pin_name, payload=state)


def rule_openhab_heat_relay(obj=models.ZoneHeatRelay(), field_changed_list=None):
    if field_changed_list is not None:
        if obj.heat_is_on:
            state = "ON"
        else:
            state = "OFF"
        send_mqtt_openhab(subtopic="heat_" + obj.heat_pin_name, payload=state)


def rule_openhab_music(obj=models.Music(), field_changed_list=None):
    if field_changed_list is not None:
        zone = obj.zone_name
        for key in field_changed_list:
            if hasattr(obj, key):
                val = getattr(obj, key)
                send_mqtt_openhab(subtopic='mpd_' + key + '_' + zone, payload=val)
            else:
                L.l.warning('Field {} in change list but not in obj={}'.format(key, obj))


def rule_openhab_musicloved(obj=models.MusicLoved(), field_changed_list=None):
    if field_changed_list is not None:
        for key in field_changed_list:
            if hasattr(obj, key):
                val = getattr(obj, key)
                if key == 'lastfmloved':
                    if val is True:
                        val = 'ON'
                    else:
                        val = 'OFF'
                send_mqtt_openhab(subtopic='mpd_' + key, payload=val)
            else:
                L.l.warning('Field musicloved {} in change list but not in obj={}'.format(key, obj))


# INBOUD RULES START
def custom_relay(name, value):
    # L.l.info("Try to set custom relay {} to {}".format(name, value))
    t = models.ZoneCustomRelay
    relay = t().query_filter_first(t.relay_pin_name == name)
    if relay is not None:
        if relay.gpio_host_name == Constant.HOST_NAME:
            L.l.info("OK setting custom relay {} to {} from openhab".format(name, value))
            relay.relay_is_on = value
            relay.save_changed_fields(new_record=relay, notify_transport_enabled=True, save_all_fields=True)


def heat_relay(name, value):
    t = models.ZoneHeatRelay
    relay = t().query_filter_first(t.heat_pin_name == name)
    if relay is not None:
        if relay.gpio_host_name == Constant.HOST_NAME:
            L.l.info("OK setting heat relay {} to {} from openhab".format(name, value))
            relay.heat_is_on = value
            relay.save_changed_fields(new_record=relay, notify_transport_enabled=True, save_all_fields=True)
