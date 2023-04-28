resource "aws_cloudwatch_log_group" "pcoip_logs" {
  name              = "pcoip"
  retention_in_days = 14
  tags              = var.tags
}

resource "aws_cloudwatch_log_subscription_filter" "pcoip_metrics" {
  depends_on = [aws_lambda_permission.allow_trigger_metrics_publisher]

  name            = "pcoip-metrics"
  log_group_name  = aws_cloudwatch_log_group.pcoip_logs.name
  filter_pattern  = "?MGMT_PCOIP_DATA ?VGMAC ?MGMT_IMG"
  destination_arn = module.metrics_publisher.lambda_function_arn
}

resource "aws_lambda_permission" "allow_trigger_metrics_publisher" {
  action        = "lambda:InvokeFunction"
  function_name = module.metrics_publisher.lambda_function_arn
  principal     = "logs.${data.aws_region.current.name}.amazonaws.com"
  source_arn    = "${aws_cloudwatch_log_group.pcoip_logs.arn}:*"
}
