from __future__ import print_function
import importlib
import time
import os
from collections import ChainMap

import copy
from os.path import join
from pprint import pprint
import subprocess
import shlex
import pip
import inspect
import requests
import datetime
import json
import yaml

def create_api_client(base_folder, OAS_folder, 
                      serviceOAS_absPath):
    service_id    = serviceOAS_absPath.split("/")[-1].replace(".yaml","")
    serviceClient_name = "client_"+service_id
    serviceClient_pkgFolder = os.path.join("/teanga/clients",
                                           serviceClient_name)

    createClient_cmd = shlex.split(f'./create_client.sh {serviceOAS_absPath} {service_id}')
    subprocess.call(createClient_cmd) 
    os.chdir(serviceClient_pkgFolder)
    pip.main(["install","."])
    os.chdir(base_folder)
    client = importlib.import_module("client_"+service_id)
    return client 


def flatten_info(OAS, operationId):
    flatten = {}
    for url in OAS['paths'].keys():
        for request_method in OAS['paths'][url].keys():
            operation_data=OAS['paths'][url][request_method]
            if operation_data["operationId"] == operationId:
                flatten["endpoint"] = url
                flatten["request_method"] = request_method
                flatten["parameters"] =  operation_data.get("parameters",[])
                flatten["requestBody"] =  operation_data.get("requestBody",{})
                flatten["sucess_response"] = operation_data["responses"]["200"]
                flatten["response_schemas"] = \
                        flatten["sucess_response"]['content']['application/json']['schema']\
                        if flatten["sucess_response"].get('content',False) else None
    flatten["schemas"] = OAS['components']['schemas']
    return flatten 

def match_input(currService_flattenedOAS, given_input, dependecies_inputs, dependecies_outputs):
    print(f"{'#'*31}") 
    print(f"{'#'*4} Beginning of Matching {'#'*4}") 
    print(f"{'#'*31}") 
    service_input = {}
    named_candidates = ChainMap(given_input, *dependecies_outputs, *dependecies_inputs)
    schemas_candidates = ChainMap(*dependecies_outputs, *dependecies_inputs)
    missing_parameters = []
    for expected_parameter in currService_flattenedOAS["parameters"]:
        parameter_name = expected_parameter['name']
        value = named_candidates.get(parameter_name, False)
        if value == False: missing_parameters.append(parameter_name)
        else: 
            expected_schema = [d for d 
                    in currService_flattenedOAS["parameters"] 
                    if d["name"] == parameter_name ][0] 
            service_input[parameter_name] = {"value":value} 
            service_input[parameter_name].update(expected_schema)

    print(f'expected inputs: {[d["name"] for d in currService_flattenedOAS["parameters"]]}')
    print(f'User input: {given_input}')
    if len(json.dumps(dependecies_inputs)) > 200: Idisplay = json.dumps(dependecies_inputs)[:100]
    else : Idisplay = json.dumps(dependecies_inputs)
    print(f'Dependencies INP: {Idisplay}')
    if len(json.dumps(dependecies_inputs)) > 200: Odisplay = json.dumps(dependecies_outputs)[:100]
    else : Odisplay = json.dumps(dependecies_outputs)
    print(f'Dependencies OUT: {Odisplay}')
    print(f'Missing parameters after matching: {missing_parameters}')


    requests_inputs = []
    if currService_flattenedOAS["requestBody"]:
        print(f'expected requestBody: {currService_flattenedOAS["requestBody"]}')
        # if there is input files, put then in requestBody
        if len(given_input.get("files",[])) == 1:
            requestBody_value = open(join("files",given_input["files"][0])).read()
            service_input["request_body"] = {"value":requestBody_value}
            requests_inputs.append(service_input)
        elif len(given_input.get("files",[])) > 1: 
            raise Exception("sending multiple files still not implemented")
        # if there is no input files, check if expected requestBody schema matches with dpdcies
        else:
            expected_schema = currService_flattenedOAS["requestBody"]\
                        ['content']['application/json']['schema']
            if expected_schema.get('$ref',False):
                expected_schema_name = expected_schema["$ref"].split("/")[-1]
                is_collection_expected = False
            elif expected_schema.get('items',False): 
                expected_schema_name = expected_schema['items']\
                                        ['$ref'].split("/")[-1]
                is_collection_expected = True 
            else:
                raise Exception("expected schema not valid")
            print(expected_schema_name)
            for d in dependecies_outputs:
                if d.get(expected_schema_name,False):
                    raise Exception("direct schema match not implemented yet")
                elif d.get(None, False):
                    if d[None]['schema_info']['name'] == None \
                       and d[None]['schema_info']['schema']['type'] == 'array' :
                           array_item_type = d[None]['schema_info']['schema']['items']['$ref'].split("/")[-1]
                           print(f'dnone: {d[None]}')
                           if expected_schema_name == array_item_type:
                               items = d[None]['value']
                               for idx, item in enumerate(items):
                                   if is_collection_expected:
                                       if "requestBody_value" in locals():
                                           requestBody_value.append(item)
                                       else:
                                           requestBody_value = [item]
                                   else:
                                       item_request = copy.copy(service_input)
                                       requestBody_value = item
                                       item_request["request_body"] = {"value":requestBody_value}
                                       requests_inputs.append(item_request)
                           else:
                               import ipdb;ipdb.set_trace()
                else:
                    raise Exception("requestBody not defined")
            if is_collection_expected:
                service_input["request_body"] = {"value":requestBody_value}
                requests_inputs.append(service_input)
    else:
        requests_inputs.append(service_input)



        """
        #schema_name = currService_flattenedOAS["requestBody"]['content']['application/json']['schema']['$ref'].split("/")[-1]
        requestBody_value = schemas_candidates.get(schema_name, {"value":{}})
        expected_requestBody_schema = currService_flattenedOAS['schemas'][schema_name]
        service_input["request_body"] = requestbody_value
        schema_name = currService_flattenedOAS["response_schemas"]["$ref"].split("/")[-1]
        requestBody_value = currService_flattenedOAS["schemas"][schema_name]
        """

    # expected output info
    if currService_flattenedOAS.get("response_schemas",False):
        if currService_flattenedOAS["response_schemas"]["type"] == "array":
            expected_output_schema = {"name":  None,
                                      "schema": currService_flattenedOAS["response_schemas"]
                                     }  
        else:
            expOut_name = currService_flattenedOAS["response_schemas"]["$ref"].split("/")[-1]
            expected_output_schema = {"name":expOut_name,
                                      "schema":currService_flattenedOAS["schemas"][expOut_name]}  
    else:
        expected_output_schema = None

    print(f"{'#'*4} End of Matching ") 
    if len(json.dumps(service_input)) > 500: print_input =json.dumps(service_input)[:500] 
    else: print_input =json.dumps(service_input)
    print(f'SERVICE INPUT: {print_input}')
    return requests_inputs, expected_output_schema 

