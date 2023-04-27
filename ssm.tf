resource "aws_ssm_parameter" "cloudwatch_config_linux" {
  name = "cw/workstations/linux"
  type = "String"

  value = replace(templatefile("${path.module}/cloudwatch/config_linux.json", {
    log_group = aws_cloudwatch_log_group.pcoip_logs.name
    namespace = "custom-metrics"
  }), "/\n| /", "")
}

resource "aws_ssm_parameter" "cloudwatch_config_windows" {
  name = "cw/workstations/linux"
  type = "String"

  value = replace(templatefile("${path.module}/cloudwatch/config_windows.json", {
    log_group = aws_cloudwatch_log_group.pcoip_logs.name
    namespace = "custom-metrics"
  }), "/\n| /", "")
}

resource "aws_ssm_document" "cloudwatch_agent" {
  name            = "install-cloudwatch-agent"
  document_type   = "Command"
  document_format = "YAML"

  content = templatefile("${path.module}/ssm/cloudwatch_agent_provisioning.yaml", {
    linux_ssm_parameter   = aws_ssm_parameter.cloudwatch_config_linux.name
    windows_ssm_parameter = aws_ssm_parameter.cloudwatch_config_windows.name
  })
}

resource "aws_ssm_association" "cloudwatch_agent" {
  name             = aws_ssm_document.cloudwatch_agent.id
  association_name = "install-cloudwatch-agent-in-workstations"

  targets {
    key    = "tag:type"
    values = ["workstation"]
  }
}
