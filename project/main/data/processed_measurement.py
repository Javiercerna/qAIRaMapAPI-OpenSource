import project.main.data.post_data_helper as post_data_helper
import project.main.data.get_data_helper as get_data_helper
import project.main.util_helper as util_helper
import project.main.same_function_helper as same_helper
import project.main.business.get_business_helper as get_business_helper
from flask import jsonify, make_response, request
from project import app, socketio
from datetime import timedelta
import dateutil.parser
import dateutil.tz
import datetime
import pytz

pollutants = ['CO','CO2','NO2','O3','H2S','SO2','PM25','PM10','VOC']

@app.route('/api/processed_measurements/', methods=['GET'])
def getProcessedData():
    """ Lists all measurements of processed measurement of the target qHAWAX within the initial and final date """
    qhawax_name = request.args.get('name')
    try:
        interval_minutes = int(request.args.get('interval_minutes')) \
            if request.args.get('interval_minutes') is not None else 60
        final_timestamp = datetime.datetime.now(dateutil.tz.tzutc())
        initial_timestamp = final_timestamp - datetime.timedelta(minutes=interval_minutes)
        processed_measurements = get_data_helper.queryDBProcessed(qhawax_name, initial_timestamp, final_timestamp)
        if processed_measurements is not None:
            return make_response(jsonify(processed_measurements), 200)
        return make_response(jsonify('Measurements not found'), 200)
    except TypeError as e:
        json_message = jsonify({'error': '\'%s\'' % (e)})
        return make_response(json_message, 400)

@app.route('/api/dataProcessed/', methods=['POST'])
def handleProcessedDataByQhawax():
    """
    Records processed and valid processed measurements every five seconds
    qHAWAX: Record new measurement
    """
    flag_email = False
    data_json = request.get_json()
    try:
        product_id = data_json['ID']
        data_json = util_helper.validTimeJsonProcessed(data_json)
        data_json = util_helper.validAndBeautyJsonProcessed(data_json)
        post_data_helper.storeProcessedDataInDB(data_json)
        data_json['ID'] = product_id
        data_json['zone'] = "Undefined Zone"
        mode = same_helper.getQhawaxMode(product_id)
        inca_value = same_helper.getMainIncaQhawaxTable(product_id)
        if(mode == "Customer" and inca_value!=None):
            data_json['zone'] = get_business_helper.getNoiseData(product_id)
            minutes_difference,last_time_turn_on = get_business_helper.getHoursDifference(product_id)
            if(minutes_difference!=None):
                if(minutes_difference<5):
                    post_data_helper.validTimeOfValidProcessed(10,"minute",last_time_turn_on,data_json,product_id,inca_value)
                elif(minutes_difference>=5):
                    post_data_helper.validTimeOfValidProcessed(2,"hour",last_time_turn_on,data_json,product_id,inca_value)
        data_json = util_helper.setNoneStringElements(data_json)
        socketio.emit(data_json['ID'] + '_processed', data_json)
        return make_response('OK', 200)
    except TypeError as e:
        json_message = jsonify({'error': '\'%s\'' % (e)})
        return make_response(json_message, 400)

@app.route('/api/dataProcessedMobile/', methods=['POST'])
def handleProcessedDataByMobileQhawax():
    data_json = request.get_json()
    try:
        product_id = data_json['ID']
        time_zone = float(-5)
        location_time_zone = pytz.timezone("America/Lima")
        data_json = util_helper.validTimeJsonProcessedTest(data_json,time_zone,location_time_zone)
        if (data_json is not None):
            data_json = util_helper.validAndBeautyJsonProcessedLatest(data_json)
            post_data_helper.storeProcessedDataInDB(data_json)
            data_json['ID'] = product_id
            minutes_difference,last_time_turn_on = get_business_helper.getHoursDifference(product_id)
            minutes_difference = 10
            if(minutes_difference!=None):
                if(minutes_difference<5):
                    if(last_time_turn_on + datetime.timedelta(minutes=10) < datetime.datetime.now(dateutil.tz.tzutc())):
                        post_data_helper.validAndBeautyJsonValidProcessedMobile(data_json,product_id)
                elif(minutes_difference>=5):
                    if(last_time_turn_on + datetime.timedelta(hours=2) < datetime.datetime.now(dateutil.tz.tzutc())):
                        post_data_helper.validAndBeautyJsonValidProcessedMobile(data_json,product_id)
            return make_response('OK', 200) 
        return make_response('Time is not correct', 400)
    except TypeError as e:
        json_message = jsonify({'error': '\'%s\'' % (e)})
        return make_response(json_message, 400)

