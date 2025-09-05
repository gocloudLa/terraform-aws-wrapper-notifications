locals {
  notifications_enable = lookup(var.notifications_parameters, "enable", false) ? 1 : 0

  create_aws_sns_topic = (
    local.notifications_enable == 1 &&
    try(var.notifications_parameters.sns_topic_arn, "") == ""
  ) ? 1 : 0
}
