from aws_cdk import (
    Duration,
    Stack,
    aws_apigateway as apigw,
    aws_iam as _iam,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_lambda as _lambda
)
from constructs import Construct
from .api_route_construct import Route

class GeneratorStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create an API Gateway REST API
        api = apigw.RestApi(self, 'ExperimentGeneratorAPI', binary_media_types=["*/*"])

        # Dynamodb and S3 storage
        modules_table = dynamodb.Table(self, "ModulesTable",
            partition_key=dynamodb.Attribute(name="function_name", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="module", type=dynamodb.AttributeType.STRING),
        )

        config_bucket = s3.Bucket(self, 'ConfigBucket')

        package_route = Route(self, 'Package',
                                api=api,
                                name="package",
                                lambda_data={
                                    'code': _lambda.Code.from_asset('lambda/package/post'),
                                    'timeout' : Duration.minutes(1)
                                },
                                api_config={
                                    'method' : "POST",
                                    'require_key': False,
                                },
                                storage={"dynamodb": modules_table,
                                         "s3": config_bucket},
                            )
        
        # delete_package_lambda = 
        
        # package_route.add_method(
        #     api_config={
        #         'method': 'DELETE',
        #         'require_key': False,
        #     },
        #     rt_lambda=
        # )

