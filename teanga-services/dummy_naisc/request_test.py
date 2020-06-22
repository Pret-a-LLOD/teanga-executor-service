#curl -X GET "http://localhost:8080/naisc/auto/block?left=left&right=right" -H "accept: application/json"
import requests
import json
port="8080"
naisc_path = f'http://localhost:{port}/naisc-rest'
config = "auto"
left_dataset = "small_left.rdf"
right_dataset = "small_right.rdf"
id1 = "left"
id2 = "right"



#step1 - upload left
left_file=open(left_dataset).read()
url = f'{naisc_path}/naisc/upload/{id1}'
r = requests.put(
                url=url,
                data=left_file
                )
print(r.text)



#step2 - upload right 
right_file=open(right_dataset).read()
url=f'{naisc_path}/naisc/upload/{id2}'
r = requests.put(
                url=url,
                data=right_file
                )
print(r.text)


#step3 - block
#url_dummy=f'http://localhost:{port}/naisc/{config}/block/{id1}/{id2}'
#url=f'http://localhost:{port}/naisc/{config}/block?left={id1}&right={id2}'
url2=f'{naisc_path}/naisc/{config}/block'
#r = requests.get(url  = url)
r2 = requests.get(url  = url2,
                  params = {
                    "left":"left",
                    "right":"right",
                      })
blocks = json.loads(r2.text)
print(blocks)

alignments = []
for block_idx, block in enumerate(blocks):
    print(f'{"-"*10}Start of Block #{block_idx+1}{"-"*10}')
    #step4 - for every block extract_text
    url=f'{naisc_path}/naisc/{config}/extract_text'
    data = json.dumps(block)
    r = requests.post(
            url  = url,
            data = data,
            headers= {'Content-Type': 'application/json'}
                     )
    langStringPairs = json.loads(r.text)
    print(f'LSP: {langStringPairs}')

    text_features = []
    for langStringPair in langStringPairs:
        #step5 - for every text -> text_features
        url = f'{naisc_path}/naisc/{config}/text_features'
        data = json.dumps(langStringPair) 
        r = requests.post(
                url  = url,
                data = data,
            headers= {'Content-Type': 'application/json'}
                         )
        text_features.extend(json.loads(r.text))
        print(f'text_features: {text_features}')

    #step6 - for every block graph_features
    url = f'{naisc_path}/naisc/{config}/graph_features'
    data = json.dumps(block)
    r = requests.post(
            url  = url,
            data = data,
            headers= {'Content-Type': 'application/json'}
                     )
    graph_features = json.loads(r.text)
    print(f'graph_features: {graph_features}')

    #step7 - for every block score 
    url = f'{naisc_path}/naisc/{config}/score'
    data = json.dumps(text_features+graph_features)
    r = requests.post(
            url  = url,
            data = data,
            headers= {'Content-Type': 'application/json'}
                     )
    scores = json.loads(r.text)
    print(f'scores: {scores}')
    for score in scores:
      alignment =\
      {
       "entity1":    block["entity1"],
       "entity2":    block["entity2"],
       "probability":score["probability"],
       "property":   score["property"],
      }
      alignments.append(alignment)
print(f'{"-"*10}END of Block #{block_idx+1}{"-"*10}')


#step8 - match 
url = f'{naisc_path}/naisc/{config}/match'
data = json.dumps(alignments)
r = requests.post(
        url  = url,
        data = data,
            headers= {'Content-Type': 'application/json'}
                 )
final_alignments= json.loads(r.text)
print(f'final_alignments: {final_alignments}')