def setup_request(named_inputs,
                endpoint,
                request_method,
                host_port):
    print("\n"*1) 
    print(f"{'#'*40}") 
    print(f"{'#'*4} Beginning of preparing request {'#'*4}") 
    print(f"{'#'*40}") 
    remaining_inputs = named_inputs.copy()
    for name, value in named_inputs.items():
        if f'{{{name}}}' in endpoint:
            endpoint = endpoint.replace(f'{{{name}}}',str(value))
            remaining_inputs.pop(name,None);
    url = f'http://localhost:{host_port}{endpoint}'
    if "request_body" in remaining_inputs.keys():
        data =  remaining_inputs.pop("request_body",None)
        if isinstance(data,dict) or isinstance(data,list) :
            headers= {'Content-Type': 'application/json'}
            print(data)
            request_ = requests.Request(
                          method=request_method.upper(),
                          headers=headers,
                          url=url,
                          params=remaining_inputs,
                          data=json.dumps(data))
        else:
            request_ = requests.Request(
                          method=request_method.upper(),
                          url=url,
                          params=remaining_inputs,
                          data=data)
    else:
        data = {}
        request_ = requests.Request(
                method=request_method.upper(),
                params=remaining_inputs,
                      url=url)
    request_ = request_.prepare()
    if len(json.dumps(data)) > 500: print_matched =json.dumps(named_inputs)[:500] 
    else: print_matched =json.dumps(named_inputs)
    print(f'all matched inputs : {named_inputs.keys()}\n {print_matched}')
    if len(json.dumps(data)) > 500: print_data =json.dumps(data)[:500] 
    else: print_data =json.dumps(data)
    print(f'what is in the body: {print_data}')
    print(f'what is in the params : {remaining_inputs}')    
    print(f'final url: {request_.url}')    

    print(f"{'#'*4} End of preparing request") 
    return request_ 

