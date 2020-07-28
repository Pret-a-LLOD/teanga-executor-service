from datetime import timedelta
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators import PythonOperator
from airflow.operators import SubDagOperator
from airflow.utils.dates import days_ago

import docker
import sys
import logging
import os
import json
import datetime

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

def generate_executeRequests_operator(): #{
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

def groupby_services(workflow_filepath):# #{
    import json
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
#{{ dynamic dag setup

docker_client = docker.from_env()
base_folder=os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
today_date = datetime.datetime.now().strftime("%d%m%Y")
workflow_filename = os.environ['TARGET_WORKFLOW'] #f'dev_naisc_workflow_{today_date}.json'#"dev_workflow.json"
workflow_filepath = os.path.join(base_folder,"workflows",workflow_filename)
dagCreation_timeStr = datetime.datetime.now().strftime("%d_%m_%Y_%H-%M-%S")

workflow, unique_services = groupby_services(workflow_filepath)
for service_id in unique_services.keys():
    if docker_client.images.get(service_id):
        print("already exists")
        docker_image = docker_client.images.get(service_id)
    else:
        docker_image = docker_client.images.pull(service_id)
    if docker_image in docker_client.images.list():
        container = docker_client.containers.create(docker_image)
        bits, stats = container.get_archive("/openapi.yaml")
        openapi_filename = service_id.replace("/","_")
        with open(f'/teanga/OAS/{openapi_filename}','wb') as outf:
            for bit in bits:
                outf.write(bit)
        container.remove()

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

workflow, unique_services = groupby_services(workflow_filepath)
with open(os.path.join(base_folder,"workflows",f'updated_{workflow_filename}'),"w") as updated_workflow:
    updated_workflow.write(json.dumps(workflow))

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

for workflow_step, step_input in list(workflow.items()):
   if not step_input["dependencies"]:
       setup_operators_instances >> rq_operators_instances[int(workflow_step)-1]
   for dependency in step_input["dependencies"]:
       if dependency["operator"] == "wait": 
           for dependency_step in dependency["steps"]:
               rq_operators_instances[int(dependency_step)-1] >> rq_operators_instances[int(workflow_step)-1]

       elif dependency["operator"] == "pass":
           rq_operators_instances[int(workflow_step)-1].IO = []
           for dependency_step in dependency["steps"]:
               rq_operators_instances[int(dependency_step)-1] >> rq_operators_instances[int(workflow_step)-1]
               rq_operators_instances[int(workflow_step)-1].IO.append(f'{{{{ task_instance.xcom_pull(task_ids="{rq_operators_instances[int(dependency_step)-1].task_id}") }}}}')

       elif dependency["operator"] == "flatten": 
           print(dependency)
           operator = flatten_operator(f'step-{workflow_step}')
           rq_operators_instances[int(dependency_step)] >> operator
           operator >> rq_operators_instances[int(workflow_step)-1]

       elif dependency["operator"] == "concatenate": 
           print(dependency)
           operator = concatenate_operator(f'step-{workflow_step}')
           for dependency_step in dependency["steps"]:
            if isinstance(dependency_step,dict):
               operator_ = groupby_operator(f'123step-{workflow_step}')
               for dependency_step_ in dependency_step["steps"]:
                   rq_operators_instances[int(dependency_step_)-1] >> operator_ 
                   operator_ >> operator
            elif isinstance(dependency_step,str):
               rq_operators_instances[int(dependency_step)-1] >> operator 
               operator >> rq_operators_instances[int(workflow_step)-1]
       elif dependency["operator"] == "compose": 
           print(dependency)
           for dependency_step in dependency["steps"]:
               rq_operators_instances[int(dependency_step)-1] >> rq_operators_instances[int(workflow_step)-1]
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
