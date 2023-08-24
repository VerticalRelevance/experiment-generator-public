from constructs import Construct
from aws_cdk import (
    Stack,
    pipelines as pipelines,
    aws_iam as _iam,
)
from vr_api.pipeline_stage import PipelineStage
from vr_api.routes.email_scraper_stage import EmailScraperStage
from vr_api.routes.planner_stage import PlannerStage
from vr_api.api_deploy_stage import DeployAPIStage
from vr_api.fargate_stage import FargateStage
from vr_api.tasks.task_updater.task_updater_stage import TaskUpdaterStage
from vr_api.routes.prospect_bot_stage  import ProspectBotStage

from os import getenv

# Pass code star connection as env variable
github_conn_arn=getenv('github_conn')
graph_secret_arn = getenv('gs_arn')
report_email = getenv('report_email')



class PipelineStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Uses CDK Pipelines
        
        pipeline = pipelines.CodePipeline(
            self,
            "Pipeline",
            synth=pipelines.ShellStep(
                "Synth",                                           
                input=pipelines.CodePipelineSource.connection("VerticalRelevance/internal-api", "master",
                    connection_arn=github_conn_arn
                ),
                env={
                "github_conn": github_conn_arn,
                "gs_arn": graph_secret_arn,
                "report_email": report_email
                },
                commands=[
                    "npm install -g aws-cdk",                               
                    "pip install -r requirements.txt",
                    "pip install -r requirements_msal_layer.txt -t lambda/layers/msal_requests/python/lib/python3.10/site-packages", # for msal lambda layer   
                    "cdk synth",                                      
                    ],
                primary_output_directory="cdk.out"
            ),
        )

        # Deploys frontend and API GW stack but does not deploy the API to prod stage. Needs to be before routes

        deploy = pipeline.add_stage(PipelineStage(self, "DeployAPIGW"))
        
        # Wave deploy of routes/other objects
        
        wave = pipeline.add_wave("WaveDeploy")
        
        wave.add_stage(FargateStage(self, "DeployFargateStage"))

        wave.add_stage(EmailScraperStage(self, "DeployEmailScraper"))

        wave.add_stage(TaskUpdaterStage(self, "DeployTaskUpdater"))
        
        wave.add_stage(PlannerStage(self, "DeployRoute3"))

        wave.add_stage(ProspectBotStage(self, "DeployFrontendProspectBot"))

        # Deploys api to prod stage. Needs to happen after routes as api is immutable once deployed

        deploy_api_stage = pipeline.add_stage(DeployAPIStage(self, "DeployAPI"))





        