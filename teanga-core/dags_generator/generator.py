from datetime import timedelta
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators import PythonOperator
from airflow.operators import SubDagOperator
from airflow.utils.dates import days_ago

import docker
from docker.errors import ImageNotFound
import sys
import logging
import os
import json
import yaml
import datetime
from io import StringIO, BytesIO
import tarfile

def generate_dag(name, description): #{{
    """
    """
    dag = DAG(
        name,
        default_args=default_args,
        description=description,
        schedule_interval=None,
        is_paused_upon_creation=False,
    )
    return dag
#}}

def generate_pull_operators(unique_services): #{
    """
    """
    operators = {}
    for full_imagePath, services_instances in unique_services.items():
        d = services_instances[0][1]
        airflow_imageName = full_imagePath.replace("/","--").replace(":","--") 
        task_id=f"pull--{airflow_imageName}--{d['port']}"
        check_imageExists = f'$(docker images -q {full_imagePath})'
        pull_command=f'docker pull {full_imagePath}'
        command=f'if [[ {check_imageExists} != "" ]]; then echo {check_imageExists};else {pull_command}; fi'
        print(command);
        operators[task_id] = BashOperator(
                task_id=task_id,
                bash_command=command,
                dag=dag,
                xcom_push=True,
        )
    '''
    today_date = datetime.datetime.now().strftime("%d%m%Y")
    repo=""# #{
    name="rq_manager"
    tag=today_date
    full_imagePath = f"{name}:{tag}"  
    task_id=f"pull--{repo}--{name}--{tag}"
    command=f'docker pull {full_imagePath}'
    print(command);
    operators[task_id] = BashOperator(
            task_id=task_id,
            bash_command=command,
            dag=dag,
            xcom_push=True,
    )# #}
    '''
    return operators
#}}

def generate_setup_operators(unique_services): #{{
    """
    """
    operators = {}
    for full_imagePath, services_instances in unique_services.items():
        d = services_instances[0][1]
        airflow_imageName = full_imagePath.replace("/","--").replace(":","--") 
        task_id=f"setup-{airflow_imageName}--{d['port']}"
        command=f"docker run --rm --name {airflow_imageName} -d -p {d['host_port']}:{d['container_port']} -e PORT={d['container_port']} {full_imagePath}"
        print(command);
        operators[task_id] = BashOperator(
                task_id=task_id,
                bash_command=command,
                dag=dag,
                xcom_push=True,
        )
    return operators
#}}

def generate_dockercp_operators(workflow_steps): #{
    """
    """
    operators = {}
    for workflow_id,service_instance_info in workflow_steps.items():
        d = service_instance_info
        if d['repo']: full_imagePath = f"{d['repo']}/{d['image_id']}:{d['image_tag']}" 
        else: full_imagePath         = f"{d['image_id']}:{d['image_tag']}" 
        airflow_imageName            = full_imagePath.replace("/","--").replace(":","--") 
        setup_task_id                =f"setup-{airflow_imageName}--{d['port']}"
        task_id                      =f"dockercp-OAS--{airflow_imageName}--{d['port']}--{workflow_id}"

        command=f'docker cp {{{{ task_instance.xcom_pull(task_ids="{setup_task_id}") }}}}:/openapi.yaml /teanga/OAS/{workflow_id}_{{{{ task_instance.xcom_pull(task_ids="{setup_task_id}") }}}}'
        #f'echo {{{{ task_instance.xcom_pull(task_ids="{setup_task_id}") }}}} >> /teanga/text.txt'
        print(command);
        operators[task_id] = BashOperator(
                task_id=task_id,
                bash_command=command,
                dag=dag,
                xcom_push=True,
        )
    return operators
#}}

def generate_validateWorkflow_operator(): #{
    """
    """
    operators = {}    
    task_id=f"validating--workflow"
    command=f'python3 /teanga/workflow_validation.py'
    operators[task_id] = BashOperator(
            task_id=task_id,
            bash_command=command,
            dag=dag,
            xcom_push=True,
    )
    return operators
#}}

def generate_requests_subDag(default_args, dag): #{
    """
    airflow.exceptions.AirflowException: The subdag's dag_id should have the form '{parent_dag_id}.{this_task_id}'. Expected 'naisc_local_workflow.json.requests--DAG'; received 'requests_DAG'.
    """
    dag_subdag = DAG(
        dag_id=f'naisc_local_workflow.json.requests--DAG',
        default_args=default_args,
        schedule_interval=None,
    )
    with dag_subdag:
        for i in range(5):
            t = DummyOperator(
                task_id='load_subdag_{0}'.format(i),
                default_args=default_args,
                dag=dag_subdag,
            )
    operators = {}    
    task_id=f"requests--DAG"
    operators[task_id] = SubDagOperator(
        task_id=task_id,
        subdag=dag_subdag,
        default_args=default_args,
        dag=dag,
    )
    return operators
