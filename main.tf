module "lambda_notifications" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "8.0.1"

  count = local.notifications_enable

  function_name = "${local.common_name}-notifications"
  description   = "Lambda function for notifications"
  handler       = "index.lambda_handler"
  runtime       = "python3.13"

  layers = [aws_lambda_layer_version.notifications_requests[0].arn]

  source_path = "${path.module}/lambdas/notifications"

  cloudwatch_logs_retention_in_days = try(var.notifications_parameters.cloudwatch_logs_retention_in_days, 14)

  environment_variables = {
    "DISCORD_WEBHOOK_URL" : try(var.notifications_parameters.notifications_discord_webhook_url, ""),
    "TEAMS_WEBHOOK_URL" : try(var.notifications_parameters.notifications_teams_webhook_url, "")
  }

  timeout = 12

  tags = merge(local.common_tags, try(var.notifications_parameters.tags, var.notifications_defaults.tags, null))
}

resource "aws_lambda_layer_version" "notifications_requests" {
  count               = local.notifications_enable
  filename            = "${path.module}/lambdas/layers/requests.zip"
  description         = ""
  layer_name          = "${local.common_name}-notifications-requests"
  compatible_runtimes = ["python3.13"]
}

## ALARM NOTIFICATIONS

module "lambda_alarm_notifications" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "8.0.1"

  count = local.notifications_enable

  function_name = "${local.common_name}-alarm-notifications"
  description   = "Lambda function for alarm-notifications"
  handler       = "index.lambda_handler"
  runtime       = "python3.13"

  layers = [aws_lambda_layer_version.notifications_requests[0].arn]

  source_path = "${path.module}/lambdas/alarm-notifications"

  cloudwatch_logs_retention_in_days = try(var.notifications_parameters.cloudwatch_logs_retention_in_days, 14)

  environment_variables = {
    "DISCORD_WEBHOOK_URL" : try(var.notifications_parameters.alarms_discord_webhook_url, "")
    "TEAMS_WEBHOOK_URL" : try(var.notifications_parameters.alarms_teams_webhook_url, "")
  }

  timeout = 5

  tags = merge(local.common_tags, try(var.notifications_parameters.tags, var.notifications_defaults.tags, null))
}

resource "aws_iam_role_policy" "allow_list_tags_for_alarms" {
  count = local.notifications_enable

  name = "${local.common_name}-allow-list-tags"
  role = module.lambda_alarm_notifications[0].lambda_role_name

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "cloudwatch:ListTagsForResource"
        ],
        Resource = "*"
      }
    ]
  })
}

## Default SNS subscription
resource "aws_sns_topic" "alerts" {
  count = local.create_aws_sns_topic

  name = "${local.common_name}-alerts"
  tags = merge(local.common_tags, try(var.notifications_parameters.tags, var.notifications_defaults.tags, null))
}

resource "aws_sns_topic_subscription" "alerts" {
  for_each = try(var.notifications_parameters["alerts_configuration"].email, {})

  topic_arn = try(var.notifications_parameters.sns_topic_arn, aws_sns_topic.alerts[0].arn)
  protocol  = "email"
  endpoint  = each.key
}

resource "aws_lambda_permission" "alarm_notification" {
  count         = local.notifications_enable
  statement_id  = "AllowExecutionFromSNS-${local.common_name}"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_alarm_notifications[0].lambda_function_name
  principal     = "sns.amazonaws.com"
  source_arn    = try(var.notifications_parameters.sns_topic_arn, aws_sns_topic.alerts[0].arn)
}

resource "aws_sns_topic_subscription" "alarm_notification" {
  count     = local.notifications_enable
  topic_arn = try(var.notifications_parameters.sns_topic_arn, aws_sns_topic.alerts[0].arn)
  protocol  = "lambda"
  endpoint  = module.lambda_alarm_notifications[0].lambda_function_arn
}

resource "aws_sns_topic_policy" "services" {
  count = local.notifications_enable

  arn = try(var.notifications_parameters.sns_topic_arn, aws_sns_topic.alerts[0].arn)

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "AllowServicesToPublish",
        Effect = "Allow",
        Principal = {
          Service = [
            "cloudwatch.amazonaws.com",
            "events.amazonaws.com",
            "budgets.amazonaws.com",
            "costalerts.amazonaws.com",
            "ses.amazonaws.com"
          ]
        },
        Action   = "sns:Publish",
        Resource = try(var.notifications_parameters.sns_topic_arn, aws_sns_topic.alerts[0].arn),
        Condition = {
          StringEquals = {
            "AWS:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}