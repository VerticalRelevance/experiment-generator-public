from aws_cdk import (
    Duration,
    Stack,
    aws_apigateway as apigw,
    aws_iam as _iam,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_ssm as ssm,
    BundlingOptions
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

        experiment_bucket = s3.Bucket(self, 'ExperimentBucket')

        storage = {"dynamodb": db_table}

        # Lambda Layers
        yaml_layer = _lambda.LayerVersion(self, "YamlLayer",
            code=_lambda.Code.from_asset('lambda_layers/yaml'),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
            )
        
        cl_layer = _lambda.LayerVersion(self, "ChaoslibLayer",
            code=_lambda.Code.from_asset('lambda_layers/chaoslib'),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
            )

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
                                    'code': _lambda.Code.from_asset('lambda/config'),
                                    'timeout' : Duration.minutes(1),
                                    'handler': "method.handler"
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
                                    'code': _lambda.Code.from_asset('lambda/config'),
                                    'timeout' : Duration.minutes(1),
                                    'handler': "scenario.handler",
                                    'layers': [cl_layer]
                                },
                                api_config={
                                    'method' : "POST",
                                    'require_key': False,
                                    'parent_route': config_route
                                },
                                storage=storage,
                            )
        
        scenario_route_read = scenario_route.add_method(
            api_config={
                'method': 'GET',
                'require_key': False,
            },
            rt_lambda=scenario_route.route_lambda
        )

        scenario_route_delete = scenario_route.add_method(
            api_config={
                'method': 'DELETE',
                'require_key': False,
            },
            rt_lambda=scenario_route.route_lambda
        )

        scenario_route_update = scenario_route.add_method(
            api_config={
                'method': 'PUT',
                'require_key': False,
            },
            rt_lambda=scenario_route.route_lambda
        )

        target_route = Route(self, 'Target',
                                api=api,
                                name="target",
                                lambda_data={
                                    'code': _lambda.Code.from_asset('lambda/config'),
                                    'timeout' : Duration.minutes(1),
                                    'handler': "target.handler",
                                    'layers': [cl_layer]
                                },
                                api_config={
                                    'method' : "POST",
                                    'require_key': False,
                                    'parent_route': config_route
                                },
                                storage=storage,
                            )
        
        target_route_read = target_route.add_method(
            api_config={
                'method': 'GET',
                'require_key': False,
            },
            rt_lambda=target_route.route_lambda
        )

        target_route_delete = target_route.add_method(
            api_config={
                'method': 'DELETE',
                'require_key': False,
            },
            rt_lambda=target_route.route_lambda
        )

        target_route_update = target_route.add_method(
            api_config={
                'method': 'PUT',
                'require_key': False,
            },
            rt_lambda=target_route.route_lambda
        )

        generate_route = Route(self, 'Generate',
                                api=api,
                                name="generate",
                                lambda_data={
                                    'code': _lambda.Code.from_asset('lambda/generate'),
                                    'timeout' : Duration.minutes(1),
                                    'layers': [yaml_layer]
                                },
                                api_config={
                                    'method' : "POST",
                                    'require_key': False,
                                },
                                storage={"dynamodb": db_table, "s3": experiment_bucket},
                            )
        
        generate_route_read = generate_route.add_method(
            api_config={
                'method': 'GET',
                'require_key': False,
            },
            rt_lambda=generate_route.route_lambda
        )

        generate_route_delete = generate_route.add_method(
            api_config={
                'method': 'DELETE',
                'require_key': False,
            },
            rt_lambda=generate_route.route_lambda
        )

        generate_route_update = generate_route.add_method(
            api_config={
                'method': 'PUT',
                'require_key': False,
            },
            rt_lambda=generate_route.route_lambda
        )

        get_all_config_route = Route(self, 'GetInputs',
                        api=api,
                        name="getinputs",
                        lambda_data={
                            'code': _lambda.Code.from_asset('lambda/config'),
                            'timeout' : Duration.minutes(1),
                            'layers': [yaml_layer],
                            'handler': 'get_config.handler'
                        },
                        api_config={
                            'method' : "GET",
                            'require_key': False,
                            'parent_route': config_route
                        },
                        storage=storage
                    )
        
        # Retrieve the API Gateway URL and store in ssm
        ssm.StringParameter(
            self,
            "ApiGatewayBaseUrlParameter",
            parameter_name="/experiment_generator/api_url" ,
            string_value=api.url,
        )