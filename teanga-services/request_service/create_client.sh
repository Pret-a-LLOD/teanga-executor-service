#!/bin/bash
# $1 must be the api .yaml relative path from base
# $2 must be the service-id on apache airflow
client_name=client_$2
mkdir -p /teanga/clients
if [ -d "/teanga/clients/${client_name}" ];
then
	rm -rf /teanga/clients/$client_name
	echo "Removing old client folder"
fi
sed -e "s/8000/8001/g" $1 > ./OAS/tmp
mv ./OAS/tmp $1
openapi-generator generate -i $1 -g python -o ./clients/$client_name
cd ./clients/$client_name
for file_relpath in `grep -Hrnl "openapi_client" /teanga/clients`;
do
    echo $file_relpath
    sed -e "s/openapi_client/${client_name}/g" $file_relpath > $file_relpath.tmp
    mv $file_relpath.tmp $file_relpath
done
sed -e "s/openapi-client/${client_name}/g" setup.py > setup.py.tmp
mv setup.py.tmp setup.py
mv -i ./openapi_client ./$client_name
#python3 setup.py install --user
cd ..
