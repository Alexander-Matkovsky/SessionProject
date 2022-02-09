import errno
import logging
import os
from flask import Blueprint, request
from .err_bp import handle_bad_input_501
from .home_bp import set_msg, validate_json_keys
from .sessions_bp import session_id_validation

def log_level_validation(cur_log_level):
    curr_log_lvls = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]
    return True if cur_log_level in curr_log_lvls else False


# dynamic methods, each for the appropriate level:
def print_CRITICAL(logger, logging_data):
    for data in logging_data: logger.critical(data)

def print_ERROR(logger, logging_data):
    for data in logging_data: logger.error(data)

def print_WARNING(logger, logging_data):
    for data in logging_data: logger.warning(data)

def print_INFO(logger, logging_data):
    for data in logging_data: logger.info(data)

def print_DEBUG(logger, logging_data):
    for data in logging_data: logger.debug(data)

def print_NOTSET(logger, logging_data):
    for data in logging_data: logger.notset(data)


# logging the data to a .log file:
def log_data(logger, session_id, json_data):

    # list for relevant logging params:
    logging_data = []

    # parsering the json params:
    str_log_level = json_data["level"]
    
    # validate str_log_level:
    if log_level_validation(str_log_level) is False:
        return handle_bad_input_501("The provided log level isn't valid!")

    logging_data.append(str_log_level)
    logging_data.append(json_data["timestamp"])
    logging_data.append(json_data["fileName"])
    logging_data.append(json_data["lineNumber"])

    # create log level printings according to provided log level, then set the same log level:
    dynamic_log_printer = globals()["print_%s" % str_log_level]
    logger.setLevel(logging.getLevelName(str_log_level))

    # config session formatter both for file_handler and stream_handler:
    session_formatter = logging.Formatter("%(asctime)s::%(levelname)s::%(name)s::%(message)s")
    
    # file_handler configurations:
    log_filename = f'logging/{session_id}.log'
    os.makedirs(os.path.dirname(log_filename), exist_ok=True)

    file_handler = logging.FileHandler(filename=log_filename, mode="a")
    file_handler.set_name(session_id)
    file_handler.setFormatter(session_formatter)

    # stream_handler configurations:
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(session_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    # dynamic printing to the relevant log:
    dynamic_log_printer(logger, logging_data)

    # removing both file and stream handlers, in order to avoid duplications:
    logger.removeHandler(file_handler)
    logger.removeHandler(stream_handler)


log_blueprint = Blueprint('log', __name__)

# handles invalid requests:
@log_blueprint.route("/log", methods=["GET", "PUT", "DELETE"])
def handle_session_log_forbidden_requests():
    return handle_bad_input_501("This method is forbidden for log url!")

# handles posting log to db:
@log_blueprint.route("/log", methods=["POST"])
def log():

    ret_val = ""

    # retriving the session id from the url:
    curr_session_id = request.args.get("session_id")

    # validate the session id:
    if session_id_validation(curr_session_id) is False:
        return handle_bad_input_501("The provided session id isn't valid!")

    # validate there arn't missing required keys in json file:
    if validate_json_keys(request.json) is False:
        return handle_bad_input_501("There is a missing key/s in the provided json!")

    logger = logging.getLogger("__name__")

    curr_msg = request.json["message"]
    ret_val+=set_msg(curr_session_id, curr_msg)

    # log the data to a dedicated file (session_id.log):
    log_data(logger, curr_session_id, request.json)

    ret_val+=f"logging session id: {str(curr_session_id)} done!"
    return ret_val