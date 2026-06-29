"""Shared constants for lesson validation: AWS allowlist and hard-coded non-AWS terms."""

from __future__ import annotations

# Hard-coded non-AWS distractors (authoritative gate)
NON_AWS_HARDCODED = frozenset({
    "Manual page", "Add cache", "Skip write", "Root keys", "Add layer",
})

# Small AWS service/feature allowlist for soft check
AWS_ALLOWLIST = frozenset({
    # AWS services
    "Lambda", "EC2", "S3", "DynamoDB", "API Gateway", "SQS", "SNS",
    "EventBridge", "Step Functions", "Kinesis", "IAM", "STS", "Cognito",
    "Secrets Manager", "Parameter Store", "KMS", "WAF", "Macie",
    "CloudWatch", "X-Ray", "CloudTrail", "CloudFormation", "SAM",
    "CodePipeline", "CodeDeploy", "CodeBuild", "ECR", "ECS", "Fargate",
    "AppConfig", "Lambda@Edge", "CloudFront", "Route 53", "ElastiCache",
    "RDS", "Aurora", "EFS", "FSx", "EBS", "S3 Glacier", "CloudWatchLogs",
    # AWS feature names
    "Async", "Synchronous", "Proxy", "Mapping", "Throttling", "Caching",
    "StageVariable", "StageVariables", "Alias", "Layer", "Layers", "Version",
    "Retry", "Retries", "Backoff", "Batch", "PartialBatch", "VisibilityTimeout",
    "DeadLetterQueue", "DLQ", "Destinations", "Idempotency", "ColdStart",
    "VPC", "ENI", "ENIs", "Subnet", "SecurityGroup", "NACL",
    "CapacityUnit", "RCU", "WCU", "GSI", "LSI", "OnDemand", "Provisioned",
    "Encryption", "KeyPolicy", "Grant", "Role", "Policy", "Principal",
    "AssumeRole", "SessionToken", "TemporaryCredential", "Credential",
    "OAuth", "JWT", "SAML", "IdentityPool", "UserPool", "Authorizer",
    "CustomAuthorizer", "CognitoIdentityProvider", "GetCredentialsForIdentity",
    "FunctionURL", "AliasRouting", "Weight", "Canary", "Linear", "AllAtOnce",
    "Rollback", "PreTraffic", "PostTraffic", "LifecycleHook", "AutoScaling",
    "ScalingPolicy", "ScheduledAction", "TargetTracking", "StepScaling",
    "CircuitBreaker", "FailureThreshold", "Invocation", "Invocations",
    "OnSuccess", "OnFailure", "EventSourceMapping", "Stream",
    "Serverless", "ServerlessApplicationModel", "ServerlessRepo",
    "Artifact", "Artifacts", "Bucket", "Object", "Multipart",
    "Lifecycle", "Transition", "StorageClass", "IntelligentTiering",
    "TestEvent", "Mock", "LocalTesting", "Invoke", "Packaging",
    "DeploymentPackage", "ZipFile", "Dockerfile", "ContainerImage", "ImageURI",
    "LayerARN", "ProvisionedConcurrency", "ReservedConcurrency",
    "Shard", "ShardIterator", "Iterator", "Throughput", "Polling", "Triggers",
    "DeploymentConfig", "DeploymentGroup", "TrafficRouting", "AppSpec",
    "HealthCheck", "MinimumHealthyHosts", "DeploymentOption",
    "CloudFormationInit", "cfninit", "WaitHandle", "WaitCondition",
    "StackSet", "StackResource", "ChangeSet", "UpdatePolicy",
    "AutoRollback", "TerminationProtection", "DeletionPolicy",
    "LambdaFunctionException", "UnhandledError", "HandledError",
    "DestinationRule", "VirtualService", "ServiceMesh", "AppMesh",
    "Parameter", "SSMParameter", "SecureString", "PublicKey",
    "PrivateKey", "KeyPair", "SSH", "WinRM", "SessionManager",
})
