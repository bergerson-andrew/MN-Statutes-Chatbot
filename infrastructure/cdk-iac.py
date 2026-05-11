import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_lambda as _lambda,
    aws_cognito as cognito,
    aws_iam as iam,
    RemovalPolicy,
    Duration
)
from constructs import Construct

class MnStatuteStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(self, "MnStatutesVpc", max_azs=2)

        # Cognito
        user_pool = cognito.UserPool(self, "MnStatutesUserPool",
            self_sign_up_enabled=True,
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            removal_policy=RemovalPolicy.DESTROY
        )
        user_pool_client = user_pool.add_client("StreamlitClient",
            auth_flows=cognito.AuthFlow(user_password=True)
        )

        # RDS
        db_engine = rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_16)
        
        database = rds.DatabaseInstance(self, "MnStatutesDb",
            engine=db_engine,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T4G, ec2.InstanceSize.MICRO),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            allocated_storage=20,
            database_name="mnstatutesdb",
            removal_policy=RemovalPolicy.DESTROY
        )

        # Lambda
        backend_lambda = _lambda.Function(self, "MnStatutesOrchestrator",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("../backend"), 
            vpc=vpc,
            timeout=Duration.seconds(30),
            environment={
                "DB_HOST": database.instance_endpoint.hostname,
                "USER_POOL_ID": user_pool.user_pool_id
            }
        )

        # Allow Lambda to talk to the DB
        database.connections.allow_from(backend_lambda, ec2.Port.tcp(5432))
        
        # Lambda can call Bedrock
        backend_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=["*"] 
        ))

app = cdk.App()
MnStatuteStack(app, "MnStatuteStack")
app.synth()