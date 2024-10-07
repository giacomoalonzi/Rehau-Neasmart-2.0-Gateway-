from flask import Flask, request
import json
import dpt_9001
import const

app = Flask(__name__)

# Define the global context and slave_id
context = None
slave_id = None

@app.route("/zones/<int:base_id>/<int:zone_id>", methods=['POST', 'GET'])
def zone(base_id=None, zone_id=None):
    """
    Handles HTTP GET and POST requests for a specific zone in the system.
    Parameters:
    base_id (int, optional): The base identifier. Must be between 1 and 4 inclusive.
    zone_id (int, optional): The zone identifier. Must be between 1 and 12 inclusive.
    Returns:
    Response: A Flask response object containing JSON data or an error message.
    GET Method:
    - Retrieves the current state, setpoint, temperature, and relative humidity of the specified zone.
    - Returns a JSON response with the retrieved data and a status code of 200.
    POST Method:
    - Updates the state and/or setpoint of the specified zone based on the provided JSON payload.
    - Payload must contain at least one of "state" or "setpoint".
    - "state" must be an integer between 1 and 6 inclusive.
    - "setpoint" must be an integer or float.
    - Returns a status code of 202 if the update is successful.
    Error Handling:
    - Returns a status code of 400 with an error message if the base_id or zone_id is invalid.
    - Returns a status code of 400 with an error message if the payload is invalid or missing required fields.
    """

    if not (1 <= base_id <= 4):
        return app.response_class(
            response=json.dumps({"err": "invalid base id"}),
            status=400,
            mimetype='application/json'
        )
    if not (1 <= zone_id <= 12):
        return app.response_class(
            response=json.dumps({"err": "invalid zone id"}),
            status=400,
            mimetype='application/json'
        )

    zone_addr = (base_id - 1) * const.NEASMART_BASE_SLAVE_ADDR + zone_id * const.BASE_ZONE_ID


    if request.method == 'GET':
        data = {
            "state": context[slave_id].getValues(
                const.READ_HR_CODE,
                zone_addr,
                count=1)[0],
            "setpoint": dpt_9001.unpack_dpt9001(context[slave_id].getValues(
                const.READ_HR_CODE,
                zone_addr + const.ZONE_SETPOINT_ADDR_OFFSET,
                count=1)[0]),
            "temperature": dpt_9001.unpack_dpt9001(context[slave_id].getValues(
                const.READ_HR_CODE,
                zone_addr + const.ZONE_TEMP_ADDR_OFFSET,
                count=1)[0]),
            "relative_humidity": context[slave_id].getValues(
                const.READ_HR_CODE,
                zone_addr + const.ZONE_RH_ADDR_OFFSET,
                count=1)[0]
        }

        response = app.response_class(
            response=json.dumps(data),
            status=200,
            mimetype='application/json'
        )
    elif request.method == 'POST':
        payload = request.json
        op_state = payload.get("state")
        setpoint = payload.get("setpoint")
        if op_state is None and setpoint is None:
            return app.response_class(
                response=json.dumps({"err": "one of state or setpoint need to be specified"}),
                status=400,
                mimetype='application/json'
            )
        if op_state is not None:
            if type(op_state) is not int or op_state == 0 or op_state > 6:
                return app.response_class(
                    response=json.dumps({"err": "invalid state"}),
                    status=400,
                    mimetype='application/json'
                )
            if not isinstance(op_state, list):
                op_state = [op_state]
            context[slave_id].setValues(
                const.READ_HR_CODE,
                zone_addr,
                op_state)
        if setpoint is not None:
            if type(setpoint) is not int and type(setpoint) is not float:
                return app.response_class(
                    response=json.dumps({"err": "invalid setpoint"}),
                    status=400,
                    mimetype='application/json'
                )
            dpt_9001_setpoint = dpt_9001.pack_dpt9001(setpoint)
            if not isinstance(dpt_9001_setpoint, list):
                dpt_9001_setpoint = [dpt_9001_setpoint]
            context[slave_id].setValues(
                const.READ_HR_CODE,
                zone_addr + const.ZONE_SETPOINT_ADDR_OFFSET,
                dpt_9001_setpoint)

        response = app.response_class(
            status=202
        )

    return response


