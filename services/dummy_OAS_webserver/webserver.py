from flask import Flask, jsonify
#from flasgger import Swagger
import pandas as pd


import collections
print(__file__)
webserver = Flask(__name__)

@webserver.route("/vocabulary/<language>/top/<number_of_words>",methods=["GET"])
def topK_words(language, number_of_words):
#{{ OpenAPI Specfication
    """
  /vocabulary/{language}/top/{number_of_words}:
    get:
      summary: List all words
      operationId: listTopK
      parameters:
        - name: language
          in: path
          description: language of the vocabulary
          required: true
          schema:
            type: string
        - name: number_of_words
          in: path
          description: How many top words return at one time (max 100)
          required: true 
          schema:
            type: integer
            format: int32
      responses:
        '200':
          description: A paged array of words
          content:
            application/json:    
              schema:
                $ref: "#/components/schemas/Words"
    """
#}}
    try:
        number_of_words = int(number_of_words)
    except:
        return "invalid number_of_words argument"
    with open("top_1000_English_words.csv") as rank:
        df_rank = pd.read_csv(rank)
        list_of_topWords = [word for word in df_rank["word"][:number_of_words]]
        return jsonify({f'word_list':list_of_topWords})#jsonify(list_of_topWords)

@webserver.route("/wordembeddings",methods=["POST"])
def wordembeddings():
#{{ OpenAPI Specification
    """
  /wordembeddings:
    post:
      summary: calculate word embeddings for each sentence in as list of sentences
      operationId: calculateWordEmbeddings 
      parameters:
        - name: language
          in: path
          description: language of the vocabulary
          required: true
          schema:
            type: string
        - name: number_of_words
          in: path
          description: How many top words return at one time (max 100)
          required: true 
          schema:
            type: integer
            format: int32
      responses:
        '200':
          description: A paged array of words
          content:
            application/json:    
              schema:
                $ref: "#/components/schemas/Embeddings"
    """
#}}
    return jsonify([[1.2, 1.0],[3.13, 4.1]]) #jsonify({f'sentence_list':[[1.2,1.0],[3.13,4.1]]})

if __name__ == "__main__":
    webserver.run("0.0.0.0",
                  port=4000,
                  debug=True)
