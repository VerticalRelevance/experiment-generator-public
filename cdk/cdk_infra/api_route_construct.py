from aws_cdk import (
    aws_apigateway as apigw,
    aws_lambda as _lambda,
    aws_iam as _iam,  
)
from constructs import Construct

class Route(Construct):
    def __init__(self, scope: Construct, id: str, name, api, lambda_data, api_config, storage, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.lambda_role = self.create_lambda_role(name, lambda_data)
        
        self.route_lambda = self.create_lambda_function(name, lambda_data, self.lambda_role, storage)

        self.route_lambda.add_permission('APIinvoke', principal=_iam.ServicePrincipal("apigateway.amazonaws.com"))

        if 'parent_route' in api_config:
            root = api_config['parent_route']
        else:
            root = api.root

        self.route = root.add_resource(name)

        self.add_method(api_config, self.route_lambda)
        
        if "cors" in api_config:
            self.route.add_cors_preflight(
                allow_origins=['*'],
                allow_methods=['*'],
                allow_headers=['*']
            )

    def create_lambda_role(self, name, lambda_data):
        lambda_role = _iam.Role(scope=self, id=name+'LambdaRole',
                                assumed_by=_iam.ServicePrincipal('lambda.amazonaws.com'),
                                role_name=name+'LambdaRole',
                                managed_policies=[
                                    _iam.ManagedPolicy.from_aws_managed_policy_name(
                                        'service-role/AWSLambdaBasicExecutionRole')  
                                ]
        )
        
        if 'managed_policies' in lambda_data:
            for policy in lambda_data['managed_policies']:
                lambda_role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name(policy))

        if 'policy_statements' in lambda_data:
            for policy in lambda_data['policy_statements']:
                lambda_role.add_to_policy(policy)

        return lambda_role

    def create_lambda_function(self, name, lambda_data, lambda_role, storage):
        
        env = None

        if storage:
            env = dict()
            if 'dynamodb' in storage:
                table = storage['dynamodb']
                env["TABLE_NAME"] = table.table_name
            
            if 's3' in storage:
                bucket = storage['s3']
                env["BUCKET_NAME"] = bucket.bucket_name

        route_lambda = _lambda.Function(
            self, name+'Lambda',
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=lambda_data['code'],
            handler=lambda_data['handler'] if 'handler' in lambda_data else 'main.handler',
            role=lambda_role,
            layers=lambda_data.get('layers'),  
            timeout=lambda_data.get('timeout'), 
            environment=env,
            function_name=name+"-lambda"
        )

        if storage:
            if 'dynamodb' in storage:
                table.grant_full_access(route_lambda)
                
            if 's3' in storage:
                bucket.grant_read_write(route_lambda)
        return route_lambda

    def add_method(self, api_config, rt_lambda):
        self.route.add_method(api_config['method'], 
            apigw.LambdaIntegration(rt_lambda),
            api_key_required=api_config['require_key'],
        )
