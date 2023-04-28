variable "metrics_namespace" {
  type        = string
  default     = "pcoip"
  description = "Namespace to put CloudWatch metrics"
  nullable    = false
}

variable "workstation_tag" {
  type = object({
    key   = string
    value = string
  })

  default = {
    key   = "type"
    value = "workstation"
  }

  description = "Tag of ec2 instances to apply CloudWatch configuration"
  nullable    = false
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags to apply to all resources"
}