@app.route('/api/dataProcessedDrone/', methods=['POST'])
def handleProcessedDataByDrone():
    """
    Records processed and valid processed measurements every second by drone
    qHAWAX: Record new measurement
    """
    flag_email = False
    data_json = request.get_json()
    try:
        product_id = data_json['ID']
        data_json = util_helper.validTimeJsonProcessed(data_json)
        data_json = util_helper.validAndBeautyJsonProcessed(data_json)
        post_data_helper.storeProcessedDataInDB(data_json)
        data_json['ID'] = product_id
        data_json = util_helper.setNoneStringElements(data_json)
        for i in range(len(pollutants)):
            socket_name = data_json['ID'] +'_'+ str(pollutants[i])+'_processed'
            pollutant = str(pollutants[i]) + "_ug_m3" if(pollutants[i] in ['CO','NO2','O3','H2S','SO2']) else str(pollutants[i])
            new_data_json = {"sensor": pollutants[i],"center":{"lat":data_json["lat"],"lng":data_json["lon"]}}
            new_data_json[pollutants[i]]= data_json[pollutant]
            socketio.emit(socket_name, new_data_json) #qH006_CO_proccessed
        return make_response('OK', 200)
    except TypeError as e:
        json_message = jsonify({'error': '\'%s\'' % (e)})
        return make_response(json_message, 400)

@app.route('/api/processed_measurements_andean_drone/', methods=['GET'])
def getProcessedDataFromAndeanDrone():
    """ Lists all measurements of processed measurement of the target drone within the initial and final date """
    qhawax_name = request.args.get('qhawax_name')
    initial_timestamp = datetime.datetime.strptime(request.args.get('initial_timestamp'), '%d-%m-%Y %H:%M:%S')
    final_timestamp = datetime.datetime.strptime(request.args.get('final_timestamp'), '%d-%m-%Y %H:%M:%S')
    try:
        processed_measurements = get_data_helper.queryDBProcessed(qhawax_name, initial_timestamp, final_timestamp)
        if processed_measurements is not None:
            return make_response(jsonify(processed_measurements), 200)
        return make_response(jsonify('Measurements not found'), 200)
    except TypeError as e:
        json_message = jsonify({'error': '\'%s\'' % (e)})
        return make_response(json_message, 400)

@app.route('/api/measurements_by_pollutant_during_flight/', methods=['GET'])
def getProcessedByPollutantDuringFlight():
    """ Lists all measurements of processed measurement of the target qHAWAX within the initial and final date """
    qhawax_name = str(request.args.get('name'))
    pollutant = str(request.args.get('pollutant'))
    try:
        start_flight = get_data_helper.qHAWAXIsInFlight(qhawax_name)
        if(start_flight is not None):
            final_timestamp = datetime.datetime.now(dateutil.tz.tzutc())
            processed_measurements = get_data_helper.queryDBProcessedByPollutant(qhawax_name, start_flight, final_timestamp,pollutant)
            if processed_measurements is not None:
                return make_response(jsonify(processed_measurements), 200)
        return make_response(jsonify('Measurements not found'), 200)
    except TypeError as e:
        json_message = jsonify({'error': '\'%s\'' % (e)})
        return make_response(json_message, 400)

@app.route('/api/processed_measurements_before_48_hours/', methods=['POST'])
def deleteProcessedMeasurementsBefore48Hours():
    #qhawax_name = str(request.args.get('qhawax_name'))
    try:
        before = datetime.datetime.now(dateutil.tz.tzutc()) - datetime.timedelta(hours=48)
        #qhawax_id = same_helper.getQhawaxID(qhawax_name)
        data = post_data_helper.deleteValuesBetweenTimestampsProcessedMeasurement(before)
        if data is not None:
            return make_response(jsonify(data), 200)
        return make_response(jsonify("Measurements not found"), 200)
    except TypeError as e:
        json_message = jsonify({'error': '\'%s\'' % (e)})
        return make_response(json_message, 400)

@app.route('/api/valid_processed_measurements_before_48_hours/', methods=['POST'])
def deleteValidProcessedMeasurementsBefore48Hours():
    #qhawax_name = str(request.args.get('qhawax_name'))
    try:
        before = datetime.datetime.now(dateutil.tz.tzutc()) - datetime.timedelta(hours=48)
        #qhawax_id = same_helper.getQhawaxID(qhawax_name)
        data = post_data_helper.deleteValuesBetweenTimestampsValidProcessedMeasurement(before)
        if data is not None:
            return make_response(jsonify(data), 200)
        return make_response(jsonify("Measurements not found"), 200)
    except TypeError as e:
        json_message = jsonify({'error': '\'%s\'' % (e)})
        return make_response(json_message, 400)