@app.route("/mixedgroups/<int:group_id>", methods=['GET'])
def get_mixed_circuit(group_id=None):
    """
    Retrieve the mixed circuit data for a specified group ID.
    This function fetches various parameters related to the mixed circuit, such as pump state,
    mixing valve opening percentage, flow temperature, and return temperature. The data is 
    retrieved from a Modbus context and returned as a JSON response.
    Parameters:
    group_id (int, optional): The ID of the mixed group. Must be between 1 and 3 inclusive. 
                              If the group_id is 0 or greater than 3, an error response is returned.
    Returns:
    flask.Response: A Flask response object containing the mixed circuit data in JSON format 
                    with a status code of 200 if successful. If the group_id is invalid, 
                    a JSON response with an error message and a status code of 400 is returned.
    Error Responses:
    - 400: {"err": "invalid mixed group id"} if the group_id is 0 or greater than 3.
    Successful Response Data:
    - pump_state (int): The state of the pump.
    - mixing_valve_opening_percentage (int): The percentage opening of the mixing valve.
    - flow_temperature (float): The flow temperature, unpacked using dpt_9001.
    - return_temperature (float): The return temperature, unpacked using dpt_9001.
    """

    if group_id == 0 or group_id > 3:
        return app.response_class(
            response=json.dumps({"err": "invalid mixed group id"}),
            status=400,
            mimetype='application/json'
        )
    data = {
        "pump_state": context[slave_id].getValues(
            const.READ_HR_CODE,
            const.MIXEDGROUP_BASE_REG[group_id] + const.MIXEDGROUP_PUMP_STATE_OFFSET,
            count=1)[0],
        "mixing_valve_opening_percentage": context[slave_id].getValues(
            const.READ_HR_CODE,
            const.MIXEDGROUP_BASE_REG[group_id] + const.MIXEDGROUP_VALVE_OPENING_OFFSET,
            count=1)[0],
        "flow_temperature": dpt_9001.unpack_dpt9001(context[slave_id].getValues(
            const.READ_HR_CODE,
            const.MIXEDGROUP_BASE_REG[group_id] + const.MIXEDGROUP_FLOW_TEMP_OFFSET,
            count=1)[0]),
        "return_temperature": dpt_9001.unpack_dpt9001(context[slave_id].getValues(
            const.READ_HR_CODE,
            const.MIXEDGROUP_BASE_REG[group_id] + const.MIXEDGROUP_RETURN_TEMP_OFFSET,
            count=1)[0])
    }
    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )
    return response


@app.route("/outsidetemperature", methods=['GET'])
def get_outside_temp():
    """
    Retrieves the outside temperature and the filtered outside temperature from the specified registers,
    formats the data as a JSON response, and returns it.
    The function performs the following steps:
    1. Reads the outside temperature value from the register defined by `const.OUTSIDE_TEMP_REG`.
    2. Reads the filtered outside temperature value from the register defined by `const.FILTERED_OUTSIDE_TEMP_REG`.
    3. Unpacks the retrieved values using the `dpt_9001.unpack_dpt9001` method.
    4. Constructs a dictionary containing both temperature values.
    5. Creates a JSON response with the temperature data, sets the HTTP status to 200, and specifies the MIME type as 'application/json'.
    6. Returns the constructed JSON response.
    Returns:
        flask.Response: A Flask response object containing the JSON-encoded temperature data.
    """
    
    data = {
        "outside_temperature": dpt_9001.unpack_dpt9001(context[slave_id].getValues(
            const.READ_HR_CODE,
            const.OUTSIDE_TEMP_REG,
            count=1)[0]),
        "filtered_outside_temperature": dpt_9001.unpack_dpt9001(context[slave_id].getValues(
            const.READ_HR_CODE,
            const.FILTERED_OUTSIDE_TEMP_REG,
            count=1)[0])
    }
    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )
    return response


@app.route("/notifications", methods=['GET'])
def get_hints_warnings_errors_presence():
    """
    Retrieves the presence status of hints, warnings, and errors from the context for a given slave ID.
    This function queries the context for specific addresses to determine if hints, warnings, and errors are present.
    It constructs a JSON response containing the presence status of each category.
    Returns:
        flask.Response: A Flask response object containing a JSON payload with the following structure:
            {
                "hints_present": bool,    # True if hints are present, False otherwise
                "warnings_present": bool, # True if warnings are present, False otherwise
                "error_present": bool     # True if errors are present, False otherwise
    """

    data = {
        "hints_present": context[slave_id].getValues(
            const.READ_HR_CODE,
            const.HINTS_PRESENT_ADDR,
            count=1)[0] == 1,
        "warnings_present": context[slave_id].getValues(
            const.READ_HR_CODE,
            const.WARNINGS_PRESENT_ADDR,
            count=1)[0] == 1,
        "error_present": context[slave_id].getValues(
            const.READ_HR_CODE,
            const.ERRORS_PRESENT_ADDR,
            count=1)[0] == 1
    }

    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )
    return response


