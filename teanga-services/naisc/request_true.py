#curl -X GET "http://localhost:8080/naisc/auto/block?left=left&right=right" -H "accept: application/json"
import requests
import json
import pprint
port="8080"
naisc_path = f'http://localhost:{port}'
config = "auto"
left_dataset = "./datasets/small_left.rdf"
right_dataset = "./datasets/small_right.rdf"
id1 = "left_id345"
id2 = "right_id345"



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
                    "left":id1,
                    "right":id2,
                      })
#print(r2.url)
print(r2.text)
blocks = json.loads(r2.text)
print_BLK = r2.text[:500] if len(r2.text) > 500 else r2.text 
print("{len(blocks)} blocks: {print_BLK}")

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
    print_LSP = r.text[:500] if len(r.text) > 500 else r.text 
    print(f'{len(langStringPairs)} LSP: {print_LSP}')

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
        try: text_features.extend(json.loads(r.text))
        except: 
            print(r.text) 
            exit()
        print_TF = r.text[:500] if len(r.text) > 500 else r.text 
        print(f'text_features: {print_TF}')

    #step6 - for every block graph_features
    url = f'{naisc_path}/naisc/{config}/graph_features'
    data = json.dumps(block)
    r = requests.post(
            url  = url,
            data = data,
            headers= {'Content-Type': 'application/json'}
                     )
    graph_features = json.loads(r.text)
    print_GF = r.text[:500] if len(r.text) > 500 else r.text 
    print(f'graph_features: {print_GF}')

    #step7 - for every block score 
    url = f'{naisc_path}/naisc/{config}/score'
    data = json.dumps(text_features+graph_features)
    r = requests.post(
            url  = url,
            data = data,
            headers= {'Content-Type': 'application/json'}
                     )
    scores = json.loads(r.text)
    print_scores = r.text[:500] if len(r.text) > 500 else r.text 
    print(f'scores: {print_scores}')
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
print_FA = r.text[:250]
prin_LA = r.text[-250:]
for alig in final_alignments:    
    pprint.pprint(alig)
    print("\n")