#}}

def generate_setupOperator_rqService(): #{{
        operators = {}
        task_id=f"setup--requestService"
        today_date = datetime.datetime.now().strftime("%d%m%Y")
        command=f'docker run --rm --name requests_manager -dt --network="host" -v {os.environ["TEANGA_DIR"]}/files:/teanga/files -v {os.environ["TEANGA_DIR"]}/OAS:/teanga/OAS -v {os.environ["TEANGA_DIR"]}/IO:/teanga/IO -v {os.environ["TEANGA_DIR"]}/workflows:/teanga/workflows -v {os.environ["TEANGA_DIR"]}/services:/teanga/services  rq_manager:{today_date}'
        print(command);
        operators[task_id] = BashOperator(
                task_id=task_id,
                bash_command=command,
                dag=dag,
                xcom_push=True,
        )
        return operators
    #}}

def request_function(step_id): #{{
    return id

def request_operator(id):
    operators = {}    
    task_id=f"request--{id}"
    return PythonOperator(
        task_id=task_id,
        python_callable=request_function,
        op_kwargs={'id': id},
        dag=dag)

def generate_executeRequests_operator(): 
    """
    """
    operators = {}    
    task_id=f"exec--requestService"
    command=f'docker exec {{{{ task_instance.xcom_pull(task_ids="setup--requestService") }}}} sh -c "python3 /teanga/request_manager.py"'
    operators[task_id] = BashOperator(
            task_id=task_id,
            bash_command=command,
            dag=dag,
            xcom_push=True,
    )
    return operators
#}}

def generate_endpointRequest_operator(workflow_step, endpoint_name,endpoint_info):#{
    def print_context(ds, **kwargs):
        pprint(kwargs)
        print(ds)
        return 'Whatever you return gets printed in the logs'


    operator = PythonOperator(
        task_id=f'step-{workflow_step}-endpoint-{endpoint_name}',
        provide_context=True,
        python_callable=print_context,
        op_kwargs={'key1': 'value1', 'key2': 'value2'},
        dag=dag,
    )
    return operator 
#}

def generate_stop_operators(unique_services): #{{
    """
    """
    operators = {}
    for full_imagePath, services_instances in unique_services.items():
        d = services_instances[0][1]
        airflow_imageName = full_imagePath.replace("/","--").replace(":","--") 
        setup_task_id=f"setup-{airflow_imageName}--{d['port']}"
        task_id=f"stop-{airflow_imageName}--{d['port']}"
        command=f'docker stop {{{{ task_instance.xcom_pull(task_ids="{setup_task_id}") }}}}'
        print(command);
        operators[task_id] = BashOperator(
                task_id=task_id,
                bash_command=command,
                dag=dag,
        )
    return operators
#}}

def groupby_services(workflow_filepath):#{
    with open(workflow_filepath) as workflow_input:
        workflow = json.load(workflow_input)
        unique_services = {}
        for workflow_id, d in workflow.items():
            service_id = f'{d["repo"]}/{d["image_id"]}:{d["image_tag"]}'\
                         if d['repo'] else f'{d["image_id"]}:{d["image_tag"]}'
            if unique_services.get(service_id, False):
                   unique_services[service_id].append([workflow_id, d])  
            else:
                   unique_services[service_id] = [[workflow_id, d]]  

        for service_id in unique_services.keys():
            for workflow_id, instance_info in unique_services[service_id]:
                workflow[workflow_id]['port'] = unique_services[service_id][0][1]['port'] 
                workflow[workflow_id]['host_port'] = unique_services[service_id][0][1]['host_port'] 
                workflow[workflow_id]['container_port'] = unique_services[service_id][0][1]['container_port'] 
    return workflow, unique_services# #}

def flatten_operator(id):#{{
    operators = {}    
    task_id=f"flatten--{id}"
    command=f'echo testing'
    return BashOperator(
            task_id=task_id,
            bash_command=command,
            dag=dag,
            xcom_push=True,
    )
#}}

def concatenate_operator(id):#{{
    operators = {}    
    task_id=f"concatenate--{id}"
    command=f'echo testing'
    return BashOperator(
            task_id=task_id,
            bash_command=command,
            dag=dag,
            xcom_push=True,
    )
#}}

def compose_operator(id):#{{
    operators = {}    
    task_id=f"compose--{id}"
    command=f'echo testing'
    return BashOperator(
            task_id=task_id,
            bash_command=command,
            dag=dag,
            xcom_push=True,
    )
#}}

