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
    Handle GET and POST requests for a specific zone.
    
    :param base_id: The base ID of the zone.
    :param zone_id: The zone ID within the base.
    :return: A Flask response object.
    """
    # Validate base_id
    if not (1 <= base_id <= 4):
        return app.response_class(
            response=json.dumps({"err": "invalid base id"}),
            status=400,
            mimetype='application/json'
        )
    
    # Validate zone_id
    if not (1 <= zone_id <= 12):
        return app.response_class(
            response=json.dumps({"err": "invalid zone id"}),
            status=400,
            mimetype='application/json'
        )

    # Calculate the zone address based on base_id and zone_id
    zone_addr = (base_id - 1) * const.NEASMART_BASE_SLAVE_ADDR + zone_id * const.BASE_ZONE_ID

    if request.method == 'GET':
        # Handle GET request: Retrieve state, setpoint, temperature, and relative humidity
        data = {
            "state": context[slave_id].getValues(const.READ_HR_CODE, zone_addr, count=1)[0],
            "setpoint": dpt_9001.unpack_dpt9001(context[slave_id].getValues(const.READ_HR_CODE, zone_addr + const.ZONE_SETPOINT_ADDR_OFFSET, count=1)[0]),
            "temperature": dpt_9001.unpack_dpt9001(context[slave_id].getValues(const.READ_HR_CODE, zone_addr + const.ZONE_TEMP_ADDR_OFFSET, count=1)[0]),
            "relative_humidity": context[slave_id].getValues(const.READ_HR_CODE, zone_addr + const.ZONE_RH_ADDR_OFFSET, count=1)[0]
        }
        # Create a JSON response with the retrieved data
        response = app.response_class(
            response=json.dumps(data),
            status=200,
            mimetype='application/json'
        )
    elif request.method == 'POST':
        # Handle POST request: Update state and setpoint
        payload = request.json
        op_state = payload.get("state")
        setpoint = payload.get("setpoint")
        # Validation and update logic here...
        response = app.response_class(status=202)
    return response

# Define all other routes here...