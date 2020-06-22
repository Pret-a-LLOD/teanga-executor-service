import flask
import random
import json
import subprocess

app = flask.Flask("teanga_backend")

@app.route("/",methods=["POST"])
def index():
    #jsonld=json.load(flask.request.files['document'])
    jsonld=json.load(flask.request.files['service_json'])

    #p = subprocess.Popen(jsonld['command'], shell=True)
    shell_status = subprocess.call(jsonld['command'], shell=True)
    #p.communicate(b'waiting for process to finish')
    if shell_status == 0:
        data = {"data": [random.random(),random.random(),random.random()]}
        header = {"Content-Type": "application/json"}
        response = (flask.jsonify(data), 200)
    else:
        response = (flask.jsonify({}), 503)
    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=4000)