def matching_operator(airflowOperator_id):#{{ 
    operators = {}    
    task_id=f"matching--{airflowOperator_id}"
    return PythonOperator(
        task_id=task_id,
        python_callable=matching_function,
        op_kwargs={'airflowOperator_id': airflowOperator_id},
        dag=dag)

def matching_function(**kwargs):
    '''
        checks if the endpoint required inputs 
        exists in the dependencies or user input
    '''
    given_inputs = {}
    expected_inputs = {}
    return kwargs['id']

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




#}}

def groupby_operator(id):#{{
    operators = {}    
    task_id=f"groupby--{id}"
    command=f'echo testing'
    return BashOperator(
            task_id=task_id,
            bash_command=command,
            dag=dag,
            xcom_push=True,
    )
#}}

def get_spec_from_operationId(OAS, operationId):#{
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
                flatten["response_schema_name"] = \
                        flatten["sucess_response"]['content']['application/json']['schema']\
                        if flatten["sucess_response"].get('content',False) else None
    flatten["schemas"] = OAS['components']['schemas']
    return flatten 

def groupby_operator(id):#{{
    operators = {}    
    task_id=f"groupby--{id}"
    command=f'echo testing'
    return BashOperator(
            task_id=task_id,
            bash_command=command,
            dag=dag,
            xcom_push=True,
    )
#}}G
#{{ dynamic dag setup

docker_client = docker.from_env()
base_folder=os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
today_date = datetime.datetime.now().strftime("%d%m%Y")
workflow_filename = os.environ['TARGET_WORKFLOW'] #f'dev_naisc_workflow_{today_date}.json'#"dev_workflow.json"
workflow_filepath = os.path.join(base_folder,"workflows",workflow_filename)
dagCreation_timeStr = datetime.datetime.now().strftime("%d_%m_%Y_%H-%M-%S")

# making sure just one container per service is run. grouping steps on the workflow by service
# copying OAS file to teanga container and adding it to workflow dictionary
workflow, unique_services = groupby_services(workflow_filepath)#{{
print(f"WORKFLOW: {workflow}")
print(f"UK : {unique_services}")
for service_id, steps_using_service in unique_services.items():
    try: 
        docker_image = docker_client.images.get(service_id)
        print("already exists")
    except ImageNotFound:
        docker_image = docker_client.images.pull(service_id)
    if docker_image in docker_client.images.list():
        container = docker_client.containers.create(docker_image)
        stream, stats = container.get_archive("/openapi.yaml")
        openapi_filename = service_id.replace("/","_")
        file_obj = BytesIO()
        for i in stream:
            file_obj.write(i)
        file_obj.seek(0)
        tar = tarfile.open(mode='r', fileobj=file_obj)
        tar.extractall("/teanga/OAS")
        tar.close()
        os.rename("/teanga/OAS/openapi.yaml",f'/teanga/OAS/{openapi_filename}')
        container.remove()
        service_openapi_spec = yaml.load(open(f'/teanga/OAS/{openapi_filename}'),Loader=yaml.FullLoader)
        for (workflow_id, d) in steps_using_service:
            operation_id  = d["operation_id"]
            workflow[workflow_id]["operation_spec"] = get_spec_from_operationId(service_openapi_spec, operation_id) 

with open(os.path.join(base_folder,"workflows",f'updated_{workflow_filename}'),"w") as updated_workflow:
    updated_workflow.write(json.dumps(workflow))
#}}


global default_args
#{{
default_args = {
    'owner': 'teanga',
    'depends_on_past': False,
    'start_date': days_ago(2),
    'schedule_interval': None,
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
    # 'wait_for_downstream': False,
    # 'dag': dag,
    # 'sla': timedelta(hours=2),
    # 'execution_timeout': timedelta(seconds=300),
    # 'on_failure_callback': some_function,
    # 'on_success_callback': some_other_function,
    # 'on_retry_callback': another_function,
    # 'sla_miss_callback': yet_another_function,
    # 'trigger_rule': 'all_success'
}
#}}
global dag
dag = generate_dag(f"{workflow_filename}","runs the workflow described in given workflow json file ")
operators_instances = {}

# instanciate operators
#{{
# pull operators_instances 
operators_instances["pull_operators_instances"] = generate_pull_operators(unique_services)

# services setup operators_instances
operators_instances["setup_operators_instances"] = generate_setup_operators(unique_services)
operators_instances[f"generate_endpointRequest_operator"] = []
for workflow_step, step_input in workflow.items():
    operators_instances[f"generate_endpointRequest_operator"].append(generate_endpointRequest_operator(workflow_step, step_input["operation_id"], step_input))



