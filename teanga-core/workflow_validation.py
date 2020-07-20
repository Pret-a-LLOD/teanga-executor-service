
def groupby_services(workflow_filepath):
    import json# #{
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



#{{ dynamic dag setup
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

base_folder=os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
today_date = datetime.datetime.now().strftime("%d%m%Y")
workflow_filename = os.environ['TARGET_WORKFLOW'] #f'dev_naisc_workflow_{today_date}.json'#"dev_workflow.json"
workflow_filepath = os.path.join(base_folder,"workflows",workflow_filename)

dagCreation_timeStr = datetime.datetime.now().strftime("%d_%m_%Y_%H-%M-%S")
global dag
dag = generate_dag(f"{workflow_filename}","runs the workflow described in given workflow json file ")

operators_instances = {}

workflow, unique_services = groupby_services(workflow_filepath)
with open(os.path.join(base_folder,"workflows",f'updated_{workflow_filename}'),"w") as updated_workflow:
    updated_workflow.write(json.dumps(workflow))
#}}



"""
from airflow import models
from airflow.operators.bash_operator import BashOperator
from airflow.utils.dates import days_ago
import os
bag = models.DagBag()
chosen_workflow = bag.get_dag(os.environ["TARGET_WORKFLOW"])
run_this = BashOperator( task_id='run_after_loop', bash_command='echo 1', dag=chosen_workflow)
with open("VALIDATION","w") as outf:
    outf.write("banana")

new_dag = models.DAG(
                dag_id="testing",
                start_date=days_ago(2),
                description='A simple tutorial DAG',
                schedule_interval=None
                    ) 
run_this = BashOperator( task_id='run_after_loop2', bash_command='echo 1', dag=new_dag)
new_dag.sync_to_db()
"""

