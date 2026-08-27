module "wrapper_notifications" {
  source = "../../"

  metadata = local.metadata

  notifications_parameters = {
    enable = true

    # DISCORD
    notifications_discord_webhook_url = ""
    alarms_discord_webhook_url        = ""

    # TEAMS
    notifications_teams_webhook_url = ""
    alarms_teams_webhook_url        = ""

    # sns_topic_arn = ""

    
    eventbridge_rules = {
      ecs_and_health = {
        name        = "${local.common_name}-health-rule"
        description = "ECS events and AWS Health events"
        event_pattern = jsonencode({
          "$or" = [
            { source = ["aws.ecs"] },
            { source = ["aws.health"], "detail-type" = ["AWS Health Event"] }
          ]
        })
      }
    }
  }

  notifications_defaults = var.notifications_defaults
}