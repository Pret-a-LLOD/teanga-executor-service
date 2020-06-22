from __future__ import print_function
import importlib
import time

from pprint import pprint



for service in []:
    dummyid_client = importlib.import_module(service)
    from dummyid_client.rest import ApiException
    with dummyid_client.ApiClient() as api_client:
        # Create an instance of the API class
        api_instance = dummyid_client.DefaultApi(api_client)
        
        try:
            # calculate word embeddings for each sentence in as list of sentences
            api_response = api_instance.calculate_word_embeddings()
            pprint(api_response)
        except ApiException as e:
            print("Exception when calling DefaultApi->calculate_word_embeddings: %s\n" % e)
