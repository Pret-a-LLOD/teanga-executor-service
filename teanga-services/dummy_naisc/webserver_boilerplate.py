from flask import Flask, jsonify, request
import pandas as pd
import numpy as np

import collections
print(__file__)
webserver = Flask(__name__)

@webserver.route("/naisc/upload/<id_>",methods=["PUT"])
def upload(id_):
    """# #{
    /naisc/upload/{id}:
    put:
      summary: Upload a dataset to Naisc
      operationId: upload
      requestBody:
        content:
          application/rdf+xml:
            schema:
              type: string
          text/turtle:
            schema:
              type: string
          application/n-triples:
            schema:
              type: string
      parameters:
        - name: id
          in: path
          description: The identifier of the dataset
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Dataset uploaded successfully
    """# #}
    print(request.data)
    print(request.files)
    return f'upload of {id_} sucessful'

@webserver.route("/naisc/<config>/block",methods=["GET"])
def block(config):  
    """# #{
    /naisc/{config}/block:
    get:
      summary: Find a blocking between two datasets
      operationId: block
      parameters:
        - name: left
          in: query
          description: The ID of the left dataset to block as uploaded to upload
          required: true
          schema:
            type: string
        - name: right
          in: query
          description: The ID of the right dataset to block as uploaded to upload
          required: true
          schema:
            type: string
        - name: config
          in: path
          description: The configuration to be used for matching
          required: true
          schema:
            type: string
      responses:
        '200':
          description: The blocking succeeded
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Blocking"
    """# #}
    print(request.args)
    print(request.json)
    print(request.data)
    if request.data: print(request.data)
    else: print("request body is empty")
    Blocking = {
    "entity1": {"uri": "http://dbpedia.org/resource/Example",
                "dataset": "dbpedia"},
    "entity2": {"uri": "http://en-word.net/lemma/example",
                "dataset": "english-wordnet"},
    "property": "http://www.w3.org/2004/02/skos/core#exactMatch",
    "probability": 0.8
    }
    return jsonify([Blocking])

@webserver.route("/naisc/<config>/extract_text",methods=["POST"])
def extract_text(config):
    """# #{
    /naisc/{config}/extract_text:
    post:
      summary: Extract text with a lens
      operationId: extract_text
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Blocking'
      parameters: 
        - name: config
          in: path
          description: The configuration to be used for matching
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/LangStringPair"
    """# #}
    if request.data: print(eval(request.data))
    else: print("request body is empty")
    LangStringPair = {
        "string1": "example",
        "lang1": "en",
        "string2": "Beispiel",
        "lang2": "de",
        "tag": "default"
    }
    return jsonify([LangStringPair])

@webserver.route("/naisc/<config>/text_features",methods=["POST"])
def text_features(config):
    """# #{
    /naisc/{config}/text_features:
    post:
      summary: Extract features from text
      operationId: text_features
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LangStringPair'
      parameters: 
        - name: config
          in: path
          description: The configuration to use
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Feature'
    """# #}
    if request.data: print(eval(request.data))
    else: print("request body is empty")
    Feature = {
     "name": "jaccard",
     "value": 0.6
    }
    return jsonify([Feature]) 

@webserver.route("/naisc/<config>/graph_features",methods=["POST"])
def graph_features(config): 
    """# #{
    /naisc/{config}/graph_features:
    post:
      summary: Extract features from the graph
      operationId: graph_features
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Blocking'
      parameters: 
        - name: config
          in: path
          description: The configuration to use
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Feature'
    """# #}
    if request.data: print(eval(request.data))
    else: print("request body is empty")
    Feature = {
        "name": "graph_feature",
        "value": 0.223
    }
    return jsonify([Feature]) 

@webserver.route("/naisc/<config>/score",methods=["POST"])
def score(config):
    """# #{
    /naisc/{config}/score:
    post:
      summary: Produce a score from a set of features
      operationId: score
      requestBody:
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/Feature'
      parameters:
        - name: config
          in: path
          description: The configuration to use
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Score'
    """# #}
    if request.data: print(eval(request.data))
    else: print("request body is empty")
    Score = {
        "property": "http://www.w3.org/2004/02/skos/core#exactMatch",
        "probability": 0.8
    }
    return jsonify([Score]) 

@webserver.route("/naisc/<config>/match",methods=["POST"])
def match(config): 
    """# #{
    /naisc/{config}/match:
    post:
      summary: Produce a matching from some alignments
      operationId: match
      requestBody:
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/Alignment'
      parameters:
        - name: config
          in: path
          description: The configuration to use
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Alignment'
    """# #}
    if request.data: print(eval(request.data))
    else: print("request body is empty")

    Alignment = { 
        "entity1":{
          "uri": "http://dbpedia.org/resource/Example",
          "dataset": "dbpedia"
          },
        "entity2":{
          "uri": "http://en-word.net/lemma/example",
          "dataset": "english-wordnet"
          },
        "property": "http://www.w3.org/2004/02/skos/core#exactMatch",
        "probability": 0.8
    }
    return jsonify([Alignment])

if __name__ == "__main__":
    webserver.run("0.0.0.0",
                  port=8001,
                  debug=True)
