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
        db_table = dynamodb.Table(self, "Table",
            partition_key=dynamodb.Attribute(name="partition_key", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="sort_key", type=dynamodb.AttributeType.STRING),
        )

        # Config bucket not used as of now
        # config_bucket = s3.Bucket(self, 'ConfigBucket')

        storage = {"dynamodb": db_table}

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
                                storage=storage
                            )
        
        delete_package_lambda = package_route.create_lambda_function(
                                                                     name='delete-package',
                                                                     lambda_data={
                                                                            'code': _lambda.Code.from_asset('lambda/package/delete'),
                                                                            'timeout' : Duration.minutes(1)
                                                                        },
                                                                     lambda_role=package_route.lambda_role,
                                                                     storage=storage
                                                                )
        
        package_route.add_method(
            api_config={
                'method': 'DELETE',
                'require_key': False,
            },
            rt_lambda=delete_package_lambda
        )

        config_route = api.root.add_resource('config')
        
        method_route = Route(self, 'Method',
                                api=api,
                                name="method",
                                lambda_data={
                                    'code': _lambda.Code.from_asset('lambda/config/method'),
                                    'timeout' : Duration.minutes(1)
                                },
                                api_config={
                                    'method' : "POST",
                                    'require_key': False,
                                    'parent_route': config_route
                                },
                                storage=storage,
                            )
        
        method_route_read = method_route.add_method(
            api_config={
                'method': 'GET',
                'require_key': False,
            },
            rt_lambda=method_route.route_lambda
        )

        method_route_delete = method_route.add_method(
            api_config={
                'method': 'DELETE',
                'require_key': False,
            },
            rt_lambda=method_route.route_lambda
        )

        scenario_route = Route(self, 'Scenario',
                                api=api,
                                name="scenario",
                                lambda_data={
                                    'code': _lambda.Code.from_asset('lambda/config/scenario'),
                                    'timeout' : Duration.minutes(1)
                                },
                                api_config={
                                    'method' : "POST",
                                    'require_key': False,
                                    'parent_route': config_route
                                },
                                storage=storage,
                            )
test = {
    "term": "test_term",
    "scenario": {
        "pod_healthy": {
            "cluster_name": "${cluster_name}",
            "health_check_path": "${health_check_path}",
            "health_check_port": "${health_check_port}",
            "name_space": "${name_space}",
            "output_s3_bucket_name": "${output_s3_bucket_name}",
            "pod_name_pattern": "${pod_name_pattern}",
            "region": "${region}",
            "tag_key": "${tag_key}",
            "tag_value": "${tag_value}"
            },
        "delete_pod": {
                "name_space": "${name_space}",
                "output_s3_bucket_name": "${output_s3_bucket_name}",
                "pod_name_pattern": "${pod_name_pattern}",
                "region": "${region}",
                "tag_key": "${tag_key}",
                "tag_value": "${tag_value}"   
        }
        }
}