"""
# docker cp operators_instances
operators_instances["dockercp_operators_instances"] = generate_dockercp_operators(workflow)
# docker setup requestService operators_instances
operators_instances["setupOperator_requestService"] = generate_setupOperator_rqService()
operators_instances["execOperator_requestService"] = generate_executeRequests_operator()
# docker stop operators_instances
operators_instances["stop_operators_instances"] = generate_stop_operators(unique_services)
"""
#}}

# create graph dependencies
#{{
pull_operators_instances = [operator for operator in operators_instances["pull_operators_instances"].values()]
setup_operators_instances = [operator for operator in operators_instances["setup_operators_instances"].values()]
rq_operators_instances = [operator for operator in operators_instances["generate_endpointRequest_operator"]]

"""
dockercp_operators_instances = [operator for operator in operators_instances["dockercp_operators_instances"].values()]
setupRequestService_operator_instances = [operator for operator in operators_instances["setupOperator_requestService"].values()]
executeRequest_operator_instance = [operator for operator in operators_instances["execOperator_requestService"].values()]
stop_operators_instance = [operator for operator in operators_instances["stop_operators_instances"].values()]
"""

for pull_operators_instance in pull_operators_instances:
    pull_operators_instance >> setup_operators_instances

# MAPPING each step on the workflow to a set of airflow operators    
for workflow_step, step_input in list(workflow.items()):
   dependencies_inputs = [step_input["input"]]
   pre_operator = matching_operator(f'step-{workflow_step}')
   if not step_input["dependencies"]:
       setup_operators_instances >> pre_operator 
       pre_operator >> rq_operators_instances[int(workflow_step)-1]
       pre_operator.op_kwargs.update(step_input)
       pre_operator.op_kwargs.update({"dependencies":step_input})

   for dependency in step_input["dependencies"]: #{{
       if dependency["operator"] == "wait": 
           for dependency_step in dependency["steps"]:
               rq_operators_instances[int(dependency_step)-1] >> pre_operator #rq_operators_instances[int(workflow_step)-1]

       elif dependency["operator"] == "pass":
           rq_operators_instances[int(workflow_step)-1].IO = []
           for dependency_step in dependency["steps"]:
               rq_operators_instances[int(dependency_step)-1] >> rq_operators_instances[int(workflow_step)-1]
               rq_operators_instances[int(workflow_step)-1].IO.append(f'{{{{ task_instance.xcom_pull(task_ids="{rq_operators_instances[int(dependency_step)-1].task_id}") }}}}')

       elif dependency["operator"] == "flatten": 
           operator = flatten_operator(f'step-{workflow_step}')
           rq_operators_instances[int(dependency_step)] >> operator
           operator >> rq_operators_instances[int(workflow_step)-1]

       elif dependency["operator"] == "concatenate": 
           operator = concatenate_operator(f'step-{workflow_step}')
           for dependency_step in dependency["steps"]:
            if isinstance(dependency_step,dict):
               operator_ = groupby_operator(f'step-{workflow_step}')
               for dependency_step_ in dependency_step["steps"]:
                   rq_operators_instances[int(dependency_step_)-1] >> operator_ 
                   operator_ >> operator
            elif isinstance(dependency_step,str):
               rq_operators_instances[int(dependency_step)-1] >> operator 
               operator >> rq_operators_instances[int(workflow_step)-1]

       elif dependency["operator"] == "compose": 
           operator_ = compose_operator(f'step-{workflow_step}')
           for dependency_step in dependency["steps"]:
               rq_operators_instances[int(dependency_step)-1] >> operator_
           operator_ >> rq_operators_instances[int(workflow_step)-1]

#}}
"""
for setup_operator_instance in setup_operators_instances :
   setup_operator_instance >> dockercp_operators_instances


for setup_operator_instance in setupRequestService_operator_instances:
    setup_operator_instance >> executeRequest_operator_instance

for executeRequest_operator_instance_ in  executeRequest_operator_instance:
    executeRequest_operator_instance_ >> stop_operators_instance
"""
#}}
#}}

#{{ main
if __name__ != "__main__":
    print("_"*80)
    print("importing dag configuration \n"*1)
    print("_"*80)

if __name__ == "__main__":
    print("_"*80)
    print("generating dag file in the dag folder"*1)
    print("_"*80)

    fileCreation_timeStr = datetime.datetime.now().strftime("%d_%m_%Y_%H:%M:%S")
    operators_str = "\n".join([f"{key}=operators_instances['{key}']" for key in operators_instances.keys()]) 
    with open("./dags_generator/dag_template") as template,\
            open(f"./dags/dag_instance.py","w") as template_instance:
                template_str = template.read()
                template_str = template_str.replace("{%OPERATORS%}",operators_str)
                template_instance.write(template_str)
#}}
