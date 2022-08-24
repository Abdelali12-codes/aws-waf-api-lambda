# aws waf with apigateway and cognito


## create s3 bucket to upload the zip files that contain the lambda code and lambda layers

## aws lambda layer 

* to create a lambda layer for your python function
1. create a directory called python (make sure that the name is python)
2. when you want to install the dependencies that your lambda will use run the below command
```
pip install packagename -t python/
```
* the above command will install the dependencies in the python directory
3. zip the the previous directory as below

```
zip -r python-requests-lambda-layer.zip python
```
4. upload the zip file to the s3 bucket 
5. go to your aws lambda console
6. click on the layer tab on the left corner of the console
7. and enter the required fields and make sure to enter the name of the bucket where you uploaded the zip file

* create s3 bucket 

```
aws s3 mb s3://aws-lambda-secret-manager-api-waf-cognito-24-08-2022 --region us-east-1
```
* upload the zip files to s3 bucket 

```
{
aws s3 cp rds-query.zip s3://aws-lambda-secret-manager-api-waf-cognito-24-08-2022 --region us-east-1
aws s3 cp rds-create-table.zip s3://aws-lambda-secret-manager-api-waf-cognito-24-08-2022 --region us-east-1
aws s3 cp python-requests-lambda-layer.zip s3://aws-lambda-secret-manager-api-waf-cognito-24-08-2022 --region us-east-1
}
```

## References

* https://www.wellarchitectedlabs.com/security/300_labs/300_autonomous_patching_with_ec2_image_builder_and_systems_manager/2_deploy_the_application_infrastructure/

* https://suricata.readthedocs.io/en/suricata-6.0.2/rules/intro.html#ports-source-and-destination
* https://docs.aws.amazon.com/secretsmanager/latest/userguide/reference_secret_json_structure.html#reference_secret_json_structure_rds-mysql
* https://suricata.readthedocs.io/en/suricata-6.0.2/rules/intro.html#ports-source-and-destination