def execute_api_client(servicesOAS,
                       workflow_idx, workflow):
    session = requests.Session()
    currService_workflow = workflow[workflow_idx]
    print(f'{"-"*13} STEP {workflow_idx}:{currService_workflow["operation_id"]} {"-"*13}')
    currService_OAS = servicesOAS[workflow_idx]
    dependecies_OAS = [flatten_info(servicesOAS[workflow_idx]['OAS'], workflow_idx)
                        for workfolow_idx in currService_workflow['dependencies']]  
    dependecies_inputs = [workflow[workflow_idx]["input"]
                        for workflow_idx in currService_workflow['dependencies']]  
    dependecies_outputs = [{workflow[workflow_idx]["output"]["schema_info"]["name"]:workflow[workflow_idx]["output"]}
                        for workflow_idx in currService_workflow['dependencies']
                        if workflow[workflow_idx]["output"]["schema_info"] != None]  

    currService_flattenedOAS= flatten_info(currService_OAS['OAS'], currService_workflow["operation_id"])
    given_input = currService_workflow.get("input",{})
    requests_inputs, expected_output_schema =\
            match_input(currService_flattenedOAS, given_input, dependecies_inputs, dependecies_outputs) 
    responses = []
    for request_inputs in requests_inputs:
        service_name_val = {name:d["value"] for (name,d) in request_inputs.items()}
        request_ = setup_request(service_name_val,
                    currService_flattenedOAS["endpoint"],
                    currService_flattenedOAS["request_method"],
                    currService_workflow["host_port"])

        raw_api_response = session.send(request_).text
        if expected_output_schema != None: 
            api_response= eval(raw_api_response)
            responses.append(api_response)
        else:
            try:
                api_response= eval(raw_api_response)
            except:
                api_response= raw_api_response
            responses.append(json.dumps(api_response))

    print_r=json.dumps(responses)
    if len(responses) == 1 and not isinstance(responses[0],dict):
        value = responses[0]
    elif len(responses) > 1:
        if all([isinstance(response,list) for response in responses]):
            value = [d for r in responses for d in r] 
    if len(print_r) > 250:
        print(f'{len(responses)} responses : {print_r[:125]} ... {print_r[-125:]}')
    else:
        print(f'{len(responses)} responses : {print_r[:250]}')
    workflow[workflow_idx]["input"] = requests_inputs
    workflow[workflow_idx]["output"] =\
                            {"value":value,
                             "schema_info":expected_output_schema}
    print_output_val = json.dumps(workflow[workflow_idx]["output"]["value"])
    print_output_schema = json.dumps(workflow[workflow_idx]["output"]["schema_info"])
    if len(print_output_val) > 200: val = print_output_val[:200]  
    else: val = print_output_val[:]
    if len(print_output_schema) > 200: schema = print_output_schema[:200]  
    else: schema = print_output_schema[:]
    print(f'STEP {workflow_idx}:{currService_workflow["operation_id"]} output value: {val}')
    print(f'STEP {workflow_idx}:{currService_workflow["operation_id"]} output schema: {schema}')
    print(f'{"-"*13} END OF  STEP {workflow_idx}:{currService_workflow["operation_id"]} {"-"*13}')
    i=input()
    if i =="1":
        exit()
    return workflow

if __name__ == "__main__":
    today_date = datetime.datetime.now().strftime("%d%m%Y")
    base_folder=os.path.dirname(os.path.abspath(__file__))
    OAS_folder=os.path.join(base_folder,"OAS")
    os.chdir(base_folder) 
    workflow_file = os.path.join(base_folder,"workflows",f'updated_dev_naisc_workflow_{today_date}.json')

    workflow = json.load(open(workflow_file))
    OAS_specifications = {fn.split("_")[0]:
                            {
                                "filepath":os.path.join(OAS_folder,fn),
                                "OAS":yaml.load(open(os.path.join(OAS_folder,fn))),
                            }
                            for fn in sorted(os.listdir(OAS_folder))
                         }

    for (workflow_idx, serviceOAS) in OAS_specifications.items():
        #client = create_api_client(
        #            base_folder, OAS_folder, serviceOAS["filepath"],
        #        )
        workflow = execute_api_client(OAS_specifications,
                                      workflow_idx, workflow)
    with open("./IO/IO.json","w") as IO_file: 
        IO_file.write(json.dumps(workflow))
