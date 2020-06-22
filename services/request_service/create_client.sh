#!/bin/bash
# $1 must be the api .yaml relative path from base
# $2 must be the service-id on apache airflow
client_name=$2_client
mkdir -p clients
openapi-generator generate -i $1 --log-to-stderr -g python -o ./clients/$client_name
cd ./clients/$client_name
for file_relpath in `grep -Hrnl "openapi_client" .`;
do
    echo $file_relpath
    sed -e "s/openapi_client/${client_name}/g" $file_relpath > $file_relpath.tmp
    mv $file_relpath.tmp $file_relpath
done
sed -e "s/openapi-client/${client_name}/g" setup.py > setup.py.tmp
mv setup.py.tmp setup.py
mv -i ./openapi_client ./$client_name
python3 setup.py install --user
cd ..

