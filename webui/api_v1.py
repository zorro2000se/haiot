__author__ = 'Dan Cristian <dan.cristian@gmail.com>'

import os
from main import app, logger, db
from main.admin.model_helper import commit
from flask import request, abort, send_file, render_template
from common import constant, utils

@app.route('/apiv1/relay/get_pin')
def relay_get_web():
    pin=request.args.get('pin', '').strip()
    if pin == '':
        response = return_web_message(pin_value=None, err_message='Argument [pin] not provided')
    else:
        response = relay_get(pin=pin, from_web=True)
    return response

@app.route('/apiv1/relay/set_pin')
def relay_set_web():
    pin=request.args.get('pin', '').strip()
    value=request.args.get('value', '').strip()
    if pin == '':
        response = return_web_message(pin_value=None, err_message='Argument [pin] not provided')
    elif value == '':
        response = return_web_message(pin_value=None, err_message='Argument [value] not provided')
    else:
        response = relay_update(gpio_pin_code=pin, pin_value=value, from_web=True)
    return response

def return_web_message(pin_value, ok_message='', err_message=''):
    if pin_value:
        return 'OK: {} \n {}={}'.format(ok_message, constant.SCRIPT_RESPONSE_OK, pin_value)
    else:
        return 'ERR: {} \n {}={}'.format(err_message, constant.SCRIPT_RESPONSE_NOTOK, pin_value)

@app.route('/apiv1/db_update/model_name=<model_name>&filter_name=<filter_name>'
           '&filter_value=<filter_value>&field_name=<field_name>&field_value=<field_value>')
def generic_db_update(model_name, filter_name, filter_value, field_name, field_value):
    try:
        table = utils.class_for_name('main.admin.models', model_name)
        #http://stackoverflow.com/questions/19506105/flask-sqlalchemy-query-with-keyword-as-variable
        kwargs = {filter_name: filter_value}
        record = table.query.filter_by(**kwargs).first()
        if record:
            if hasattr(record, field_name):
                setattr(record, field_name, field_value)
                db.session.add(record)
                commit()
                return  '%s: %s' % (constant.SCRIPT_RESPONSE_OK, record)
            else:
                msg = 'Field {} not found in record {}'.format(field_name, record)
                logger.warning(msg)
                return  '%s: %s' % (constant.SCRIPT_RESPONSE_NOTOK, msg)
        else:
            msg = 'No records returned for filter_name={} and filter_value={}'.format(filter_name, filter_value)
            logger.warning(msg)
            return  '%s: %s' % (constant.SCRIPT_RESPONSE_NOTOK, msg)
    except Exception, ex:
        msg = 'Exception on /apiv1/db_update: {}'.format(ex)
        logger.error(msg)
        return  '%s: %s' % (constant.SCRIPT_RESPONSE_NOTOK, msg)

def return_error(message):
    return message
def return_ok():
    return "all ok"

@app.route('/ebooks', defaults={'req_path': ''})
@app.route('/<path:req_path>')
def dir_listing(req_path):
    try:
        #BASE_DIR = '/media/ebooks'
        BASE_DIR = '/temp'

        # Joining the base and the requested path
        abs_path = os.path.join(BASE_DIR, req_path)

        # Return 404 if path doesn't exist
        if not os.path.exists(abs_path):
            return abort(404)

        # Check if path is a file and serve
        if os.path.isfile(abs_path):
            return send_file(abs_path)

        # Show directory contents
        files = os.listdir(abs_path)
        return render_template('files.html', files=files)
    except Exception, ex:
        return 'Error request={}, err={}'.format(req_path, ex)