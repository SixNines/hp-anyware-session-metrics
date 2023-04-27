module "metrics_publisher" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.2.0"

  function_name                     = "pcoip-metrics-publisher"
  description                       = "Lambda to process PCoIP logs and push metrics to CloudWatch"
  handler                           = "main.lambda_handler"
  runtime                           = "python3.8"
  source_path                       = "${path.module}/lambda/metrics_publisher"
  artifacts_dir                     = "${path.module}/builds"
  publish                           = true
  recreate_missing_package          = true
  ignore_source_code_hash           = true
  attach_policy_statements          = true
  cloudwatch_logs_retention_in_days = 14

  allowed_triggers = {
    sns = {
      principal  = "sns.amazonaws.com"
      source_arn = aws_sns_topic.photo_album_create.arn
    }
  }

  policy_statements = {
    cloudwatch = {
      effect    = "Allow"
      actions   = ["cloudwatch:PutMetricData"]
      resources = ["*"]
    }
  }

  environment_variables = {
    metrics_namespace = "custom-metrics"
  }
}
