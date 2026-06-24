# Domain 1 (Deployment)
## Flash Cards
### What is AWS Serverless Application Model (AWS SAM)?
A framework for building serverless applications in AWS

### How do you share AWS CloudFormation templates across multiple AWS accounts? 
Use CloudFormation StackSets

### Where do you store files for an AWS Lambda function that needs temporary storage during execution?
/tmp directory

### In Amazon Elastic Container Server (Amazon ECS), where are port mappings located and where are they configured?
Port mappings are part of the container definition and are configured in the task definition

### What is the unit of scale for Lambda?
Concurrent executions

### What condition keys would you use to limit the execution of a Lambda function to a particular Amazon VPC?
- `lambda:VpcIds` - allow or deny one or more VPCs
- `lambda:SubnetIds` - allow or deny one or more subnets
- `lambda:SecurityGroupIds` - allow or deny one or more security groups

### Global security index queries support what type of consistency?
Eventual consistency only

### What are best practices for partition keys in Amazon DynamoDB?
- Use high-cardinality attributes which are attributes that have distinct values for each item.
- Use composite attributes to combine more than one attribute to form a unique key.
- Cache the popular items when there is a high volume of read traffic using Amazon DynamoDB Accelerator (DAX).
- Add random numbers or digits from a predetermined range for write-heavy use cases.

### How do you ensure that your applications cannot retrieve a message from an Amazon Simple Queue Service (Amazon SQS) queue that is being processed or has already been processed?
Increase the VisibilityTimeout value from the ChangeMessageVisibility API and delete the message using the DeleteMessage API

### What API call do you use to give the ability to the application so that it can use an IAM role
AssumeRole API