@app.route("/mode", methods=['POST', 'GET'])
def mode():
    """
    Handle GET and POST requests to manage the operational mode.
    GET:
        - Retrieves the current operational mode from the context.
        - Returns:
            - JSON response containing the current mode.
            - HTTP Status 200 on success.
    POST:
        - Sets a new operational mode based on the provided payload.
        - Payload:
            - JSON object with a key "mode" containing the new mode value.
        - Validations:
            - The "mode" key must be present in the payload.
            - The mode value must be an integer between 1 and 5 (inclusive).
        - Returns:
            - HTTP Status 202 on successful update.
            - HTTP Status 400 if the payload is missing the "mode" key or if the mode value is invalid.
    Returns:
        - Flask response object with appropriate status and JSON data.
    """

    if request.method == 'GET':
        data = {
            "mode": context[slave_id].getValues(
                const.READ_HR_CODE,
                const.GLOBAL_OP_MODE_ADDR,
                count=1)[0]
        }

        response = app.response_class(
            response=json.dumps(data),
            status=200,
            mimetype='application/json'
        )
    elif request.method == 'POST':
        payload = request.json
        op_mode = payload.get("mode")
        if not op_mode:
            return app.response_class(
                response=json.dumps({"err": "missing mode key in payload"}),
                status=400,
                mimetype='application/json'
            )
        if type(op_mode) is not int or op_mode == 0 or op_mode > 5:
            return app.response_class(
                response=json.dumps({"err": "invalid mode"}),
                status=400,
                mimetype='application/json'
            )
        if not isinstance(op_mode, list):
            op_mode = [op_mode]
        context[slave_id].setValues(
            const.WRITE_HR_CODE,
            const.GLOBAL_OP_MODE_ADDR,
            op_mode)
        response = app.response_class(
            status=202,
        )

    return response


@app.route("/state", methods=['POST', 'GET'])
def state():
    """
    Handle the state of the application based on the HTTP request method.
    GET:
        - Retrieves the current state from the context using the slave_id.
        - Returns a JSON response with the state value.
        - Response status: 200 OK.
    POST:
        - Expects a JSON payload with a "state" key.
        - Validates the "state" value:
            - Must be present in the payload.
            - Must be an integer between 0 and 6 (inclusive).
        - Sets the state in the context using the slave_id.
        - Returns a response with status 202 Accepted if successful.
        - Returns a response with status 400 Bad Request if validation fails.
    Returns:
        - A Flask response object with the appropriate status and JSON payload.
    """

    if request.method == 'GET':
        data = {
            "state": context[slave_id].getValues(
                const.READ_HR_CODE,
                const.GLOBAL_OP_STATE_ADDR,
                count=1)[0]
        }
        response = app.response_class(
            response=json.dumps(data),
            status=200,
            mimetype='application/json'
        )

    elif request.method == 'POST':
        payload = request.json
        op_state = payload.get("state")
        if not op_state:
            return app.response_class(
                response=json.dumps({"err": "missing state key in payload"}),
                status=400,
                mimetype='application/json'
            )
        if type(op_state) is not int and op_state == 0 or op_state > 6:
            return app.response_class(
                response=json.dumps({"err": "invalid state"}),
                status=400,
                mimetype='application/json'
            )
        if not isinstance(op_state, list):
            op_state = [op_state]
        context[slave_id].setValues(
            const.WRITE_HR_CODE,
            const.GLOBAL_OP_STATE_ADDR,
            op_state)
        response = app.response_class(
            status=202,
        )

    return response


@app.route("/dehumidifiers/<int:dehumidifier_id>", methods=['GET'])
def get_dehumidifier(dehumidifier_id=None):
    """
    Retrieve the state of a specified dehumidifier.
    This function fetches the state of a dehumidifier based on the provided 
    dehumidifier ID. It validates the ID to ensure it is within the acceptable 
    range (1 to 9). If the ID is invalid, it returns a JSON response with an 
    error message and a 400 status code. If the ID is valid, it retrieves the 
    state of the dehumidifier from the context and returns it in a JSON response 
    with a 200 status code.
    Args:
        dehumidifier_id (int, optional): The ID of the dehumidifier to retrieve. 
                                         Must be between 1 and 9 inclusive.
    Returns:
        flask.Response: A Flask response object containing the state of the 
                        dehumidifier in JSON format, or an error message if 
                        the ID is invalid.
    """

    if dehumidifier_id > 9 or dehumidifier_id < 1:
        return app.response_class(
            response=json.dumps({"err": "invalid dehumidifier id"}),
            status=400,
            mimetype='application/json'
        )
    data = {
        "dehumidifier_state": context[slave_id].getValues(
            const.READ_HR_CODE,
            dehumidifier_id + const.DEHUMIDIFIERS_ADDR_OFFSET,
            count=1)[0],
    }

    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )
    return response


@app.route("/pumps/<int:pump_id>", methods=['GET'])
def get_extra_pumps(pump_id=None):
    """
    Retrieves the state of an extra pump based on the provided pump ID.
    Args:
        pump_id (int, optional): The ID of the pump to retrieve the state for. 
                                 Must be between 1 and 5 inclusive. Defaults to None.
    Returns:
        Response: A Flask response object containing the pump state in JSON format 
                  with a status code of 200 if the pump ID is valid.
                  If the pump ID is invalid, returns a JSON response with an error 
                  message and a status code of 400.
    """

    if pump_id > 5 or pump_id < 1:
        return app.response_class(
            response=json.dumps({"err": "invalid pump id"}),
            status=400,
            mimetype='application/json'
        )
    data = {
        "pump_state": context[slave_id].getValues(
            const.READ_HR_CODE,
            pump_id + const.EXTRA_PUMPS_ADDR_OFFSET,
            count=1)[0],
    }

    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )
    return response


@app.route("/health")
def get_health():
    return "OK"
